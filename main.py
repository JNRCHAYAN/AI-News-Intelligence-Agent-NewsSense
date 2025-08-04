import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool
import requests
import logfire

# --- Logfire Setup ---
logfire.configure()
logfire.instrument_openai_agents()

# --- Environment Setup ---
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError("Please set BASE_URL, API_KEY, and MODEL_NAME in your environment.")

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

# --- Models ---
class TrendingNewsItem(BaseModel):
    headline: str
    source: str
    category: str
    summary: str
    rank: int

class FactCheckResult(BaseModel):
    is_true: Optional[bool]
    verdict: str
    sources: List[str]

class NewsSummary(BaseModel):
    topic: str
    bullet_points: List[str]

@dataclass
class UserContext:
    user_id: str
    preferred_topics: List[str] = None
    session_start: datetime = None

    def __post_init__(self):
        if self.preferred_topics is None:
            self.preferred_topics = []
        if self.session_start is None:
            self.session_start = datetime.now()

# --- Tools ---
@function_tool
def get_trending_news(topic: Optional[str] = "latest", category: Optional[str] = None) -> str:
    print("[DEBUG] Making GNews API request...")

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": topic or "breaking",
        "lang": "en",
        "max": 5,
        "token": GNEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        print(f"[DEBUG] Response status: {response.status_code}")

        if response.status_code != 200:
            return json.dumps([{
                "headline": "Failed to fetch news",
                "source": "System",
                "category": topic,
                "summary": f"API error {response.status_code}: {response.text}",
                "rank": 1
            }])

        articles = response.json().get("articles", [])
        if not articles:
            return json.dumps([{
                "headline": "No news found",
                "source": "GNews",
                "category": topic,
                "summary": "No articles found for this topic.",
                "rank": 1
            }])

        results = [
            {
                "headline": a.get("title", "No headline"),
                "source": a.get("source", {}).get("name", "Unknown"),
                "category": topic,
                "summary": a.get("description", ""),
                "rank": i + 1
            } for i, a in enumerate(articles)
        ]

        return json.dumps(results)

    except Exception as e:
        return json.dumps([{
            "headline": "Error fetching news",
            "source": "Exception",
            "category": topic,
            "summary": str(e),
            "rank": 1
        }])

@function_tool
def fact_check_claim(claim: str) -> str:
    url = f"https://www.googleapis.com/customsearch/v1?q={claim}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}"
    try:
        response = requests.get(url)
        items = response.json().get("items", [])
        sources = [item['link'] for item in items[:3]]
        verdict = "Unverified claim" if not items else "Supporting sources found"
        return json.dumps({
            "is_true": None,
            "verdict": verdict,
            "sources": sources
        })
    except Exception as e:
        return json.dumps({
            "is_true": None,
            "verdict": f"Error: {str(e)}",
            "sources": []
        })

@function_tool
def summarize_news(article_text: str) -> str:
    try:
        prompt = f"Summarize the following news article into 3-5 bullet points:\n\n{article_text}"
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        summary_text = response.choices[0].message.content.strip()
        summary_lines = [line.strip("-\u2022 ").strip() for line in summary_text.split("\n") if line.strip()]
        return json.dumps({
            "topic": "Custom Article Summary",
            "bullet_points": summary_lines
        })
    except Exception as e:
        return json.dumps({
            "topic": "Summarization Error",
            "bullet_points": [f"Failed to summarize article: {str(e)}"]
        })

# --- Agents ---
trending_agent = Agent[UserContext](
    name="Trending News Finder",
    instructions="""
    You retrieve trending news stories by topic or category.
    Rank them by relevance and popularity. Group related topics.
    """,
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    tools=[get_trending_news],
    output_type=List[TrendingNewsItem]
)

fact_checker_agent = Agent[UserContext](
    name="Fact Checker",
    instructions="""
    Given a user-submitted claim, verify its truthfulness using web sources (via Google Custom Search).
    Return a verdict with 2–3 supporting links.
    """,
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    tools=[fact_check_claim],
    output_type=FactCheckResult
)

summarizer_agent = Agent[UserContext](
    name="News Summarizer",
    instructions="""
    You transform lengthy news articles or topics into 3–5 concise bullet points.
    The summary should be factual, easy to read, and capture key developments.
    """,
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    tools=[summarize_news],
    output_type=NewsSummary
)

controller_agent = Agent[UserContext](
    name="NewsSense Controller",
    instructions="""
    You’re the entry point for NewsSense. Based on the query, determine whether the user wants:
    - Trending News
    - Fact Check
    - Summary

    Route it to the right agent.
    Respond clearly and journalistically.
    """,
    model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
    handoffs=[trending_agent, fact_checker_agent, summarizer_agent]
)

# --- Main Test ---
async def main():
    logfire.info("Running NewsSense main test")
    user_ctx = UserContext(user_id="news_user_001", preferred_topics=["tech", "politics"])

    queries = [
        "What's trending in tech today?",
        "Did Apple acquire OpenAI?",
        "Summarize this article: OpenAI expands GPT access to new platforms"
    ]

    for query in queries:
        print("\n" + "=" * 40)
        print(f"User: {query}")
        print("=" * 40)
        result = await Runner.run(controller_agent, query, context=user_ctx)
        print("\n🤬 Agent Response:\n", result.final_output)

    print(f"\n🔗 Logfire session: {logfire.session_url()}")

if __name__ == "__main__":
    asyncio.run(main())
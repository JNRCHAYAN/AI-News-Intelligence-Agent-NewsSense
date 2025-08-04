# 🧠 NewsSense – AI News Intelligence Agent

This repository contains a multi-agent system built using the OpenAI Agents SDK, designed to track, verify, and summarize breaking news from across the web.

## 🧭 Overview
NewsSense intelligently handles:
- Trending news detection
- Claim verification via web search
- Article summarization into bullet points

## 🗂️ Project Structure

- `main.py` – Core multi-agent orchestration with controller and sub-agents
- `ui_Main.py` – Streamlit UI for chat interface with session memory

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file with your keys:
```env
BASE_URL="https://models.github.ai/inference/v1"
API_KEY=your_openai_api_key
MODEL_NAME="openai/gpt-4.1-nano"
GNEWS_API_KEY=your_gnews_api_key
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_google_cse_id
```
```
🔑 How to Get Your Keys
GNEWS_API_KEY
Go to https://gnews.io/
Sign up for a free developer account
Get your API key from the dashboard
```
GOOGLE_API_KEY & SEARCH_ENGINE_ID
Go to https://programmablesearchengine.google.com
Create a new custom search engine
Get the Search Engine ID from control panel
Go to https://console.cloud.google.com/apis/credentials
Create an API key under Credentials
```
Enable Custom Search API in the API Library
## 🚀 Running the Agents

### Controller + Agents Test
Run the terminal-based test harness:
```bash
python main.py
```

This will:
- Retrieve trending news via GNews API
- Verify claims using Google Search API
- Summarize input articles using OpenAI

### 🖥️ Launch Streamlit App
```bash
streamlit run ui_Main.py
```

Features:
- Conversational news agent UI
- Sidebar for preferred topic filtering
- Trending, claim-checking, and summarization all-in-one
- Persistent chat per session
- Agent output formatted into readable blocks

## 🔧 Tools Used

### 1. `get_trending_news(topic: str)`
- Fetches latest news via GNews API
- Parses headlines, source, description, and ranks by frequency

### 2. `fact_check_claim(claim: str)`
- Uses Google Custom Search to fetch claim-related links
- Returns a verdict and 2–3 reference URLs

### 3. `summarize_news(article_text: str)`
- Uses OpenAI’s chat model to generate 3–5 bullet summaries
- Works with any pasted article or long-form content

## 🧠 Agents Overview

### 🤖 Controller Agent
- Classifies queries: `"trending"`, `"verify"`, or `"summarize"`
- Routes to appropriate specialist agent

### 🔥 Trending News Agent
- Gathers news headlines from GNews
- Groups related stories
- Outputs structured results using `TrendingNewsItem`

### ✅ Fact Checker Agent
- Performs retrieval-augmented verification
- Returns verdict + top sources using `FactCheckResult`

### 📝 News Summarizer Agent
- Uses OpenAI model to abstractively summarize articles
- Outputs `NewsSummary` object with bullets and topic

## 🎯 Example Queries

### Trending
- "What's trending in tech today?"
- "Any news in politics or finance?"

### Fact-Check
- "Did Apple acquire OpenAI?"
- "Is Bitcoin at $100K?"

### Summarization
- "Summarize this article: [paste]"
- "What happened in today’s WSJ newsletter?"

## 🔍 Logfire Integration
Logfire is preconfigured for tracing agent decisions, including:
- Agent handoffs
- Tool invocations
- Model output debugging

Optional setup at [logfire.pydantic.dev](https://logfire.pydantic.dev/docs/#logfire)

## 📌 Notes
- GNews and Google Custom Search APIs must be enabled in your dev console
- OpenAI summarization is real-time, not mocked
- Use `.env` securely for managing credentials

---

Built for AI-driven journalism and news awareness ⚡

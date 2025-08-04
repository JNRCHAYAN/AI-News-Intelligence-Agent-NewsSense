import streamlit as st
import asyncio
import uuid
from datetime import datetime
from typing import List

from main import (
    controller_agent,
    UserContext,
    TrendingNewsItem,
    FactCheckResult,
    NewsSummary
)
from agents import Runner

# Page config
st.set_page_config(
    page_title="NewsSense – AI News Agent",
    page_icon="🧠",
    layout="wide"
)

# CSS for chat UI
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #eef6ff;
        border-left: 5px solid #1e88e5;
    }
    .chat-message.assistant {
        background-color: #f0f4f7;
        border-left: 5px solid #43a047;
    }
    .chat-message .content {
        display: flex;
        margin-top: 0.5rem;
    }
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
    }
    .message {
        flex: 1;
        color: #111;
    }
    .timestamp {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "user_context" not in st.session_state:
    st.session_state.user_context = UserContext(user_id=str(uuid.uuid4()))
if "processing_message" not in st.session_state:
    st.session_state.processing_message = None

# --- Helper functions ---
def format_response(output):
    if hasattr(output, "model_dump"):
        output = output.model_dump()
    elif hasattr(output, "__dict__"):
        output = output.__dict__

    if isinstance(output, dict):
        if "headline" in output:  # Trending item
            return f"**{output['headline']}**\n\n_{output['source']} – {output['summary']}"
        elif "verdict" in output:  # FactCheckResult
            sources = '\n'.join(f"- [{s}]({s})" for s in output.get("sources", []))
            return f"**Verdict:** {output['verdict']}\n\n**Sources:**\n{sources}"
        elif "bullet_points" in output:  # NewsSummary
            bullets = '\n'.join(f"- {pt}" for pt in output["bullet_points"])
            return f"**Topic:** {output['topic']}\n\n{bullets}"

    return str(output)

def handle_user_input(user_input: str):
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })
    st.session_state.processing_message = user_input

# Sidebar preferences
with st.sidebar:
    st.title("🧠 NewsSense Preferences")
    preferred_topics = st.multiselect("Preferred Topics", ["tech", "politics", "finance", "health"], default=st.session_state.user_context.preferred_topics)
    if st.button("Save Preferences"):
        st.session_state.user_context.preferred_topics = preferred_topics
        st.success("Preferences updated.")

    st.divider()
    if st.button("New Session"):
        st.session_state.chat_history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.success("Started new session!")

# Main Interface
st.title("🗞️ NewsSense: AI News Agent")
st.caption("Ask about trending news, verify claims, or summarize articles.")

# Display chat
for msg in st.session_state.chat_history:
    avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={st.session_state.user_context.user_id}" if msg["role"] == "user" else "https://api.dicebear.com/7.x/bottts/svg?seed=news-agent"
    role_class = "user" if msg["role"] == "user" else "assistant"
    st.markdown(f"""
    <div class="chat-message {role_class}">
        <div class="content">
            <img src="{avatar}" class="avatar" />
            <div class="message">
                {msg["content"]}
                <div class="timestamp">{msg['timestamp']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Input area
user_prompt = st.chat_input("Ask a question about the news...")
if user_prompt:
    handle_user_input(user_prompt)
    st.rerun()

# Process input
if st.session_state.processing_message:
    user_input = st.session_state.processing_message
    st.session_state.processing_message = None
    with st.spinner("Thinking..."):
        try:
            result = asyncio.run(Runner.run(
                controller_agent,
                user_input,
                context=st.session_state.user_context
            ))

            # Handle single or list of responses
            if isinstance(result.final_output, list):
                for item in result.final_output:
                    response_text = format_response(item)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
            else:
                response_text = format_response(result.final_output)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().strftime("%I:%M %p")
            })
        st.rerun()

# Footer
st.divider()
st.caption("NewsSense • AI News Agent • Built with Streamlit")
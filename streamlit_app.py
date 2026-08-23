import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = st.secrets.get(
    "MED_AI_API_URL",
    os.environ.get("MED_AI_API_URL", ""),
)
FUNCTION_KEY = st.secrets.get(
    "MED_AI_FUNCTION_KEY",
    os.environ.get("MED_AI_FUNCTION_KEY", ""),
)
SYSTEM_PROMPT = """
You are a medical information assistant. Do not recommend or prescribe medicines,
tell the user what medicine to take or eat for an illness, diagnose a condition,
recommend pathology tests or clinical tests for a specific illness, or interpret
results as a diagnosis. For any such request, just say that
the user should consult a qualified healthcare professional and not any AI bot.
""".strip()

def call_backend(
    api_url: str,
    chat_history: list[dict[str, str]],
) -> tuple[str, list[dict]]:
    if not FUNCTION_KEY:
        raise ValueError("MED_AI_FUNCTION_KEY is not configured in the .env file.")

    response = requests.post(
        api_url,
        headers={"x-functions-key": FUNCTION_KEY},
        json={"chat_history": chat_history},
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()
    return (
        str(payload.get("response") or ""),
        payload.get("retrieved_contexts") or [],
    )

def remove_citation_markers(text: str) -> str:
    return re.sub(r"【[^】]*†source】", "", text).strip()

def display_contexts(contexts: list[dict]):
    for index, context in enumerate(contexts[:3], start=1):
        document_id = context.get("id", "N/A")
        description = remove_citation_markers(str(context.get("description", "")))
        with st.expander(f"Context {index} | Document: {document_id}"):
            st.markdown(description or "No context text returned.")

st.set_page_config(page_title="Med Chatbot", page_icon="🩺", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 35%),
                    linear-gradient(180deg, #f6fbff 0%, #eef6f2 100%);
        font-size: 1.1rem;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        width: 100%;
    }
    .hero-card {
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 1.25rem 1.5rem;
        box-shadow: none;
        backdrop-filter: none;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        color: #475569;
        font-size: 1.15rem;
        line-height: 1.5;
    }
    .stApp p,
    .stApp label,
    .stApp textarea,
    .stApp input,
    .stApp button,
    [data-testid="stCaptionContainer"],
    [data-testid="stChatMessageContent"],
    [data-testid="stExpander"] {
        font-size: 1.1rem;
    }
    .stMarkdown, [data-testid="stChatMessageContent"], [data-testid="stExpander"] {
        overflow-wrap: anywhere;
    }
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 1.5rem;
        }
        .hero-card {
            border-radius: 16px;
            padding: 1rem;
        }
        .hero-title {
            font-size: 1.6rem;
        }
        .hero-subtitle {
            font-size: 1.05rem;
        }
    }
    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
        .hero-title {
            font-size: 1.35rem;
        }
        .hero-subtitle {
            font-size: 1rem;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem;
        }
        [data-testid="stChatMessage"] {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

header_title, header_action = st.columns([5, 1])
with header_title:
    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-title">Medical RAG Chatbot</div>
          <div class="hero-subtitle">OpenAI GPT 5 mini model + Azure AI Search retrieval over an indexed medical corpus.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_action:
    clear_chat = st.button("Clear chat", use_container_width=True)

api_url = DEFAULT_API_URL

if clear_chat:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
elif not any(message.get("role") == "system" for message in st.session_state.messages):
    st.session_state.messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

st.caption("Azure Function handles conversation history, retrieval, and answer generation.")
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            display_contexts(message.get("contexts", []))
st.text_area(
    "Example prompts",
    value="""\t1. List the human genes encoding for the dishevelled proteins?\t2. What is the mode of inheritance of Facioscapulohumeral muscular dystrophy (FSHD)?\t3. What is HIV?""",
    height="content",
)
user_prompt = st.chat_input("Ask a medical question about the indexed corpus.")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching the corpus and generating an answer..."):
            chat_history = [
                {"role": message["role"], "content": message["content"]}
                for message in st.session_state.messages
            ]
            answer_text, contexts = call_backend(
                api_url=api_url,
                chat_history=chat_history,
            )
            answer_text = remove_citation_markers(answer_text)
            if not answer_text.strip():
                answer_text = "No answer returned by the backend."

            answer = answer_text
            st.markdown(answer)
            display_contexts(contexts)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "contexts": contexts[:3]}
    )

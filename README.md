# Medical RAG Chatbot

An intelligent, enterprise-grade Medical Retrieval-Augmented Generation (RAG) chatbot designed to query curated medical literature and return accurate, context-aware answers with cited sources[cite: 1].

---

## 🌟 Key Features

* **Retrieval-Augmented Generation (RAG):** Connects Azure AI Foundry agents with Azure AI Search index for grounded document retrieval over a curated medical text corpus[cite: 1].
* **Serverless Middleware:** Azure Functions HTTP API handles multi-turn chat requests, communicates with Azure OpenAI Responses API, and extracts retrieved document metadata[cite: 1].
* **Interactive UI:** Streamlit-powered chat interface featuring conversational memory, responsive UI layout, citation cleanup, and expandable retrieved-context passages[cite: 1].
* **Automated Data Pipeline:** Automated corpus ingestion from Parquet files into Azure AI Search using batched document indexing[cite: 1].

---

## 🛠️ Tech Stack & Tools

* **Language:** Python[cite: 1]
* **Frontend:** Streamlit[cite: 1]
* **Cloud & Serverless:** Azure Functions, Azure Identity, Requests[cite: 1]
* **AI & Search:** Azure AI Foundry, Azure OpenAI Responses API, Azure AI Search[cite: 1]
* **Data Processing:** Pandas (Parquet ingestion)[cite: 1]

---

## 🏗️ System Architecture

```text
[ Parquet Data ] ──> [ Batch Ingestion (Pandas) ] ──> [ Azure AI Search ]
                                                              │
[ Streamlit UI ] <──> [ Azure Functions API ] <──> [ Azure AI Foundry / OpenAI ]

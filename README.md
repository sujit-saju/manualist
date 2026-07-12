# Manualist

An AI agent that answers questions about your documents. Upload a file or paste a link, and ask it anything — get summaries, step-by-step instructions, or answers to specific questions, without digging through pages yourself.

## What it does

- Ingests documents (PDF, or a link) 
- Chunks and embeds the content for retrieval
- Answers questions using RAG (Retrieval-Augmented Generation)
- Can summarize whole documents or pull out specific steps (e.g. installation guides)

## Status

🚧 Work in progress — built as a learning project to explore AI agent concepts (RAG, embeddings, tool-calling, ReAct-style loops).

## Tech Stack

- Backend: Python (FastAPI/Quart)
- Vector store: Chroma
- Embeddings: sentence-transformers
- LLM: Claude / OpenAI API
- Frontend: React

## Setup

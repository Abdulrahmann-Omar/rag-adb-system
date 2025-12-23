---
title: ADB Course RAG System
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
---

# 📚 ADB Course RAG System

An intelligent Question-Answering system for Advanced Databases course materials, featuring:

- **Hybrid Retrieval**: FAISS (semantic) + BM25 (keyword) search
- **Dynamic Upload**: Add new PDFs with intelligent conflict resolution  
- **Self-Learning**: Adaptive query expansion and feedback integration
- **Beautiful UI**: Glassmorphism progress visualization

## Features

- 🔍 **Semantic Search** - Understands query meaning
- 📊 **BM25 Keyword Search** - Precise term matching
- ⚖️ **Hybrid Fusion** - Best of both approaches
- 📤 **Dynamic Upload** - Add documents with REPLACE/MERGE/INSERT logic
- 🧠 **Query Expansion** - LLM-enhanced queries
- 💬 **Feedback System** - Learns from user ratings

## Tech Stack

- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS
- **LLM**: GitHub Models API (GPT-4o-mini)
- **UI**: Streamlit with glassmorphism CSS
- **Deployment**: HuggingFace Spaces

## Usage

1. Ask a question about databases, SQL, indexing, transactions, etc.
2. Upload additional PDFs to expand the knowledge base
3. Provide feedback to help the system learn

---

*Built for ADB Course @ Zewail City*

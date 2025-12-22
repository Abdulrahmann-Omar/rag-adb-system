# ADB Course RAG System

A Retrieval-Augmented Generation system for Advanced Databases course materials, featuring vector database storage, hybrid retrieval, context-aware generation, self-learning capabilities, and an interactive Gradio UI.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your GitHub token:

```bash
cp .env.example .env
```

Edit `.env` and set your `GITHUB_TOKEN`:
```env
GITHUB_TOKEN=your_github_token_here
```

### 3. Build Index

```bash
python main.py --build-index
```

### 4. Launch UI

```bash
python app.py
```

Then open http://localhost:7860 in your browser.

## 📁 Project Structure

```
RAG/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── config.py             # Configuration management
│   ├── document_processor.py # PDF extraction & chunking
│   ├── vector_store.py       # FAISS & BM25 indexing
│   ├── retriever.py          # Hybrid retrieval logic
│   ├── generator.py          # LLM integration
│   ├── self_learning.py      # Feedback & adaptation
│   └── utils.py              # Helper functions
│
├── data/
│   ├── processed/            # Extracted text files
│   └── vector_store/         # Saved FAISS index
│
├── logs/
│   ├── queries.jsonl         # Query history
│   └── feedback.jsonl        # User feedback
│
├── app.py                    # Gradio UI
├── main.py                   # CLI interface
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🎯 Features

### Core RAG System
- **Vector Database**: FAISS for efficient similarity search
- **Hybrid Retrieval**: Combines semantic (FAISS) and keyword (BM25) search
- **LLM Generation**: GitHub Models API (GPT-4o-mini) for context-aware responses

### Self-Learning Layer
- **Feedback Collection**: Track user ratings (👍/👎)
- **Query Expansion**: Automatically improve unclear queries
- **Adaptive Retrieval**: Adjust parameters based on query complexity

### User Interface
- **Chat Interface**: Conversational Q&A with history
- **Source Display**: View retrieved document chunks
- **Feedback Buttons**: Rate response quality
- **Statistics Panel**: Monitor system performance

## 🖥️ Usage

### CLI Commands

```bash
# Build/rebuild index
python main.py --build-index

# Force rebuild
python main.py --build-index --force

# Single query
python main.py --query "What is ACID?"

# Interactive mode
python main.py --interactive

# Check environment
python main.py --check

# Launch UI
python main.py --ui
```

### Python API

```python
from src.self_learning import SelfLearningRAG

# Initialize
rag = SelfLearningRAG()
rag.initialize()

# Query
result, metadata = rag.query("What are ACID properties?")
print(result.response)
print(result.sources)

# Provide feedback
rag.submit_feedback("positive")
```

## 🏗️ Architecture

```
User Query → Embedding → Vector Search → Context Retrieval → LLM Generation → Response
                ↓                                                    ↓
          Vector DB (FAISS)                              Self-Learning (Feedback Loop)
                                                                     ↓
                                                              UI (Gradio)
```

### Design Choices

| Component | Choice | Justification |
|-----------|--------|---------------|
| Embedding | all-MiniLM-L6-v2 | Free, fast, 384 dimensions |
| Vector DB | FAISS | In-memory, efficient for small corpus |
| Similarity | Cosine + BM25 | Semantic + keyword precision |
| LLM | GitHub Models | Free tier, OpenAI-compatible |
| UI | Gradio | Rapid prototyping, built-in chat |

## 📊 Evaluation

### Test Queries

1. **Factual**: "What are the ACID properties?"
2. **Conceptual**: "Explain B+ tree indexing advantages"
3. **Comparative**: "Difference between SQL and NoSQL"
4. **Edge Case**: "What is machine learning?" (not in lectures)

## 🔧 Configuration

Key settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| GITHUB_TOKEN | - | GitHub API token |
| MODEL_NAME | gpt-4o-mini | LLM model to use |
| CHUNK_SIZE | 1000 | Document chunk size |
| CHUNK_OVERLAP | 200 | Chunk overlap |
| TOP_K | 5 | Default retrieval count |

## 📝 License

This project is for educational purposes as part of the ADB course.

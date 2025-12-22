# ADB Course RAG System - Architecture

## System Overview
The system follows a standard RAG architecture enhanced with hybrid retrieval (Dense + Sparse) and a self-learning feedback loop.

```mermaid
graph TD
    subgraph "Data Ingestion"
        A[PDF Lectures] --> B[Document Processor]
        B --> C[Recursive Text Splitter]
        C --> D[Chunks with Metadata]
    end

    subgraph "Indexing"
        D --> E[MiniLM-L6-v2 Embedder]
        E --> F[(FAISS Vector Store)]
        D --> G[(BM25 Keyword Index)]
    end

    subgraph "Retrieval Module"
        H[User Query] --> I[Query Expander - LLM]
        I --> J[Adaptive Retriever]
        J -- Semantic Search --> F
        J -- Keyword Search --> G
        F --> K[Hybrid Score Fusion]
        G --> K
        K --> L[Retrieved Contexts]
    end

    subgraph "Generation Module"
        L --> M[Prompt Builder]
        H --> M
        M --> N[GitHub Models - GPT-4o-mini]
        N --> O[Final Response with Citations]
    end

    subgraph "Self-Learning Layer"
        O --> P[User Feedback - Thumb Up/Down]
        P --> Q[Feedback Collector]
        Q --> R[(Feedback/Query Logs)]
        R -- Analytics --> J
    end
```

## Key Components
1. **Hybrid Search**: Combines semantic understanding (FAISS) with exact keyword matching (BM25) to handle technical database terminology effectively.
2. **Query Expansion**: Uses the LLM to rephrase short or ambiguous queries into detailed search prompts.
3. **Adaptive Retrieval**: Adjusts the number of retrieved documents (`top_k`) based on the confidence scores of the initial retrieval.
4. **Citation Engine**: Automatically maps retrieved chunks back to their source PDF and page number for academic integrity.

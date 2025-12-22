# Technical Report: ADB Course RAG System
**Course**: Advanced Databases (ADB)
**Student**: Abdulrahman Omar
**Date**: December 23, 2025

---

## 1. Introduction
This project implements a Retrieval-Augmented Generation (RAG) system specifically designed for the Advanced Databases course. The goal is to provide students with an intelligent assistant that can answer technical questions about database theory, transactions, indexing, and NoSQL systems by grounding its responses in course lectures.

## 2. System Design Choices

### 2.1 Embedding Model: all-MiniLM-L6-v2
We selected the `all-MiniLM-L6-v2` model from Sentence-Transformers. 
- **Justification**: It provides a perfect balance between performance and efficiency. With 384 dimensions, it is fast to index and query while maintaining high semantic accuracy for academic text.

### 2.2 Vector Database: FAISS
For the vector store, we chose **FAISS (Facebook AI Similarity Search)**.
- **Justification**: Given the dataset size (8-9 PDFs, ~500 chunks), an in-memory vector store like FAISS is extremely fast and requires no external server infrastructure, making the system lightweight and portable.

### 2.3 Hybrid Retrieval (0.7 Semantic + 0.3 Keyword)
The retrieval mechanism combines Dense (FAISS) and Sparse (BM25) search.
- **Justification**: Database terminology often involves specific keywords (e.g., "ACID", "B+Tree", "WAL"). While semantic search understands the *concept*, BM25 ensures we precisely match these exact terms. We used a 70/30 weight distribution to prioritize meaning while respecting terminology.

## 3. Implementation Details

### 3.1 Document Processing
- **Extraction**: Used `pdfplumber` for high-fidelity text extraction.
- **Chunking**: Implemented `RecursiveCharacterTextSplitter` with a chunk size of 1000 characters and an overlap of 200. This ensures that context is preserved across chunk boundaries.

### 3.2 Generation & Prompt Engineering
We utilized the **GitHub Models API (GPT-4o-mini)**. The system prompt enforces strict grounding: "Answer only based on the provided context. If the answer is not in the context, state that you do not know."

## 4. Bonus Features: Self-Learning Layer
The system includes three "Self-Learning" components:
1. **Query Expansion**: If a user enters a brief query like "ACID", the LLM expands it to "Explain the ACID properties and their role in transactions" to improve retrieval quality.
2. **Adaptive Retrieval**: The system dynamically adjusts `top_k` based on the retrieval confidence scores.
3. **Feedback Loop**: A UI allows users to rate responses (👍/👎), which are logged for future fine-tuning or hard-negative mining.

## 5. Demonstrations & Results

### Example 1: Factual Retrieval
**Query**: "What are ACID properties?"
**Observation**: The system successfully retrieved Lecture 7 and provided a categorized list with page-level citations.

### Example 2: Query Expansion
**Query**: "Explain transactions"
**Behavior**: The system expanded the query to include properties and significance, leading to a much richer retrieved context.

*(Insert UI Screenshots here)*

## 6. Critical Analysis
- **Strengths**: High citation accuracy, fast retrieval, and professional UI.
- **Limitations**: Performance depends on PDF text quality; cold start for self-learning.
- **Future Work**: Implementing Graph-RAG for cross-lecture conceptual linking.

---
## 7. References
- Course Lectures: ADB_Lec01 - ADB_Lec09
- Sentence-Transformers Documentation
- FAISS Research Paper

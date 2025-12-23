# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-12-23

### Added

- **Core RAG Pipeline**
  - PDF document processing with pdfplumber
  - Text chunking with configurable size and overlap
  - Document metadata preservation (source, page numbers)

- **Vector Store**
  - FAISS index for semantic similarity search
  - BM25 index for keyword matching
  - Automatic persistence to disk
  - Dynamic document addition and removal

- **Hybrid Retrieval**
  - Combined semantic (70%) and keyword (30%) search
  - Configurable weights for score fusion
  - Top-K document selection

- **LLM Generation**
  - GitHub Models API integration (GPT-4o-mini)
  - Context-aware answer generation
  - Source citation in responses

- **Self-Learning System**
  - User feedback collection (positive/negative)
  - Query expansion for ambiguous questions
  - Learning statistics dashboard

- **Progress Visualization**
  - Multi-stage pipeline indicators
  - Real-time metrics (time, chunks, progress)
  - Beautiful dark-mode UI animations

- **Dynamic Document Upload**
  - PDF upload through Streamlit UI
  - Real-time processing feedback
  - Incremental index updates

- **Streamlit UI**
  - Professional dark-mode interface
  - Query input with example suggestions
  - Source display with relevance scores
  - Feedback buttons
  - Sidebar with statistics

- **Documentation**
  - Comprehensive README
  - Architecture documentation
  - API reference
  - Deployment guide
  - Development guide
  - Contributing guidelines

### Technical Details

- Python 3.10+ support
- Sentence-transformers (all-MiniLM-L6-v2) for embeddings
- FAISS-CPU for vector storage
- OpenAI-compatible API for LLM
- Streamlit for web interface

---

## [Unreleased]

### Planned

- Multi-language document support
- Advanced query understanding (NER, intent classification)
- Graph-based retrieval
- Fine-tuned domain embeddings
- Export/import functionality
- API endpoint mode

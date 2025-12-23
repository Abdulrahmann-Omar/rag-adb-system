# Development Guide

Guide for developers contributing to or extending the RAG system.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool (venv, conda)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/rag-adb-system.git
cd rag-adb-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install all dependencies (including dev)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your GITHUB_TOKEN

# Verify setup
python -c "from src.config import config; config.print_config()"
```

---

## Project Structure

```
rag-adb-system/
├── src/                          # Source code
│   ├── __init__.py               # Package init
│   ├── config.py                 # Configuration management
│   ├── document_processor.py     # PDF extraction & chunking
│   ├── vector_store.py           # FAISS + BM25 indexing
│   ├── retriever.py              # Hybrid retrieval
│   ├── generator.py              # LLM generation
│   ├── self_learning.py          # Main RAG orchestrator
│   ├── dynamic_updater.py        # Dynamic document updates
│   ├── progress_viz.py           # Progress visualization
│   └── utils.py                  # Utility functions
│
├── data/                         # Runtime data (gitignored)
│   ├── processed/                # Extracted text cache
│   └── vector_store/             # FAISS index
│
├── docs/                         # Documentation
├── logs/                         # Query and feedback logs
├── tests/                        # Test suite
├── .github/                      # GitHub workflows
│
├── app.py                        # Streamlit application
├── main.py                       # CLI interface
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
└── README.md                     # Project documentation
```

---

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

- **Line length**: 100 characters max
- **Imports**: Grouped (stdlib, third-party, local)
- **Type hints**: Required for public functions
- **Docstrings**: Google style

### Example

```python
"""
Module description here.
"""

from pathlib import Path
from typing import List, Optional

import pdfplumber
from langchain.schema import Document

from src.config import config


def process_document(
    file_path: Path,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[Document]:
    """
    Process a PDF document into chunks.
    
    Args:
        file_path: Path to the PDF file.
        chunk_size: Maximum characters per chunk.
        overlap: Overlap between consecutive chunks.
    
    Returns:
        List of Document objects with content and metadata.
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the PDF is corrupted.
    
    Example:
        >>> docs = process_document(Path("lecture.pdf"))
        >>> print(len(docs))
        42
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    
    # Implementation here...
    return documents
```

### Linting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

---

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_document_processor.py
├── test_vector_store.py
├── test_retriever.py
├── test_generator.py
└── test_integration.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_retriever.py

# Run specific test function
pytest tests/test_retriever.py::test_hybrid_search

# Verbose output
pytest tests/ -v
```

### Writing Tests

```python
"""Tests for vector store module."""

import pytest
from pathlib import Path
from src.vector_store import HybridVectorStore


@pytest.fixture
def vector_store(tmp_path):
    """Create a temporary vector store."""
    return HybridVectorStore(persist_path=str(tmp_path / "store"))


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    from langchain.schema import Document
    return [
        Document(page_content="ACID properties in databases", metadata={"page": 1}),
        Document(page_content="B+ tree indexing structures", metadata={"page": 2}),
    ]


class TestVectorStore:
    """Test cases for HybridVectorStore."""
    
    def test_add_documents(self, vector_store, sample_documents):
        """Test adding documents to store."""
        count = vector_store.add_documents(sample_documents)
        assert count == 2
    
    def test_search_returns_results(self, vector_store, sample_documents):
        """Test that search returns relevant results."""
        vector_store.add_documents(sample_documents)
        results = vector_store.search("ACID", top_k=1)
        
        assert len(results) == 1
        assert "ACID" in results[0][0].page_content
    
    def test_empty_search(self, vector_store):
        """Test search on empty store."""
        results = vector_store.search("query", top_k=5)
        assert results == []
```

---

## Adding Features

### Feature Branch Workflow

```bash
# Start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-new-feature

# Make changes...

# Commit with clear message
git add .
git commit -m "feat: add multi-language support"

# Push branch
git push origin feature/my-new-feature

# Create Pull Request on GitHub
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructure
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(retriever): add BM25 keyword search
fix(generator): handle empty context gracefully
docs(readme): add deployment instructions
test(vector_store): add persistence tests
```

### Pull Request Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] Code formatted (`black`, `isort`)
- [ ] Type hints added for new functions
- [ ] Docstrings updated
- [ ] Documentation updated if needed
- [ ] No secrets or sensitive data committed

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Detailed debug info")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error occurred")
```

### Debug Mode

Set in `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "GITHUB_TOKEN not set" | Missing env var | Check `.env` file |
| "No documents indexed" | Empty vector store | Upload PDFs first |
| Import errors | Wrong Python path | Run from project root |
| FAISS issues | Version mismatch | Use `faiss-cpu==1.7.4` |

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json:
{
    "name": "Streamlit Debug",
    "type": "python",
    "request": "launch",
    "module": "streamlit",
    "args": ["run", "app.py"]
}
```

---

## Architecture Decisions

When modifying architecture, document decisions in `docs/architecture.md`:

1. **What** was decided
2. **Why** this approach was chosen
3. **Alternatives** considered
4. **Tradeoffs** accepted

Example:
```markdown
### Decision: Use FAISS instead of ChromaDB

**Date**: 2024-12-23

**Status**: Accepted

**Context**: Need a vector database for similarity search.

**Decision**: Use FAISS (faiss-cpu) for vector storage.

**Reasoning**:
- No external server needed (embedded)
- Faster for small-medium datasets
- Simpler deployment

**Alternatives Considered**:
- ChromaDB: More features but requires server
- Pinecone: Cloud-based, API limits

**Tradeoffs**:
- Less features than ChromaDB
- Manual persistence management
```

---

## Performance Profiling

### Timing Decorator

```python
import time
import functools

def timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__}: {elapsed:.3f}s")
        return result
    return wrapper

@timing
def slow_function():
    # ...
```

### Memory Profiling

```bash
pip install memory-profiler

python -m memory_profiler app.py
```

---

## Release Process

1. Update `CHANGELOG.md`
2. Update version in relevant files
3. Create git tag: `git tag -a v1.1.0 -m "Release 1.1.0"`
4. Push tag: `git push origin v1.1.0`
5. Create GitHub release with changelog

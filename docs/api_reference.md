# API Reference

Complete API documentation for all public modules and classes.

---

## SelfLearningRAG

**File**: `src/self_learning.py`

The main entry point for the RAG system with self-learning capabilities.

### Class: `SelfLearningRAG`

```python
from src.self_learning import SelfLearningRAG

rag = SelfLearningRAG()
```

#### Methods

##### `initialize(force_rebuild: bool = False) -> None`

Initialize the RAG system, loading or building indexes.

**Parameters**:
- `force_rebuild` (bool): If True, rebuild index even if exists. Default: False

**Example**:
```python
rag = SelfLearningRAG()
rag.initialize()  # Load existing index
rag.initialize(force_rebuild=True)  # Rebuild from PDFs
```

---

##### `query(question: str, enable_expansion: bool = True, top_k: int = 5) -> Tuple[RAGResult, Dict]`

Query the RAG system.

**Parameters**:
- `question` (str): User's question
- `enable_expansion` (bool): Enable query expansion for unclear queries. Default: True
- `top_k` (int): Number of documents to retrieve. Default: 5

**Returns**:
- `RAGResult`: Object with `.response` (str) and `.sources` (list)
- `Dict`: Metadata including expansion info, timing

**Example**:
```python
result, metadata = rag.query("What are ACID properties?")

print(result.response)  # The generated answer
print(result.sources)   # List of source documents

# Check if query was expanded
if metadata.get('was_expanded'):
    print(f"Expanded to: {metadata['expanded_query']}")
```

---

##### `submit_feedback(rating: str) -> None`

Submit feedback for the last query.

**Parameters**:
- `rating` (str): Either "positive" or "negative"

**Example**:
```python
result, _ = rag.query("Explain B+ trees")
# User found it helpful
rag.submit_feedback("positive")
```

---

##### `get_learning_stats() -> Dict`

Get statistics about the self-learning system.

**Returns**:
- `Dict`: Contains feedback counts, query history stats

**Example**:
```python
stats = rag.get_learning_stats()
print(f"Total feedback: {stats['feedback']['total']}")
print(f"Positive rate: {stats['feedback']['positive'] / stats['feedback']['total']:.0%}")
```

---

##### `is_ready -> bool`

Property indicating if the system is ready for queries.

**Example**:
```python
if rag.is_ready:
    result, _ = rag.query("My question")
else:
    print("Please upload documents first")
```

---

## DocumentProcessor

**File**: `src/document_processor.py`

Handles PDF extraction and text chunking.

### Class: `PDFProcessor`

```python
from src.document_processor import PDFProcessor

processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
```

#### Constructor

**Parameters**:
- `chunk_size` (int): Maximum characters per chunk. Default: 1000
- `chunk_overlap` (int): Overlap between chunks. Default: 200

---

#### Methods

##### `process_file(file_path: Path) -> List[Document]`

Process a single PDF file.

**Parameters**:
- `file_path` (Path): Path to PDF file

**Returns**:
- `List[Document]`: List of document chunks with metadata

**Example**:
```python
from pathlib import Path

processor = PDFProcessor()
docs = processor.process_file(Path("lecture.pdf"))

for doc in docs:
    print(f"Page {doc.metadata['page']}: {doc.page_content[:100]}...")
```

---

##### `process_directory(dir_path: Path) -> List[Document]`

Process all PDFs in a directory.

**Parameters**:
- `dir_path` (Path): Path to directory containing PDFs

**Returns**:
- `List[Document]`: Combined list of all document chunks

**Example**:
```python
docs = processor.process_directory(Path("Lectures/"))
print(f"Processed {len(docs)} chunks from directory")
```

---

## VectorStore

**File**: `src/vector_store.py`

Manages FAISS and BM25 indexes.

### Class: `HybridVectorStore`

```python
from src.vector_store import HybridVectorStore

store = HybridVectorStore(persist_path="data/vector_store")
```

#### Constructor

**Parameters**:
- `persist_path` (str): Directory for saving/loading indexes
- `embedding_model` (str): HuggingFace model name. Default: config value

---

#### Methods

##### `add_documents(documents: List[Document]) -> int`

Add documents to the index.

**Parameters**:
- `documents` (List[Document]): Document chunks to add

**Returns**:
- `int`: Number of documents added

**Example**:
```python
from src.document_processor import PDFProcessor

processor = PDFProcessor()
docs = processor.process_file(Path("new_lecture.pdf"))
count = store.add_documents(docs)
print(f"Added {count} chunks to index")
```

---

##### `search(query: str, top_k: int = 5) -> List[Tuple[Document, float]]`

Search the index with hybrid retrieval.

**Parameters**:
- `query` (str): Search query
- `top_k` (int): Number of results. Default: 5

**Returns**:
- `List[Tuple[Document, float]]`: Documents with relevance scores

**Example**:
```python
results = store.search("ACID properties", top_k=3)
for doc, score in results:
    print(f"Score {score:.3f}: {doc.page_content[:100]}...")
```

---

##### `save() -> None`

Persist indexes to disk.

```python
store.save()
```

---

##### `load() -> bool`

Load indexes from disk.

**Returns**:
- `bool`: True if loaded successfully

```python
if store.load():
    print("Index loaded")
else:
    print("No existing index found")
```

---

## HybridRetriever

**File**: `src/retriever.py`

Combines semantic and keyword search.

### Class: `HybridRetriever`

```python
from src.retriever import HybridRetriever

retriever = HybridRetriever(
    vector_store=store,
    semantic_weight=0.7,
    keyword_weight=0.3
)
```

#### Methods

##### `retrieve(query: str, top_k: int = 5) -> List[Document]`

Retrieve relevant documents using hybrid search.

**Parameters**:
- `query` (str): User query
- `top_k` (int): Number of documents to return

**Returns**:
- `List[Document]`: Ranked relevant documents

---

##### `get_statistics() -> Dict`

Get retriever statistics.

**Returns**:
- `Dict`: Contains document count, weights, etc.

---

## ContextualGenerator

**File**: `src/generator.py`

LLM-powered answer generation.

### Class: `ContextualGenerator`

```python
from src.generator import ContextualGenerator

generator = ContextualGenerator()
```

#### Methods

##### `generate(query: str, context: List[Document]) -> str`

Generate an answer using retrieved context.

**Parameters**:
- `query` (str): User question
- `context` (List[Document]): Retrieved document chunks

**Returns**:
- `str`: Generated answer

**Example**:
```python
docs = retriever.retrieve("What is normalization?")
answer = generator.generate("What is normalization?", docs)
print(answer)
```

---

## DynamicUpdatePipeline

**File**: `src/dynamic_updater.py`

Handles dynamic document updates with progress callbacks.

### Class: `DynamicUpdatePipeline`

```python
from src.dynamic_updater import DynamicUpdatePipeline

pipeline = DynamicUpdatePipeline(vector_store, llm_client)
```

#### Methods

##### `process_document(pdf_path: Path, progress_callback: Callable = None) -> Dict`

Process and add a new document to the index.

**Parameters**:
- `pdf_path` (Path): Path to PDF file
- `progress_callback` (Callable): Function called with (stage, progress, message)

**Returns**:
- `Dict`: Processing results including chunks_processed, actions, success, errors

**Example**:
```python
def on_progress(stage, progress, message):
    print(f"[{stage}] {progress:.0%} - {message}")

result = pipeline.process_document(
    Path("new_lecture.pdf"),
    progress_callback=on_progress
)

print(f"Processed {result['chunks_processed']} chunks")
```

---

## Config

**File**: `src/config.py`

Configuration management.

### Class: `Config`

Access configuration values as class attributes.

```python
from src.config import config

print(config.CHUNK_SIZE)        # 1000
print(config.EMBEDDING_MODEL)   # sentence-transformers/all-MiniLM-L6-v2
print(config.TOP_K)             # 5
```

#### Attributes

| Attribute | Type | Default |
|-----------|------|---------|
| `GITHUB_TOKEN` | str | *from env* |
| `MODEL_NAME` | str | "gpt-4o-mini" |
| `EMBEDDING_MODEL` | str | "sentence-transformers/all-MiniLM-L6-v2" |
| `CHUNK_SIZE` | int | 1000 |
| `CHUNK_OVERLAP` | int | 200 |
| `TOP_K` | int | 5 |
| `SEMANTIC_WEIGHT` | float | 0.7 |
| `KEYWORD_WEIGHT` | float | 0.3 |

#### Methods

##### `validate() -> bool`

Check if required configuration is present.

```python
if config.validate():
    print("Configuration valid")
else:
    print("Missing required configuration")
```

##### `print_config() -> None`

Print current configuration for debugging.

```python
config.print_config()
```

---

## Data Classes

### RAGResult

Result from a RAG query.

```python
@dataclass
class RAGResult:
    response: str           # Generated answer
    sources: List[Document] # Retrieved source documents
    confidence: float       # Confidence score (0-1)
```

### Document

LangChain Document class used throughout.

```python
from langchain.schema import Document

doc = Document(
    page_content="Text content here...",
    metadata={
        "source": "lecture1.pdf",
        "page": 5,
        "chunk_id": 42
    }
)
```

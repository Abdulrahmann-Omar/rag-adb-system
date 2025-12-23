"""
Vector Store Module
Handles embeddings generation, FAISS indexing, and BM25 keyword search.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from rank_bm25 import BM25Okapi
from tqdm import tqdm

from .config import config
from .document_processor import Document


class EmbeddingManager:
    """Manages embedding generation using sentence-transformers."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingManager._model is None:
            import os
            # Increase timeout for slow connections
            os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '120'
            os.environ['TRANSFORMERS_OFFLINE'] = '0'
            
            print(f"🔄 Loading embedding model: {config.EMBEDDING_MODEL}")
            print("   (This may take a few minutes on first run...)")
            
            try:
                EmbeddingManager._model = SentenceTransformer(
                    config.EMBEDDING_MODEL,
                    trust_remote_code=True
                )
                print("✅ Embedding model loaded!")
            except Exception as e:
                print(f"⚠️  Error loading model: {e}")
                print("   Trying with local cache only...")
                # Try offline mode if network fails
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_HUB_OFFLINE'] = '1'
                try:
                    EmbeddingManager._model = SentenceTransformer(
                        config.EMBEDDING_MODEL,
                        trust_remote_code=True
                    )
                    print("✅ Embedding model loaded from cache!")
                except Exception as e2:
                    print(f"❌ Failed to load model: {e2}")
                    print("\n💡 Solutions:")
                    print("   1. Check your internet connection")
                    print("   2. Try using a VPN")
                    print("   3. Run: huggingface-cli download sentence-transformers/all-MiniLM-L6-v2")
                    raise
    
    @property
    def model(self) -> SentenceTransformer:
        return EmbeddingManager._model
    
    def embed_texts(
        self, 
        texts: List[str], 
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            show_progress: Whether to show progress bar
            
        Returns:
            numpy array of embeddings (n_texts, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query string
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self.model.encode(query, convert_to_numpy=True)


class FAISSVectorStore:
    """FAISS-based vector store for semantic search."""
    
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
    
    def build_index(self, documents: List[Document]) -> None:
        """
        Build FAISS index from documents.
        
        Args:
            documents: List of Document objects
        """
        self.documents = documents
        texts = [doc.content for doc in documents]
        
        print("\n🔄 Generating embeddings...")
        self.embeddings = self.embedding_manager.embed_texts(texts)
        
        # Normalize embeddings for cosine similarity (using inner product)
        faiss.normalize_L2(self.embeddings)
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product = cosine for normalized vectors
        self.index.add(self.embeddings)
        
        print(f"✅ FAISS index built with {self.index.ntotal} vectors (dim={dimension})")
    
    def search(
        self, 
        query: str, 
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")
        
        top_k = top_k or config.TOP_K
        
        # Get query embedding
        query_embedding = self.embedding_manager.embed_query(query)
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save(self, path: Path = None) -> None:
        """Save index and documents to disk."""
        path = path or config.VECTOR_STORE_PATH
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "faiss.index"))
        
        # Save documents and embeddings
        with open(path / "documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        np.save(path / "embeddings.npy", self.embeddings)
        
        print(f"💾 Vector store saved to {path}")
    
    def load(self, path: Path = None) -> bool:
        """Load index and documents from disk."""
        path = path or config.VECTOR_STORE_PATH
        
        try:
            self.index = faiss.read_index(str(path / "faiss.index"))
            
            with open(path / "documents.pkl", "rb") as f:
                self.documents = pickle.load(f)
            
            self.embeddings = np.load(path / "embeddings.npy")
            
            print(f"✅ Vector store loaded: {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"⚠️  Could not load vector store: {e}")
            return False
    
    def add_documents(
        self, 
        new_documents: List[Document],
        save_after: bool = True
    ) -> int:
        """
        Add new documents to existing FAISS index incrementally.
        
        Args:
            new_documents: List of new Document objects to add
            save_after: Whether to save the updated index to disk
            
        Returns:
            Number of documents added
        """
        if not new_documents:
            return 0
        
        if self.index is None:
            # First time - build from scratch
            self.build_index(new_documents)
            if save_after:
                self.save()
            return len(new_documents)
        
        # Generate embeddings for new documents
        texts = [doc.content for doc in new_documents]
        new_embeddings = self.embedding_manager.embed_texts(texts, show_progress=True)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(new_embeddings)
        
        # Add to FAISS index
        self.index.add(new_embeddings)
        
        # Update internal state
        self.documents.extend(new_documents)
        self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        print(f"✅ Added {len(new_documents)} documents to FAISS index (total: {len(self.documents)})")
        
        if save_after:
            self.save()
        
        return len(new_documents)
    
    def remove_documents(
        self, 
        doc_indices: List[int],
        save_after: bool = True
    ) -> int:
        """
        Remove documents from FAISS index by their indices.
        Note: FAISS doesn't support efficient deletion, so we rebuild the index
        excluding the specified documents.
        
        Args:
            doc_indices: List of document indices to remove
            save_after: Whether to save the updated index to disk
            
        Returns:
            Number of documents removed
        """
        if not doc_indices or self.index is None:
            return 0
        
        # Create mask for documents to keep
        keep_mask = np.ones(len(self.documents), dtype=bool)
        for idx in doc_indices:
            if 0 <= idx < len(self.documents):
                keep_mask[idx] = False
        
        # Filter documents and embeddings
        self.documents = [doc for i, doc in enumerate(self.documents) if keep_mask[i]]
        self.embeddings = self.embeddings[keep_mask]
        
        # Rebuild FAISS index with remaining embeddings
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)
        
        removed_count = len(doc_indices)
        print(f"✅ Removed {removed_count} documents from FAISS index (remaining: {len(self.documents)})")
        
        if save_after:
            self.save()
        
        return removed_count
    
    def get_document_sources(self) -> List[Dict[str, Any]]:
        """Get list of unique document sources with metadata."""
        sources = {}
        for i, doc in enumerate(self.documents):
            source = doc.metadata.get('source', 'Unknown')
            if source not in sources:
                sources[source] = {
                    'filename': source,
                    'chunk_count': 0,
                    'chunk_indices': [],
                    'pages': set()
                }
            sources[source]['chunk_count'] += 1
            sources[source]['chunk_indices'].append(i)
            if 'page' in doc.metadata:
                sources[source]['pages'].add(doc.metadata['page'])
        
        # Convert sets to sorted lists
        for source in sources.values():
            source['pages'] = sorted(list(source['pages']))
        
        return list(sources.values())


class BM25Index:
    """BM25-based keyword search index."""
    
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
    
    def build_index(self, documents: List[Document]) -> None:
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of Document objects
        """
        self.documents = documents
        
        # Tokenize documents (simple whitespace + lowercase)
        self.tokenized_corpus = [
            self._tokenize(doc.content) for doc in documents
        ]
        
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"✅ BM25 index built with {len(self.documents)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on whitespace
        return text.lower().split()
    
    def search(
        self, 
        query: str, 
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for documents using BM25.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index first.")
        
        top_k = top_k or config.TOP_K
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with positive score
                results.append((self.documents[idx], float(scores[idx])))
        
        return results
    
    def save(self, path: Path = None) -> None:
        """Save BM25 index to disk."""
        path = path or config.VECTOR_STORE_PATH
        path.mkdir(parents=True, exist_ok=True)
        
        with open(path / "bm25_data.pkl", "wb") as f:
            pickle.dump({
                'documents': self.documents,
                'tokenized_corpus': self.tokenized_corpus
            }, f)
        
        print(f"💾 BM25 index saved to {path}")
    
    def load(self, path: Path = None) -> bool:
        """Load BM25 index from disk."""
        path = path or config.VECTOR_STORE_PATH
        
        try:
            with open(path / "bm25_data.pkl", "rb") as f:
                data = pickle.load(f)
            
            self.documents = data['documents']
            self.tokenized_corpus = data['tokenized_corpus']
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            
            print(f"✅ BM25 index loaded: {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"⚠️  Could not load BM25 index: {e}")
            return False


class HybridVectorStore:
    """
    Combines FAISS (semantic) and BM25 (keyword) search.
    Uses weighted score fusion for better retrieval.
    """
    
    def __init__(
        self,
        semantic_weight: float = None,
        keyword_weight: float = None
    ):
        self.faiss_store = FAISSVectorStore()
        self.bm25_index = BM25Index()
        self.semantic_weight = semantic_weight or config.SEMANTIC_WEIGHT
        self.keyword_weight = keyword_weight or config.KEYWORD_WEIGHT
        self.documents: List[Document] = []
    
    def build_index(self, documents: List[Document]) -> None:
        """Build both FAISS and BM25 indices."""
        self.documents = documents
        
        print("\n📊 Building Hybrid Index...")
        print("-" * 40)
        
        # Build FAISS index
        self.faiss_store.build_index(documents)
        
        # Build BM25 index
        self.bm25_index.build_index(documents)
        
        print("-" * 40)
        print(f"✅ Hybrid index ready! (semantic={self.semantic_weight}, keyword={self.keyword_weight})")
    
    def search(
        self, 
        query: str, 
        top_k: int = None
    ) -> List[Tuple[Document, float, Dict[str, float]]]:
        """
        Hybrid search combining semantic and keyword results.
        
        Args:
            query: Query string
            top_k: Number of final results
            
        Returns:
            List of (Document, combined_score, score_breakdown) tuples
        """
        top_k = top_k or config.TOP_K
        
        # Get more results from each to ensure good coverage
        fetch_k = top_k * 3
        
        # Semantic search
        semantic_results = self.faiss_store.search(query, fetch_k)
        
        # Keyword search  
        keyword_results = self.bm25_index.search(query, fetch_k)
        
        # Normalize scores
        semantic_scores = self._normalize_scores(semantic_results)
        keyword_scores = self._normalize_scores(keyword_results)
        
        # Combine scores using document content as key
        combined = {}
        
        for doc, score in semantic_scores:
            key = id(doc)  # Use object id as key
            combined[key] = {
                'doc': doc,
                'semantic': score,
                'keyword': 0.0
            }
        
        for doc, score in keyword_scores:
            key = id(doc)
            if key in combined:
                combined[key]['keyword'] = score
            else:
                combined[key] = {
                    'doc': doc,
                    'semantic': 0.0,
                    'keyword': score
                }
        
        # Calculate final scores
        results = []
        for key, data in combined.items():
            final_score = (
                self.semantic_weight * data['semantic'] + 
                self.keyword_weight * data['keyword']
            )
            score_breakdown = {
                'semantic': data['semantic'],
                'keyword': data['keyword'],
                'combined': final_score
            }
            results.append((data['doc'], final_score, score_breakdown))
        
        # Sort by final score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _normalize_scores(
        self, 
        results: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """Normalize scores to 0-1 range."""
        if not results:
            return []
        
        scores = [score for _, score in results]
        max_score = max(scores) if scores else 1.0
        min_score = min(scores) if scores else 0.0
        
        if max_score == min_score:
            return [(doc, 1.0) for doc, _ in results]
        
        normalized = []
        for doc, score in results:
            norm_score = (score - min_score) / (max_score - min_score)
            normalized.append((doc, norm_score))
        
        return normalized
    
    def save(self, path: Path = None) -> None:
        """Save both indices to disk."""
        path = path or config.VECTOR_STORE_PATH
        self.faiss_store.save(path)
        self.bm25_index.save(path)
    
    def load(self, path: Path = None) -> bool:
        """Load both indices from disk."""
        path = path or config.VECTOR_STORE_PATH
        faiss_loaded = self.faiss_store.load(path)
        bm25_loaded = self.bm25_index.load(path)
        
        if faiss_loaded and bm25_loaded:
            self.documents = self.faiss_store.documents
            return True
        return False


# For testing
if __name__ == "__main__":
    from .document_processor import process_all_pdfs
    
    # Process documents
    docs = process_all_pdfs()
    
    # Build hybrid index
    store = HybridVectorStore()
    store.build_index(docs)
    
    # Test search
    query = "What is ACID?"
    results = store.search(query, top_k=3)
    
    print(f"\n🔍 Query: '{query}'")
    print("-" * 40)
    for doc, score, breakdown in results:
        print(f"\n📄 {doc.metadata['source']} (Page {doc.metadata['page']})")
        print(f"   Score: {score:.4f} (semantic={breakdown['semantic']:.3f}, keyword={breakdown['keyword']:.3f})")
        print(f"   Preview: {doc.content[:150]}...")

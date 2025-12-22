"""
Retriever Module
High-level retrieval interface with query processing and result formatting.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from .config import config
from .document_processor import Document, DocumentProcessor
from .vector_store import HybridVectorStore


@dataclass
class RetrievalResult:
    """Structured result from retrieval."""
    query: str
    documents: List[Document]
    scores: List[float]
    score_breakdowns: List[Dict[str, float]]
    
    @property
    def has_results(self) -> bool:
        return len(self.documents) > 0
    
    @property
    def top_score(self) -> float:
        return self.scores[0] if self.scores else 0.0
    
    def get_context(self, max_docs: int = None) -> str:
        """
        Format retrieved documents as context string for LLM.
        
        Args:
            max_docs: Maximum number of documents to include
            
        Returns:
            Formatted context string
        """
        docs = self.documents[:max_docs] if max_docs else self.documents
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', '?')
            
            context_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{doc.content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get formatted source information."""
        sources = []
        for i, (doc, score) in enumerate(zip(self.documents, self.scores)):
            sources.append({
                'rank': i + 1,
                'source': doc.metadata.get('source', 'Unknown'),
                'page': doc.metadata.get('page', '?'),
                'score': round(score, 4),
                'preview': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            })
        return sources


class Retriever:
    """
    Main retrieval interface for the RAG system.
    Handles document loading, indexing, and query processing.
    """
    
    def __init__(self, auto_load: bool = True):
        """
        Initialize the retriever.
        
        Args:
            auto_load: Whether to automatically load existing index
        """
        self.vector_store = HybridVectorStore()
        self.processor = DocumentProcessor()
        self.is_initialized = False
        
        if auto_load:
            self._try_load_index()
    
    def _try_load_index(self) -> bool:
        """Try to load existing index from disk."""
        if self.vector_store.load():
            self.is_initialized = True
            return True
        return False
    
    def build_index(
        self, 
        documents_path: Path = None,
        force_rebuild: bool = False
    ) -> bool:
        """
        Build or rebuild the search index.
        
        Args:
            documents_path: Path to documents directory
            force_rebuild: Force rebuild even if index exists
            
        Returns:
            True if successful
        """
        if self.is_initialized and not force_rebuild:
            print("ℹ️  Index already loaded. Use force_rebuild=True to rebuild.")
            return True
        
        # Process documents
        documents = self.processor.process_directory(documents_path)
        
        if not documents:
            print("❌ No documents processed. Cannot build index.")
            return False
        
        # Build index
        self.vector_store.build_index(documents)
        
        # Save index
        self.vector_store.save()
        
        self.is_initialized = True
        return True
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve
            
        Returns:
            RetrievalResult object
        """
        if not self.is_initialized:
            raise RuntimeError(
                "Retriever not initialized. Call build_index() first."
            )
        
        top_k = top_k or config.TOP_K
        
        # Search
        results = self.vector_store.search(query, top_k)
        
        # Unpack results
        documents = [doc for doc, _, _ in results]
        scores = [score for _, score, _ in results]
        breakdowns = [breakdown for _, _, breakdown in results]
        
        return RetrievalResult(
            query=query,
            documents=documents,
            scores=scores,
            score_breakdowns=breakdowns
        )
    
    def retrieve_with_context(
        self, 
        query: str, 
        top_k: int = None
    ) -> Tuple[str, RetrievalResult]:
        """
        Retrieve and format context for LLM.
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve
            
        Returns:
            Tuple of (context_string, RetrievalResult)
        """
        result = self.retrieve(query, top_k)
        context = result.get_context()
        return context, result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        if not self.is_initialized:
            return {'status': 'not initialized'}
        
        return {
            'status': 'initialized',
            'num_documents': len(self.vector_store.documents),
            'semantic_weight': self.vector_store.semantic_weight,
            'keyword_weight': self.vector_store.keyword_weight,
            'default_top_k': config.TOP_K
        }


def get_retriever() -> Retriever:
    """Get a retriever instance (convenience function)."""
    return Retriever(auto_load=True)


# For testing
if __name__ == "__main__":
    # Initialize retriever
    retriever = Retriever(auto_load=False)
    
    # Build index
    retriever.build_index()
    
    # Test queries
    test_queries = [
        "What is ACID?",
        "Explain B+ tree indexing",
        "What is the difference between SQL and NoSQL?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 Query: {query}")
        print("="*60)
        
        result = retriever.retrieve(query)
        
        print(f"\nTop {len(result.documents)} results:")
        for source in result.get_sources():
            print(f"\n  [{source['rank']}] {source['source']} (Page {source['page']})")
            print(f"      Score: {source['score']}")
            print(f"      Preview: {source['preview'][:100]}...")

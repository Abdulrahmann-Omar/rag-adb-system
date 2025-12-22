"""
Self-Learning Module
Implements feedback collection, query expansion, and adaptive retrieval.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from .config import config
from .retriever import RetrievalResult
from .generator import GenerationResult, GitHubModelsClient


@dataclass
class FeedbackEntry:
    """Represents a single feedback entry."""
    timestamp: str
    query: str
    response: str
    sources: List[Dict[str, Any]]
    rating: str  # 'positive', 'negative', or 'neutral'
    retrieval_score: float
    model: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        return cls(**data)


@dataclass
class QueryLogEntry:
    """Represents a query log entry."""
    timestamp: str
    query: str
    expanded_query: Optional[str]
    num_results: int
    top_score: float
    response_length: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeedbackCollector:
    """Collects and stores user feedback for learning."""
    
    def __init__(self, log_path: Path = None):
        self.log_path = log_path or config.FEEDBACK_LOG_PATH
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure log file exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()
    
    def record_feedback(
        self,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        rating: str,
        retrieval_score: float = 0.0,
        model: str = "unknown"
    ) -> FeedbackEntry:
        """
        Record user feedback for a query-response pair.
        
        Args:
            query: Original query
            response: Generated response
            sources: Retrieved sources
            rating: 'positive', 'negative', or 'neutral'
            retrieval_score: Top retrieval score
            model: Model used for generation
            
        Returns:
            FeedbackEntry object
        """
        entry = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            query=query,
            response=response,
            sources=sources,
            rating=rating,
            retrieval_score=retrieval_score,
            model=model
        )
        
        # Append to log file
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
        
        return entry
    
    def get_all_feedback(self) -> List[FeedbackEntry]:
        """Load all feedback entries."""
        entries = []
        if self.log_path.exists():
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entries.append(FeedbackEntry.from_dict(json.loads(line)))
        return entries
    
    def get_negative_feedback(self) -> List[FeedbackEntry]:
        """Get entries with negative feedback for analysis."""
        return [e for e in self.get_all_feedback() if e.rating == 'negative']
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        feedback = self.get_all_feedback()
        
        if not feedback:
            return {'total': 0}
        
        ratings = defaultdict(int)
        for entry in feedback:
            ratings[entry.rating] += 1
        
        return {
            'total': len(feedback),
            'positive': ratings['positive'],
            'negative': ratings['negative'],
            'neutral': ratings['neutral'],
            'satisfaction_rate': ratings['positive'] / len(feedback) if feedback else 0
        }


class QueryLogger:
    """Logs queries for analysis and improvement."""
    
    def __init__(self, log_path: Path = None):
        self.log_path = log_path or config.QUERY_LOG_PATH
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure log file exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()
    
    def log_query(
        self,
        query: str,
        expanded_query: Optional[str],
        num_results: int,
        top_score: float,
        response_length: int
    ) -> QueryLogEntry:
        """Log a query and its results."""
        entry = QueryLogEntry(
            timestamp=datetime.now().isoformat(),
            query=query,
            expanded_query=expanded_query,
            num_results=num_results,
            top_score=top_score,
            response_length=response_length
        )
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
        
        return entry
    
    def get_low_score_queries(self, threshold: float = 0.5) -> List[QueryLogEntry]:
        """Get queries with low retrieval scores."""
        entries = []
        if self.log_path.exists():
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = QueryLogEntry(**json.loads(line))
                        if entry.top_score < threshold:
                            entries.append(entry)
        return entries


class QueryExpander:
    """
    Expands unclear queries using LLM.
    Part of the self-learning/improvement mechanism.
    """
    
    EXPANSION_PROMPT = """You are helping to improve search queries for a database course search system.
The user asked: "{query}"

This query might be too short, ambiguous, or use informal language.
Please rewrite this as a clearer, more specific query about database concepts.
Keep it concise (one sentence) and focused on database terminology.

Only output the improved query, nothing else."""

    def __init__(self, client: GitHubModelsClient = None):
        self.client = client
        self._initialized = False
    
    def _ensure_client(self):
        """Lazily initialize client."""
        if self.client is None:
            try:
                self.client = GitHubModelsClient()
                self._initialized = True
            except ValueError:
                self._initialized = False
    
    def expand_query(self, query: str) -> Tuple[str, bool]:
        """
        Expand/improve a query using LLM.
        
        Args:
            query: Original query
            
        Returns:
            Tuple of (expanded_query, was_expanded)
        """
        # Short queries are candidates for expansion
        if len(query.split()) >= 5:
            return query, False
        
        self._ensure_client()
        
        if not self._initialized:
            return query, False
        
        try:
            expanded = self.client.generate(
                messages=[{"role": "user", "content": self.EXPANSION_PROMPT.format(query=query)}],
                temperature=0.3,
                max_tokens=100
            )
            
            # Clean up response
            expanded = expanded.strip().strip('"').strip("'")
            
            if expanded and expanded != query:
                print(f"🔄 Query expanded: '{query}' → '{expanded}'")
                return expanded, True
            
        except Exception as e:
            print(f"⚠️  Query expansion failed: {e}")
        
        return query, False


class AdaptiveRetriever:
    """
    Adaptive retrieval that adjusts parameters based on query characteristics.
    """
    
    def __init__(self):
        self.query_logger = QueryLogger()
        self.feedback_collector = FeedbackCollector()
    
    def get_adaptive_top_k(self, query: str, base_top_k: int = None) -> int:
        """
        Determine optimal top_k based on query complexity.
        
        Args:
            query: User query
            base_top_k: Base top_k value
            
        Returns:
            Adjusted top_k value
        """
        base_k = base_top_k or config.TOP_K
        
        # Longer queries might need more context
        word_count = len(query.split())
        
        if word_count <= 3:
            # Short query - might be ambiguous, get more results
            return min(base_k + 2, 10)
        elif word_count >= 10:
            # Long, specific query - fewer results needed
            return max(base_k - 1, 3)
        else:
            return base_k
    
    def should_expand_query(self, query: str, retrieval_score: float) -> bool:
        """
        Determine if query should be expanded.
        
        Args:
            query: User query
            retrieval_score: Score from initial retrieval
            
        Returns:
            True if query should be expanded
        """
        # Expand if retrieval score is low
        if retrieval_score < config.MIN_CONFIDENCE_THRESHOLD:
            return True
        
        # Expand if query is very short
        if len(query.split()) <= 2:
            return True
        
        return False


class SelfLearningRAG:
    """
    RAG system with self-learning capabilities.
    Wraps the main RAG pipeline with feedback and adaptation.
    """
    
    def __init__(self):
        from .generator import RAGPipeline
        
        self.pipeline = RAGPipeline()
        self.feedback_collector = FeedbackCollector()
        self.query_logger = QueryLogger()
        self.query_expander = QueryExpander()
        self.adaptive_retriever = AdaptiveRetriever()
        
        # Track current session
        self._current_result: Optional[GenerationResult] = None
    
    def initialize(self, force_rebuild: bool = False) -> bool:
        """Initialize the underlying pipeline."""
        return self.pipeline.initialize(force_rebuild=force_rebuild)
    
    def query(
        self,
        question: str,
        enable_expansion: bool = True,
        top_k: int = None
    ) -> Tuple[GenerationResult, Dict[str, Any]]:
        """
        Process a query with self-learning features.
        
        Args:
            question: User question
            enable_expansion: Whether to enable query expansion
            top_k: Override top_k
            
        Returns:
            Tuple of (GenerationResult, metadata_dict)
        """
        metadata = {
            'original_query': question,
            'expanded_query': None,
            'was_expanded': False,
            'adaptive_top_k': None
        }
        
        # Get adaptive top_k
        adaptive_k = self.adaptive_retriever.get_adaptive_top_k(question, top_k)
        metadata['adaptive_top_k'] = adaptive_k
        
        # Initial retrieval to check score
        initial_result = self.pipeline.retriever.retrieve(question, adaptive_k)
        
        # Determine if expansion needed
        query_to_use = question
        if enable_expansion and self.adaptive_retriever.should_expand_query(
            question, initial_result.top_score
        ):
            expanded, was_expanded = self.query_expander.expand_query(question)
            if was_expanded:
                query_to_use = expanded
                metadata['expanded_query'] = expanded
                metadata['was_expanded'] = True
        
        # Run full pipeline with (possibly expanded) query
        result = self.pipeline.query(query_to_use, adaptive_k)
        
        # Log query
        self.query_logger.log_query(
            query=question,
            expanded_query=metadata['expanded_query'],
            num_results=len(result.sources),
            top_score=result.retrieval_result.top_score if result.retrieval_result else 0,
            response_length=len(result.response)
        )
        
        # Store for feedback
        self._current_result = result
        
        return result, metadata
    
    def submit_feedback(self, rating: str) -> bool:
        """
        Submit feedback for the last query.
        
        Args:
            rating: 'positive', 'negative', or 'neutral'
            
        Returns:
            True if feedback was recorded
        """
        if self._current_result is None:
            print("⚠️  No query to provide feedback for")
            return False
        
        result = self._current_result
        
        self.feedback_collector.record_feedback(
            query=result.query,
            response=result.response,
            sources=result.sources,
            rating=rating,
            retrieval_score=result.retrieval_result.top_score if result.retrieval_result else 0,
            model=result.model
        )
        
        print(f"✅ Feedback recorded: {rating}")
        return True
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        feedback_stats = self.feedback_collector.get_feedback_stats()
        low_score_queries = self.query_logger.get_low_score_queries()
        
        return {
            'feedback': feedback_stats,
            'low_score_query_count': len(low_score_queries),
            'negative_feedback_queries': [
                e.query for e in self.feedback_collector.get_negative_feedback()
            ][:5]  # Last 5
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if system is ready."""
        return self.pipeline.is_ready


# For testing
if __name__ == "__main__":
    rag = SelfLearningRAG()
    
    if not rag.is_ready:
        print("Building index...")
        rag.initialize()
    
    # Test with short query (should trigger expansion)
    question = "ACID properties"
    print(f"\n🔍 Query: {question}")
    
    result, metadata = rag.query(question)
    
    print(f"\n📊 Metadata:")
    print(f"  • Was expanded: {metadata['was_expanded']}")
    print(f"  • Expanded query: {metadata['expanded_query']}")
    print(f"  • Adaptive top_k: {metadata['adaptive_top_k']}")
    
    print(f"\n📝 Response:\n{result.response[:500]}...")
    
    # Simulate feedback
    rag.submit_feedback('positive')
    
    # Show stats
    print(f"\n📈 Learning Stats:")
    stats = rag.get_learning_stats()
    print(json.dumps(stats, indent=2))

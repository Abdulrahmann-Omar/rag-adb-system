"""
Generator Module
Handles LLM integration with GitHub Models API for context-aware response generation.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI

from .config import config
from .retriever import RetrievalResult


@dataclass
class GenerationResult:
    """Structured result from generation."""
    query: str
    response: str
    sources: List[Dict[str, Any]]
    model: str
    retrieval_result: Optional[RetrievalResult] = None
    
    def format_response_with_sources(self) -> str:
        """Format response with source citations."""
        if not self.sources:
            return self.response
        
        source_text = "\n\n📚 **Sources:**\n"
        for source in self.sources:
            source_text += f"- {source['source']} (Page {source['page']})\n"
        
        return self.response + source_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'query': self.query,
            'response': self.response,
            'sources': self.sources,
            'model': self.model
        }


class GitHubModelsClient:
    """Client for GitHub Models API (OpenAI-compatible)."""
    
    def __init__(self, token: str = None, model: str = None):
        """
        Initialize GitHub Models client.
        
        Args:
            token: GitHub token (defaults to config)
            model: Model name (defaults to config)
        """
        self.token = token or config.GITHUB_TOKEN
        self.model = model or config.MODEL_NAME
        self.endpoint = config.GITHUB_MODELS_ENDPOINT
        
        if not self.token:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable."
            )
        
        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=self.token
        )
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Generation error: {str(e)}"
            print(f"❌ {error_msg}")
            return f"I encountered an error generating a response: {error_msg}"


class RAGGenerator:
    """
    RAG-based response generator.
    Combines retrieved context with LLM generation.
    """
    
    SYSTEM_PROMPT = """You are an expert teaching assistant for the Advanced Databases (ADB) course.
Your role is to help students understand database concepts clearly and accurately.

Guidelines:
1. Answer questions based ONLY on the provided lecture content
2. If the answer is not in the context, honestly say "I don't have information about this in the course materials"
3. Be educational and explain concepts clearly
4. Reference specific lectures when possible (e.g., "As discussed in Lecture 3...")
5. Use examples to illustrate complex concepts when helpful
6. Keep answers focused and relevant to the question"""

    CONTEXT_PROMPT_TEMPLATE = """Here is the relevant content from the ADB course lectures:

{context}

---

Based on the above lecture content, please answer the following question:

Question: {query}

Provide a clear, educational answer. If the information is not available in the provided context, say so."""

    def __init__(self, client: GitHubModelsClient = None):
        """
        Initialize the generator.
        
        Args:
            client: Optional pre-configured client
        """
        self.client = client
        self._initialized = False
    
    def _ensure_client(self):
        """Lazily initialize client."""
        if self.client is None:
            try:
                self.client = GitHubModelsClient()
                self._initialized = True
            except ValueError as e:
                print(f"⚠️  {e}")
                self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """Check if generator is available."""
        self._ensure_client()
        return self._initialized
    
    def generate(
        self,
        query: str,
        context: str,
        retrieval_result: RetrievalResult = None,
        temperature: float = 0.7
    ) -> GenerationResult:
        """
        Generate a response for a query given context.
        
        Args:
            query: User query
            context: Retrieved context string
            retrieval_result: Optional retrieval result for metadata
            temperature: Sampling temperature
            
        Returns:
            GenerationResult object
        """
        self._ensure_client()
        
        if not self._initialized:
            return GenerationResult(
                query=query,
                response="⚠️ LLM not available. Please set GITHUB_TOKEN in .env file.",
                sources=[],
                model="none",
                retrieval_result=retrieval_result
            )
        
        # Build prompt
        user_message = self.CONTEXT_PROMPT_TEMPLATE.format(
            context=context,
            query=query
        )
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # Generate response
        response = self.client.generate(
            messages=messages,
            temperature=temperature
        )
        
        # Extract sources from retrieval result
        sources = []
        if retrieval_result:
            sources = retrieval_result.get_sources()
        
        return GenerationResult(
            query=query,
            response=response,
            sources=sources,
            model=self.client.model,
            retrieval_result=retrieval_result
        )
    
    def generate_with_fallback(
        self,
        query: str,
        context: str,
        retrieval_result: RetrievalResult = None
    ) -> GenerationResult:
        """
        Generate with fallback for when retrieval has no results.
        
        Args:
            query: User query
            context: Retrieved context string
            retrieval_result: Retrieval result
            
        Returns:
            GenerationResult object
        """
        # Check if retrieval found anything
        if retrieval_result and not retrieval_result.has_results:
            return GenerationResult(
                query=query,
                response="I couldn't find any relevant information in the course materials for this question. "
                         "This topic might not be covered in the available lectures, or you could try rephrasing your question.",
                sources=[],
                model="none",
                retrieval_result=retrieval_result
            )
        
        # Check confidence threshold
        if retrieval_result and retrieval_result.top_score < config.MIN_CONFIDENCE_THRESHOLD:
            # Low confidence - include disclaimer
            result = self.generate(query, context, retrieval_result)
            result.response = (
                "⚠️ *Note: The retrieved content may not be highly relevant to your question.*\n\n" +
                result.response
            )
            return result
        
        return self.generate(query, context, retrieval_result)


class RAGPipeline:
    """
    Complete RAG pipeline combining retrieval and generation.
    """
    
    def __init__(self):
        from .retriever import Retriever
        
        self.retriever = Retriever(auto_load=True)
        self.generator = RAGGenerator()
    
    def initialize(self, force_rebuild: bool = False) -> bool:
        """
        Initialize the pipeline (build index if needed).
        
        Args:
            force_rebuild: Force rebuild of index
            
        Returns:
            True if successful
        """
        return self.retriever.build_index(force_rebuild=force_rebuild)
    
    def query(
        self,
        question: str,
        top_k: int = None
    ) -> GenerationResult:
        """
        Process a query through the full RAG pipeline.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            
        Returns:
            GenerationResult with response and sources
        """
        # Retrieve relevant documents
        context, retrieval_result = self.retriever.retrieve_with_context(
            question, 
            top_k
        )
        
        # Generate response
        result = self.generator.generate_with_fallback(
            query=question,
            context=context,
            retrieval_result=retrieval_result
        )
        
        return result
    
    @property
    def is_ready(self) -> bool:
        """Check if pipeline is ready for queries."""
        return self.retriever.is_initialized


# For testing
if __name__ == "__main__":
    pipeline = RAGPipeline()
    
    if not pipeline.is_ready:
        print("Building index...")
        pipeline.initialize()
    
    # Test query
    question = "What are the ACID properties in databases?"
    print(f"\n🔍 Query: {question}\n")
    
    result = pipeline.query(question)
    
    print("📝 Response:")
    print("-" * 40)
    print(result.response)
    print("-" * 40)
    
    print("\n📚 Sources:")
    for source in result.sources:
        print(f"  - {source['source']} (Page {source['page']}) - Score: {source['score']}")

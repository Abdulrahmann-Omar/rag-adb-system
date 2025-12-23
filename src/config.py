"""
Configuration management for RAG system.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
(DATA_DIR / "processed").mkdir(exist_ok=True)
(DATA_DIR / "vector_store").mkdir(exist_ok=True)


class Config:
    """Central configuration class for the RAG system."""
    
    # GitHub Models API
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    GITHUB_MODELS_ENDPOINT: str = "https://models.inference.ai.azure.com"
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", 
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 output dimension
    
    # Document Processing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Retrieval Configuration
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SEMANTIC_WEIGHT: float = 0.7
    KEYWORD_WEIGHT: float = 0.3
    
    # Paths
    LECTURES_PATH: Path = Path(os.getenv("LECTURES_PATH", str(BASE_DIR / "Lectures")))
    VECTOR_STORE_PATH: Path = DATA_DIR / "vector_store"
    PROCESSED_PATH: Path = DATA_DIR / "processed"
    
    # Logging
    QUERY_LOG_PATH: Path = LOGS_DIR / "queries.jsonl"
    FEEDBACK_LOG_PATH: Path = LOGS_DIR / "feedback.jsonl"
    
    # Self-Learning
    MIN_CONFIDENCE_THRESHOLD: float = 0.5
    MAX_QUERY_EXPANSIONS: int = 2
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.GITHUB_TOKEN:
            print("⚠️  Warning: GITHUB_TOKEN not set. LLM generation will not work.")
            return False
        if not cls.LECTURES_PATH.exists():
            print(f"⚠️  Warning: Lectures path does not exist: {cls.LECTURES_PATH}")
            return False
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration for debugging."""
        print("\n📋 RAG System Configuration:")
        print(f"  • Model: {cls.MODEL_NAME}")
        print(f"  • Embedding: {cls.EMBEDDING_MODEL}")
        print(f"  • Chunk Size: {cls.CHUNK_SIZE} (overlap: {cls.CHUNK_OVERLAP})")
        print(f"  • Top-K: {cls.TOP_K}")
        print(f"  • Lectures Path: {cls.LECTURES_PATH}")
        print(f"  • Vector Store: {cls.VECTOR_STORE_PATH}")
        print()


# Create singleton instance
config = Config()

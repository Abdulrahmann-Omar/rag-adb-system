"""
Utility functions for the RAG system.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any


def setup_project_path():
    """Add project root to path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def format_sources_markdown(sources: List[Dict[str, Any]]) -> str:
    """
    Format sources as markdown for display.
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Markdown formatted string
    """
    if not sources:
        return "*No sources found*"
    
    lines = []
    for source in sources:
        lines.append(
            f"**[{source['rank']}]** {source['source']} (Page {source['page']}) "
            f"- Score: {source['score']:.3f}"
        )
        lines.append(f"> {source['preview'][:150]}...")
        lines.append("")
    
    return "\n".join(lines)


def format_response_html(response: str, sources: List[Dict[str, Any]]) -> str:
    """
    Format response and sources as HTML.
    
    Args:
        response: Generated response text
        sources: List of source dictionaries
        
    Returns:
        HTML formatted string
    """
    html = f"<div class='response'>{response}</div>"
    
    if sources:
        html += "<div class='sources'><h4>📚 Sources:</h4><ul>"
        for source in sources:
            html += (
                f"<li><strong>{source['source']}</strong> "
                f"(Page {source['page']}) - Score: {source['score']:.3f}</li>"
            )
        html += "</ul></div>"
    
    return html


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_project_info() -> Dict[str, Any]:
    """Get project information."""
    from . import __version__
    from .config import config
    
    return {
        'version': __version__,
        'model': config.MODEL_NAME,
        'embedding_model': config.EMBEDDING_MODEL,
        'chunk_size': config.CHUNK_SIZE,
        'top_k': config.TOP_K
    }


def print_banner():
    """Print project banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║           📚 ADB Course RAG System                        ║
║   Retrieval-Augmented Generation for Database Learning   ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_environment() -> Dict[str, bool]:
    """
    Validate that all required environment variables and dependencies are set.
    
    Returns:
        Dictionary of validation results
    """
    from .config import config
    
    results = {
        'github_token': bool(config.GITHUB_TOKEN),
        'lectures_path': config.LECTURES_PATH.exists(),
        'vector_store_path': config.VECTOR_STORE_PATH.exists()
    }
    
    # Check for required packages
    required_packages = [
        'pdfplumber',
        'sentence_transformers', 
        'faiss',
        'rank_bm25',
        'gradio',
        'openai'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            results[f'package_{package}'] = True
        except ImportError:
            results[f'package_{package}'] = False
    
    return results

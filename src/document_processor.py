"""
Document Processing Module
Handles PDF extraction, text chunking, and metadata management.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from .config import config


@dataclass
class Document:
    """Represents a document chunk with metadata."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        source = self.metadata.get('source', 'unknown')
        page = self.metadata.get('page', '?')
        return f"Document(source={source}, page={page}, len={len(self.content)})"


class PDFExtractor:
    """Extracts text from PDF files with page-level tracking."""
    
    @staticmethod
    def extract_from_pdf(pdf_path: Path) -> List[Tuple[str, int]]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of (text, page_number) tuples
        """
        pages = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    if text.strip():  # Only include non-empty pages
                        # Clean up the text
                        text = PDFExtractor._clean_text(text)
                        pages.append((text, i))
        except Exception as e:
            print(f"❌ Error extracting {pdf_path.name}: {e}")
        return pages
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)


class DocumentChunker:
    """Splits documents into chunks with overlap."""
    
    def __init__(
        self, 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """
        Split text into chunks while preserving metadata.
        
        Args:
            text: The text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of Document objects
        """
        chunks = self.splitter.split_text(text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                'chunk_index': i,
                'chunk_total': len(chunks)
            }
            documents.append(Document(content=chunk, metadata=chunk_metadata))
        
        return documents


class DocumentProcessor:
    """Main document processing pipeline."""
    
    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = DocumentChunker()
    
    def process_pdf(self, pdf_path: Path) -> List[Document]:
        """
        Process a single PDF file into document chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Document objects
        """
        documents = []
        pages = self.extractor.extract_from_pdf(pdf_path)
        
        for text, page_num in pages:
            metadata = {
                'source': pdf_path.name,
                'source_path': str(pdf_path),
                'page': page_num
            }
            chunks = self.chunker.chunk_text(text, metadata)
            documents.extend(chunks)
        
        return documents
    
    def process_directory(
        self, 
        directory: Path = None,
        file_pattern: str = "*.pdf"
    ) -> List[Document]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory: Directory containing PDFs (defaults to config)
            file_pattern: Glob pattern for files
            
        Returns:
            List of all Document objects
        """
        directory = directory or config.LECTURES_PATH
        pdf_files = sorted(directory.glob(file_pattern))
        
        if not pdf_files:
            print(f"⚠️  No PDF files found in {directory}")
            return []
        
        print(f"\n📚 Processing {len(pdf_files)} PDF files from {directory}")
        
        all_documents = []
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            docs = self.process_pdf(pdf_path)
            all_documents.extend(docs)
            print(f"  ✓ {pdf_path.name}: {len(docs)} chunks")
        
        print(f"\n✅ Total: {len(all_documents)} document chunks created")
        return all_documents
    
    def get_statistics(self, documents: List[Document]) -> Dict[str, Any]:
        """Get statistics about processed documents."""
        if not documents:
            return {}
        
        sources = {}
        total_chars = 0
        
        for doc in documents:
            source = doc.metadata.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            total_chars += len(doc.content)
        
        return {
            'total_chunks': len(documents),
            'total_characters': total_chars,
            'avg_chunk_size': total_chars // len(documents),
            'sources': sources,
            'num_sources': len(sources)
        }


def process_all_pdfs(directory: str = None) -> List[Document]:
    """
    Convenience function to process all PDFs.
    
    Args:
        directory: Optional directory path
        
    Returns:
        List of Document objects
    """
    processor = DocumentProcessor()
    dir_path = Path(directory) if directory else None
    return processor.process_directory(dir_path)


# For testing
if __name__ == "__main__":
    processor = DocumentProcessor()
    docs = processor.process_directory()
    stats = processor.get_statistics(docs)
    
    print("\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  • {key}: {value}")

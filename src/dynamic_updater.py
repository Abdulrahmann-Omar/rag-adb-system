"""
Dynamic Document Update System
Implements semantic conflict resolution with REPLACE/MERGE/INSERT logic.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

from .config import config
from .document_processor import Document, PDFExtractor, DocumentChunker, DocumentProcessor


class ConflictType(Enum):
    """Types of conflicts detected during document update."""
    REPLACEMENT = "replacement"  # >0.90 similarity
    MERGE = "merge"              # 0.70-0.89 similarity
    INSERT = "insert"            # <0.70 similarity
    SKIP = "skip"                # Duplicate or low quality


@dataclass
class ValidationResult:
    """Result of document validation."""
    is_valid: bool
    filename: str
    file_size: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DocumentMetadata:
    """Metadata for an ingested document."""
    filename: str
    upload_timestamp: str
    file_size: int
    page_count: int
    chunk_count: int
    content_hash: str
    authority_score: float = 1.0  # Default authority


@dataclass
class EnrichedChunk:
    """A document chunk with enrichment data."""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    entities: List[str] = field(default_factory=list)
    comprehensiveness_score: float = 0.0
    content_hash: str = ""


@dataclass
class ConflictResult:
    """Result of conflict detection."""
    conflict_type: ConflictType
    new_chunk: EnrichedChunk
    similar_chunks: List[Tuple[int, float]]  # (chunk_id, similarity_score)
    entity_overlap: float = 0.0


@dataclass
class Decision:
    """Decision made by the decision engine."""
    action: ConflictType
    new_chunk: EnrichedChunk
    target_chunk_ids: List[int]
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Stage 1: Ingestion & Preprocessing
# =============================================================================

class DocumentIngester:
    """
    Stage 1: Validates and preprocesses uploaded documents.
    
    Responsibilities:
    - File type and size validation
    - Corruption detection
    - Metadata extraction
    - Quality gates for chunks
    """
    
    # Configuration
    MAX_FILE_SIZE_MB = 50
    MIN_CHUNK_WORDS = 50
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.chunker = DocumentChunker(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        self._processed_hashes: set = set()
        self._load_hash_cache()
    
    def _load_hash_cache(self):
        """Load previously processed document hashes."""
        cache_path = config.VECTOR_STORE_PATH / "document_hashes.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    self._processed_hashes = set(json.load(f))
            except Exception:
                self._processed_hashes = set()
    
    def _save_hash_cache(self):
        """Save processed document hashes."""
        cache_path = config.VECTOR_STORE_PATH / "document_hashes.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(list(self._processed_hashes), f)
    
    def validate(self, file_path: Path) -> ValidationResult:
        """
        Validate an uploaded file.
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []
        
        # Check file exists
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                filename=file_path.name,
                file_size=0,
                errors=["File does not exist"]
            )
        
        # Check extension
        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file type: {file_path.suffix}. Only PDF files are allowed.")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            errors.append(f"File too large: {file_size / (1024*1024):.1f}MB. Maximum is {self.MAX_FILE_SIZE_MB}MB.")
        
        if file_size == 0:
            errors.append("File is empty.")
        
        # Check for corruption by attempting to read
        if not errors:
            try:
                pages = self.pdf_extractor.extract_from_pdf(file_path)
                total_text = ''.join([text for text, _ in pages])
                if not total_text or len(total_text.strip()) < 100:
                    warnings.append("Document contains very little extractable text.")
            except Exception as e:
                errors.append(f"Failed to read PDF: {str(e)}")
        
        # Check for duplicates
        if not errors:
            content_hash = self._compute_hash(file_path)
            if content_hash in self._processed_hashes:
                warnings.append("This document appears to have been processed before.")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            filename=file_path.name,
            file_size=file_size,
            errors=errors,
            warnings=warnings
        )
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def extract_metadata(self, file_path: Path, chunks: List[Document]) -> DocumentMetadata:
        """
        Extract metadata from a document.
        
        Args:
            file_path: Path to the document
            chunks: Processed chunks from the document
            
        Returns:
            DocumentMetadata object
        """
        # Get page count from chunks
        pages = set()
        for chunk in chunks:
            if 'page' in chunk.metadata:
                pages.add(chunk.metadata['page'])
        
        return DocumentMetadata(
            filename=file_path.name,
            upload_timestamp=datetime.now().isoformat(),
            file_size=file_path.stat().st_size,
            page_count=len(pages) or 1,
            chunk_count=len(chunks),
            content_hash=self._compute_hash(file_path)
        )
    
    def apply_quality_gates(self, chunks: List[Document]) -> Tuple[List[Document], List[str]]:
        """
        Apply quality gates to filter out low-quality chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Tuple of (filtered_chunks, rejection_reasons)
        """
        filtered = []
        rejections = []
        
        for i, chunk in enumerate(chunks):
            word_count = len(chunk.content.split())
            
            # Minimum word count
            if word_count < self.MIN_CHUNK_WORDS:
                rejections.append(f"Chunk {i+1}: Too short ({word_count} words < {self.MIN_CHUNK_WORDS})")
                continue
            
            # Check for mostly whitespace/special characters
            alpha_ratio = sum(c.isalpha() for c in chunk.content) / max(len(chunk.content), 1)
            if alpha_ratio < 0.5:
                rejections.append(f"Chunk {i+1}: Low text quality (alpha ratio: {alpha_ratio:.2f})")
                continue
            
            filtered.append(chunk)
        
        return filtered, rejections
    
    def ingest(
        self, 
        file_path: Path,
        authority_score: float = 1.0
    ) -> Tuple[List[Document], DocumentMetadata, List[str]]:
        """
        Full ingestion pipeline for a document.
        
        Args:
            file_path: Path to the PDF file
            authority_score: Authority weight for this document (default 1.0)
            
        Returns:
            Tuple of (chunks, metadata, warnings)
        """
        warnings = []
        
        # Validate
        validation = self.validate(file_path)
        if not validation.is_valid:
            raise ValueError(f"Validation failed: {'; '.join(validation.errors)}")
        warnings.extend(validation.warnings)
        
        # Extract text from PDF (page by page)
        print(f"📄 Extracting text from {file_path.name}...")
        pages = self.pdf_extractor.extract_from_pdf(file_path)
        
        if not pages:
            raise ValueError(f"Could not extract any text from {file_path.name}")
        
        # Chunk each page
        print(f"✂️  Chunking document...")
        all_chunks = []
        for text, page_num in pages:
            metadata = {
                'source': file_path.name,
                'page': page_num
            }
            page_chunks = self.chunker.chunk_text(text, metadata)
            all_chunks.extend(page_chunks)
        
        # Apply quality gates
        all_chunks, rejections = self.apply_quality_gates(all_chunks)
        if rejections:
            warnings.extend(rejections)
            print(f"⚠️  Filtered out {len(rejections)} low-quality chunks")
        
        # Extract metadata
        doc_metadata = self.extract_metadata(file_path, all_chunks)
        doc_metadata.authority_score = authority_score
        
        # Update hash cache
        self._processed_hashes.add(doc_metadata.content_hash)
        self._save_hash_cache()
        
        print(f"✅ Ingested {len(all_chunks)} chunks from {file_path.name}")
        
        return all_chunks, doc_metadata, warnings


# =============================================================================
# Stage 2: Embedding & Enrichment
# =============================================================================

class EmbeddingEnricher:
    """
    Stage 2: Generates enriched embeddings and extracts entities.
    
    Responsibilities:
    - Generate context-enriched embeddings
    - Extract entities using spaCy
    - Score chunk comprehensiveness
    """
    
    def __init__(self):
        from .vector_store import EmbeddingManager
        self.embedding_manager = EmbeddingManager()
        self._nlp = None  # Lazy load spaCy
    
    def _get_nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
                self._nlp = None
        return self._nlp
    
    def generate_embeddings(
        self, 
        chunks: List[Document],
        parent_summary: str = ""
    ) -> np.ndarray:
        """
        Generate context-enriched embeddings for chunks.
        
        Args:
            chunks: List of document chunks
            parent_summary: Optional summary of parent document for context
            
        Returns:
            numpy array of embeddings
        """
        # Create enriched text for embedding
        texts = []
        for chunk in chunks:
            if parent_summary:
                # Context-enriched: combine chunk with parent summary
                enriched = f"{parent_summary}\n\n{chunk.content}"
            else:
                enriched = chunk.content
            texts.append(enriched)
        
        return self.embedding_manager.embed_texts(texts, show_progress=True)
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities from text using spaCy.
        
        Args:
            text: Input text
            
        Returns:
            List of entity strings
        """
        nlp = self._get_nlp()
        if nlp is None:
            return []
        
        doc = nlp(text[:10000])  # Limit for performance
        
        # Extract relevant entity types
        relevant_types = {'ORG', 'PRODUCT', 'WORK_OF_ART', 'LAW', 'EVENT', 'NORP'}
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in relevant_types:
                entities.append(ent.text.lower())
        
        # Also extract noun chunks as concepts
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                entities.append(chunk.text.lower())
        
        return list(set(entities))
    
    def score_comprehensiveness(self, chunk: Document) -> float:
        """
        Score chunk comprehensiveness based on multiple factors.
        
        Factors:
        - Length (word count)
        - Entity density
        - Structural indicators (headers, lists, etc.)
        
        Args:
            chunk: Document chunk
            
        Returns:
            Comprehensiveness score (0-1)
        """
        content = chunk.content
        
        # Factor 1: Length (normalize to 0-1, cap at 500 words)
        word_count = len(content.split())
        length_score = min(word_count / 500, 1.0)
        
        # Factor 2: Entity density
        entities = self.extract_entities(content)
        entity_density = len(entities) / max(word_count, 1) * 100
        entity_score = min(entity_density / 5, 1.0)  # Normalize
        
        # Factor 3: Structural indicators
        structural_indicators = [
            content.count('\n'),           # Line breaks
            content.count(':'),            # Definitions
            content.count('•') + content.count('-'),  # Lists
            len([w for w in content.split() if w.isupper() and len(w) > 2]),  # Acronyms
        ]
        structural_score = min(sum(structural_indicators) / 20, 1.0)
        
        # Weighted combination
        final_score = (
            0.4 * length_score +
            0.3 * entity_score +
            0.3 * structural_score
        )
        
        return round(final_score, 3)
    
    def enrich_chunks(
        self, 
        chunks: List[Document],
        parent_summary: str = ""
    ) -> List[EnrichedChunk]:
        """
        Full enrichment pipeline for chunks.
        
        Args:
            chunks: List of document chunks
            parent_summary: Optional parent document summary
            
        Returns:
            List of EnrichedChunk objects
        """
        print("🧠 Generating embeddings...")
        embeddings = self.generate_embeddings(chunks, parent_summary)
        
        enriched = []
        print("🔍 Extracting entities and scoring...")
        for i, chunk in enumerate(chunks):
            entities = self.extract_entities(chunk.content)
            score = self.score_comprehensiveness(chunk)
            content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:16]
            
            enriched.append(EnrichedChunk(
                content=chunk.content,
                metadata=chunk.metadata,
                embedding=embeddings[i],
                entities=entities,
                comprehensiveness_score=score,
                content_hash=content_hash
            ))
        
        print(f"✅ Enriched {len(enriched)} chunks")
        return enriched


# =============================================================================
# Conflict Thresholds Configuration
# =============================================================================

CONFLICT_THRESHOLDS = {
    'replacement_min': 0.90,   # >0.90 = REPLACEMENT candidate
    'merge_min': 0.70,         # 0.70-0.89 = MERGE candidate
    'relationship_min': 0.50,  # 0.50-0.69 = Relationship discovery
    'entity_overlap_merge': 0.80  # High entity overlap with low similarity = MERGE
}

COMPREHENSIVENESS_BOOST = 0.15  # Required improvement for replacement
AGE_THRESHOLD_DAYS = 180  # Auto-replace if older than this


# =============================================================================
# Stage 3: Conflict Detection
# =============================================================================

class ConflictDetector:
    """
    Stage 3: Detects conflicts between new and existing content.
    
    Responsibilities:
    - Similarity search against existing chunks
    - Three-tier classification (REPLACE/MERGE/INSERT)
    - Entity overlap detection for hidden conflicts
    """
    
    def __init__(self, vector_store):
        """
        Args:
            vector_store: HybridVectorStore instance with existing documents
        """
        self.vector_store = vector_store
        self.thresholds = CONFLICT_THRESHOLDS
    
    def find_similar(
        self, 
        embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Tuple[int, float, 'Document']]:
        """
        Find similar chunks in the existing vector store.
        
        Args:
            embedding: Query embedding
            top_k: Number of similar chunks to retrieve
            
        Returns:
            List of (chunk_index, similarity_score, document) tuples
        """
        import faiss
        
        # Normalize embedding for cosine similarity
        query = embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query)
        
        # Search FAISS index
        faiss_store = self.vector_store.faiss_store
        if faiss_store.index is None:
            return []
        
        scores, indices = faiss_store.index.search(query, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(faiss_store.documents):
                results.append((int(idx), float(score), faiss_store.documents[idx]))
        
        return results
    
    def calculate_entity_overlap(
        self, 
        entities1: List[str], 
        entities2: List[str]
    ) -> float:
        """
        Calculate Jaccard overlap between two entity sets.
        
        Returns:
            Overlap ratio (0-1)
        """
        if not entities1 or not entities2:
            return 0.0
        
        set1 = set(e.lower() for e in entities1)
        set2 = set(e.lower() for e in entities2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def classify_conflict(
        self, 
        similarity: float, 
        entity_overlap: float = 0.0
    ) -> ConflictType:
        """
        Classify conflict type based on similarity and entity overlap.
        
        Args:
            similarity: Cosine similarity score (0-1)
            entity_overlap: Entity overlap ratio (0-1)
            
        Returns:
            ConflictType enum value
        """
        # High similarity = REPLACEMENT candidate
        if similarity >= self.thresholds['replacement_min']:
            return ConflictType.REPLACEMENT
        
        # Medium similarity = MERGE candidate
        if similarity >= self.thresholds['merge_min']:
            return ConflictType.MERGE
        
        # Hidden conflict: Low similarity but high entity overlap
        if (similarity < self.thresholds['merge_min'] and 
            entity_overlap >= self.thresholds['entity_overlap_merge']):
            return ConflictType.MERGE
        
        # Low similarity with some relationship potential
        if similarity >= self.thresholds['relationship_min']:
            return ConflictType.INSERT  # Will discover relationships
        
        # Completely new content
        return ConflictType.INSERT
    
    def detect(self, enriched_chunk: EnrichedChunk) -> ConflictResult:
        """
        Detect conflicts for a new enriched chunk.
        
        Args:
            enriched_chunk: The new chunk to check
            
        Returns:
            ConflictResult with classification and similar chunks
        """
        # Find similar chunks
        similar = self.find_similar(enriched_chunk.embedding, top_k=5)
        
        if not similar:
            return ConflictResult(
                conflict_type=ConflictType.INSERT,
                new_chunk=enriched_chunk,
                similar_chunks=[],
                entity_overlap=0.0
            )
        
        # Get top match
        top_idx, top_score, top_doc = similar[0]
        
        # Calculate entity overlap with top match
        # Extract entities from existing doc if not cached
        enricher = EmbeddingEnricher()
        existing_entities = enricher.extract_entities(top_doc.content)
        entity_overlap = self.calculate_entity_overlap(
            enriched_chunk.entities, 
            existing_entities
        )
        
        # Classify conflict
        conflict_type = self.classify_conflict(top_score, entity_overlap)
        
        return ConflictResult(
            conflict_type=conflict_type,
            new_chunk=enriched_chunk,
            similar_chunks=[(idx, score) for idx, score, _ in similar],
            entity_overlap=entity_overlap
        )


# =============================================================================
# Stage 4: Decision Engine
# =============================================================================

class DecisionEngine:
    """
    Stage 4: Makes decisions based on conflict type.
    
    Responsibilities:
    - Evaluate REPLACEMENT conditions (comprehensiveness, age)
    - Evaluate MERGE conditions (unique facts)
    - Discover relationships for INSERT
    """
    
    def __init__(self, vector_store, llm_client=None):
        """
        Args:
            vector_store: HybridVectorStore instance
            llm_client: Optional LLM client for merge/relationship analysis
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.enricher = EmbeddingEnricher()
    
    def evaluate_replacement(
        self, 
        new_chunk: EnrichedChunk, 
        old_chunk_idx: int,
        old_score: float
    ) -> Decision:
        """
        Evaluate if REPLACEMENT should be executed.
        
        Conditions:
        - new_comprehensiveness > old + 0.15
        - OR: old chunk is older than 180 days
        
        Otherwise: downgrade to MERGE
        """
        old_doc = self.vector_store.faiss_store.documents[old_chunk_idx]
        old_comprehensiveness = self.enricher.score_comprehensiveness(old_doc)
        
        score_improvement = new_chunk.comprehensiveness_score - old_comprehensiveness
        
        # Check comprehensiveness improvement
        if score_improvement >= COMPREHENSIVENESS_BOOST:
            return Decision(
                action=ConflictType.REPLACEMENT,
                new_chunk=new_chunk,
                target_chunk_ids=[old_chunk_idx],
                reason=f"New chunk more comprehensive (improvement: {score_improvement:.2f})",
                metadata={
                    'old_score': old_comprehensiveness,
                    'new_score': new_chunk.comprehensiveness_score,
                    'improvement': score_improvement
                }
            )
        
        # Check age (would need timestamp in metadata - fallback to MERGE)
        # For now, downgrade to MERGE if not significantly better
        return Decision(
            action=ConflictType.MERGE,
            new_chunk=new_chunk,
            target_chunk_ids=[old_chunk_idx],
            reason=f"Insufficient improvement ({score_improvement:.2f} < {COMPREHENSIVENESS_BOOST}), downgrading to MERGE",
            metadata={
                'downgraded_from': 'REPLACEMENT',
                'old_score': old_comprehensiveness,
                'new_score': new_chunk.comprehensiveness_score
            }
        )
    
    def evaluate_merge(
        self, 
        new_chunk: EnrichedChunk, 
        old_chunk_idx: int
    ) -> Decision:
        """
        Evaluate if MERGE should be executed.
        
        Conditions:
        - Both chunks have ≥2 unique facts each
        - Merged result would be <250 words
        """
        old_doc = self.vector_store.faiss_store.documents[old_chunk_idx]
        
        # Simple heuristic: count unique entities as proxy for unique facts
        old_entities = set(self.enricher.extract_entities(old_doc.content))
        new_entities = set(new_chunk.entities)
        
        unique_old = len(old_entities - new_entities)
        unique_new = len(new_entities - old_entities)
        
        # Check if both have unique content
        if unique_old >= 2 and unique_new >= 2:
            # Check combined length
            combined_words = len(old_doc.content.split()) + len(new_chunk.content.split())
            
            return Decision(
                action=ConflictType.MERGE,
                new_chunk=new_chunk,
                target_chunk_ids=[old_chunk_idx],
                reason=f"Both chunks have unique content (old: {unique_old}, new: {unique_new} unique entities)",
                metadata={
                    'unique_old_entities': unique_old,
                    'unique_new_entities': unique_new,
                    'combined_word_count': combined_words,
                    'needs_split': combined_words > 250
                }
            )
        
        # Not enough unique content - skip merge, just insert
        return Decision(
            action=ConflictType.INSERT,
            new_chunk=new_chunk,
            target_chunk_ids=[],
            reason=f"Insufficient unique content for merge (old: {unique_old}, new: {unique_new})",
            metadata={'downgraded_from': 'MERGE'}
        )
    
    def discover_relationships(
        self, 
        new_chunk: EnrichedChunk,
        similar_chunks: List[Tuple[int, float]]
    ) -> Decision:
        """
        Discover relationships for INSERT action.
        
        Edge types: extends, supports, contradicts, prerequisite_of
        """
        relationships = []
        
        for chunk_idx, similarity in similar_chunks:
            if similarity >= CONFLICT_THRESHOLDS['relationship_min']:
                # Simple heuristic for relationship type based on similarity
                if similarity >= 0.60:
                    rel_type = "extends"  # Highly related content
                elif similarity >= 0.55:
                    rel_type = "supports"  # Supporting content
                else:
                    rel_type = "related"  # General relationship
                
                relationships.append({
                    'target_id': chunk_idx,
                    'type': rel_type,
                    'similarity': similarity
                })
        
        return Decision(
            action=ConflictType.INSERT,
            new_chunk=new_chunk,
            target_chunk_ids=[r['target_id'] for r in relationships],
            reason=f"New content with {len(relationships)} discovered relationships",
            metadata={'relationships': relationships}
        )
    
    def decide(self, conflict_result: ConflictResult) -> Decision:
        """
        Make a decision based on conflict detection result.
        
        Args:
            conflict_result: Result from ConflictDetector
            
        Returns:
            Decision object with action and metadata
        """
        if conflict_result.conflict_type == ConflictType.REPLACEMENT:
            if conflict_result.similar_chunks:
                top_idx, top_score = conflict_result.similar_chunks[0]
                return self.evaluate_replacement(
                    conflict_result.new_chunk, 
                    top_idx, 
                    top_score
                )
        
        elif conflict_result.conflict_type == ConflictType.MERGE:
            if conflict_result.similar_chunks:
                top_idx, _ = conflict_result.similar_chunks[0]
                return self.evaluate_merge(conflict_result.new_chunk, top_idx)
        
        # Default: INSERT with relationship discovery
        return self.discover_relationships(
            conflict_result.new_chunk,
            conflict_result.similar_chunks
        )


# =============================================================================
# Stage 5: Update Executor
# =============================================================================

class UpdateExecutor:
    """
    Stage 5: Executes the decided action.
    
    Responsibilities:
    - Execute REPLACEMENT (transfer edges, version old)
    - Execute MERGE (LLM synthesis, new embedding)
    - Execute INSERT (add with typed edges)
    """
    
    def __init__(self, vector_store, llm_client=None):
        """
        Args:
            vector_store: HybridVectorStore instance
            llm_client: Optional LLM client for merge synthesis
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        self._version_history: List[Dict] = []
    
    def execute_replacement(self, decision: Decision) -> Dict[str, Any]:
        """
        Execute REPLACEMENT action.
        
        - Remove old chunk from index
        - Add new chunk
        - Maintain version history
        """
        from .document_processor import Document
        
        result = {
            'action': 'REPLACEMENT',
            'success': False,
            'old_ids': decision.target_chunk_ids,
            'details': {}
        }
        
        try:
            # Create Document from EnrichedChunk
            new_doc = Document(
                content=decision.new_chunk.content,
                metadata=decision.new_chunk.metadata
            )
            
            # Record version history before removal
            for old_idx in decision.target_chunk_ids:
                old_doc = self.vector_store.faiss_store.documents[old_idx]
                self._version_history.append({
                    'action': 'superseded',
                    'old_content_hash': hash(old_doc.content),
                    'new_content_hash': decision.new_chunk.content_hash,
                    'timestamp': datetime.now().isoformat(),
                    'reason': decision.reason
                })
            
            # Remove old chunks
            self.vector_store.faiss_store.remove_documents(
                decision.target_chunk_ids, 
                save_after=False
            )
            
            # Add new chunk
            self.vector_store.faiss_store.add_documents([new_doc], save_after=True)
            
            result['success'] = True
            result['details'] = {
                'removed_count': len(decision.target_chunk_ids),
                'reason': decision.reason
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def execute_merge(self, decision: Decision) -> Dict[str, Any]:
        """
        Execute MERGE action.
        
        - Combine content from both chunks
        - Generate new embedding
        - Create merged_from links
        """
        from .document_processor import Document
        
        result = {
            'action': 'MERGE',
            'success': False,
            'merged_ids': decision.target_chunk_ids,
            'details': {}
        }
        
        try:
            # Get old chunk content
            old_contents = []
            for idx in decision.target_chunk_ids:
                old_doc = self.vector_store.faiss_store.documents[idx]
                old_contents.append(old_doc.content)
            
            # Simple merge: combine with separator
            # In production, would use LLM for intelligent synthesis
            merged_content = decision.new_chunk.content
            for old_content in old_contents:
                # Find unique sentences in old content
                old_sentences = set(old_content.split('. '))
                new_sentences = set(decision.new_chunk.content.split('. '))
                unique_old = old_sentences - new_sentences
                
                if unique_old:
                    merged_content += "\n\n" + '. '.join(unique_old)
            
            # Truncate if too long (250 words max per plan)
            words = merged_content.split()
            if len(words) > 250:
                merged_content = ' '.join(words[:250]) + '...'
                result['details']['truncated'] = True
            
            # Create merged document
            merged_doc = Document(
                content=merged_content,
                metadata={
                    **decision.new_chunk.metadata,
                    'merged_from': decision.target_chunk_ids
                }
            )
            
            # Remove old chunks
            self.vector_store.faiss_store.remove_documents(
                decision.target_chunk_ids, 
                save_after=False
            )
            
            # Add merged chunk
            self.vector_store.faiss_store.add_documents([merged_doc], save_after=True)
            
            result['success'] = True
            result['details']['merged_word_count'] = len(merged_content.split())
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def execute_insert(self, decision: Decision) -> Dict[str, Any]:
        """
        Execute INSERT action.
        
        - Add new chunk to vector store
        - Record relationships in metadata
        """
        from .document_processor import Document
        
        result = {
            'action': 'INSERT',
            'success': False,
            'relationships': decision.metadata.get('relationships', []),
            'details': {}
        }
        
        try:
            # Create document with relationship metadata
            new_doc = Document(
                content=decision.new_chunk.content,
                metadata={
                    **decision.new_chunk.metadata,
                    'relationships': decision.metadata.get('relationships', [])
                }
            )
            
            # Add to vector store
            added_count = self.vector_store.faiss_store.add_documents(
                [new_doc], 
                save_after=True
            )
            
            result['success'] = True
            result['details'] = {
                'added_count': added_count,
                'relationship_count': len(result['relationships'])
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def execute(self, decision: Decision) -> Dict[str, Any]:
        """
        Execute the appropriate action based on decision.
        
        Args:
            decision: Decision from DecisionEngine
            
        Returns:
            Execution result dictionary
        """
        if decision.action == ConflictType.REPLACEMENT:
            return self.execute_replacement(decision)
        elif decision.action == ConflictType.MERGE:
            return self.execute_merge(decision)
        elif decision.action == ConflictType.INSERT:
            return self.execute_insert(decision)
        else:
            return {'action': 'SKIP', 'success': True, 'reason': decision.reason}


# =============================================================================
# Main Pipeline Orchestrator
# =============================================================================

class DynamicUpdatePipeline:
    """
    Orchestrates the full dynamic update pipeline.
    
    Stages:
    1. Ingestion & Preprocessing
    2. Embedding & Enrichment
    3. Conflict Detection
    4. Decision Engine
    5. Execution
    """
    
    def __init__(self, vector_store, llm_client=None):
        self.vector_store = vector_store
        self.ingester = DocumentIngester()
        self.enricher = EmbeddingEnricher()
        self.detector = ConflictDetector(vector_store)
        self.decision_engine = DecisionEngine(vector_store, llm_client)
        self.executor = UpdateExecutor(vector_store, llm_client)
    
    def process_document(
        self, 
        file_path: Path,
        authority_score: float = 1.0,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Process a document through the full pipeline.
        
        Args:
            file_path: Path to PDF file
            authority_score: Authority weight for this document
            progress_callback: Optional callback(stage, progress, message)
            
        Returns:
            Processing result summary
        """
        result = {
            'filename': file_path.name,
            'success': False,
            'chunks_processed': 0,
            'actions': {'REPLACEMENT': 0, 'MERGE': 0, 'INSERT': 0, 'SKIP': 0},
            'warnings': [],
            'errors': []
        }
        
        def update_progress(stage, progress, message):
            if progress_callback:
                progress_callback(stage, progress, message)
            print(f"[{stage}] {message}")
        
        try:
            # Stage 1: Ingestion
            update_progress('ingestion', 0.1, f"Starting ingestion of {file_path.name}")
            chunks, metadata, warnings = self.ingester.ingest(file_path, authority_score)
            result['warnings'].extend(warnings)
            update_progress('ingestion', 0.2, f"Ingested {len(chunks)} chunks")
            
            # Stage 2: Enrichment
            update_progress('enrichment', 0.3, "Generating embeddings and extracting entities")
            enriched_chunks = self.enricher.enrich_chunks(chunks)
            update_progress('enrichment', 0.5, f"Enriched {len(enriched_chunks)} chunks")
            
            # Stages 3-5: Process each chunk
            for i, enriched_chunk in enumerate(enriched_chunks):
                progress = 0.5 + (0.4 * i / len(enriched_chunks))
                
                # Stage 3: Conflict Detection
                conflict_result = self.detector.detect(enriched_chunk)
                
                # Stage 4: Decision
                decision = self.decision_engine.decide(conflict_result)
                
                # Stage 5: Execution
                exec_result = self.executor.execute(decision)
                
                # Track results
                action_name = decision.action.value.upper()
                result['actions'][action_name] = result['actions'].get(action_name, 0) + 1
                result['chunks_processed'] += 1
                
                if not exec_result.get('success'):
                    result['errors'].append(exec_result.get('error', 'Unknown error'))
                
                update_progress('processing', progress, 
                    f"Chunk {i+1}/{len(enriched_chunks)}: {action_name}")
            
            result['success'] = True
            update_progress('complete', 1.0, "Processing complete")
            
        except Exception as e:
            result['errors'].append(str(e))
            update_progress('error', 0, str(e))
        
        return result


# Export classes
__all__ = [
    'ConflictType',
    'ValidationResult', 
    'DocumentMetadata',
    'EnrichedChunk',
    'ConflictResult',
    'Decision',
    'DocumentIngester',
    'EmbeddingEnricher',
    'ConflictDetector',
    'DecisionEngine',
    'UpdateExecutor',
    'DynamicUpdatePipeline',
    'CONFLICT_THRESHOLDS'
]


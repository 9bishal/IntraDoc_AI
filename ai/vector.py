"""
FAISS Vector Store Service.

Manages per-department FAISS indexes for storing and retrieving
document embeddings. Now uses the BM25-weighted TF-IDF embedding
engine for dramatically better retrieval quality.

Improvements over original:
    - Proper semantic embeddings (BM25 + TF-IDF) instead of naive BoW hashing
    - Cosine similarity (Inner Product) instead of L2 distance for normalized vectors
    - Relevance score filtering (rejects low-quality matches)
    - Query result caching (avoids redundant searches)
    - Cache invalidation on document add/delete

Department indexes:
    - hr_index
    - accounts_index
    - legal_index
"""

import json
import logging
from pathlib import Path

import faiss
import numpy as np
from django.conf import settings

from .embeddings import get_embedding_engine, EMBEDDING_DIM
from .cache import get_search_cache

logger = logging.getLogger(__name__)

# Supported departments
DEPARTMENTS = ['hr', 'accounts', 'legal', 'finance']

# Minimum relevance score to include a result (cosine similarity threshold).
# Inner product of normalized vectors = cosine similarity, range [-1, 1].
# 0.05 is intentionally low to not over-filter with sparse embeddings.
MIN_RELEVANCE_SCORE = 0.05


class VectorStore:
    """
    Manages FAISS indexes per department.

    Each department has:
        - A FAISS index (Inner Product for cosine similarity)
        - A metadata store mapping vector IDs to text chunks
    """

    def __init__(self):
        self.index_dir = Path(settings.FAISS_INDEX_DIR)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.indexes = {}
        self.metadata = {}
        self._embedding_engine = get_embedding_engine()
        self._load_all_indexes()

    def _get_index_path(self, department):
        """Return the file path for a department's FAISS index."""
        return self.index_dir / f"{department}_index.faiss"

    def _get_metadata_path(self, department):
        """Return the file path for a department's metadata."""
        return self.index_dir / f"{department}_metadata.json"

    def _load_all_indexes(self):
        """Load all existing FAISS indexes from disk."""
        for dept in DEPARTMENTS:
            self._load_index(dept)

    def _load_index(self, department):
        """Load a single department's FAISS index and metadata."""
        index_path = self._get_index_path(department)
        metadata_path = self._get_metadata_path(department)

        if index_path.exists():
            self.indexes[department] = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index for {department}: {self.indexes[department].ntotal} vectors")
        else:
            # Use Inner Product index for cosine similarity (vectors are normalized)
            self.indexes[department] = faiss.IndexFlatIP(EMBEDDING_DIM)
            logger.info(f"Created new FAISS index for {department}")

        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata[department] = json.load(f)
        else:
            self.metadata[department] = []

    def _save_index(self, department):
        """Persist a department's FAISS index and metadata to disk."""
        index_path = self._get_index_path(department)
        metadata_path = self._get_metadata_path(department)

        faiss.write_index(self.indexes[department], str(index_path))
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata[department], f, indent=2)

        logger.info(f"Saved FAISS index for {department}: {self.indexes[department].ntotal} vectors")

    def add_chunks(self, department, chunks, document_id=None):
        """
        Add text chunks to a department's FAISS index.

        Args:
            department: Department name (hr, accounts, legal).
            chunks: List of text strings to index.
            document_id: Optional document ID for metadata tracking.

        Returns:
            int: Number of chunks added.
        """
        if department not in DEPARTMENTS:
            raise ValueError(f"Invalid department: {department}. Must be one of {DEPARTMENTS}")

        if not chunks:
            return 0

        # Ensure index exists
        if department not in self.indexes:
            self._load_index(department)

        # Update IDF statistics with new chunks
        self._embedding_engine.update_stats(chunks)

        # Generate embeddings using the improved engine
        embeddings_array = self._embedding_engine.embed_batch(chunks)

        # Add to FAISS index
        start_id = self.indexes[department].ntotal
        self.indexes[department].add(embeddings_array)

        # Store metadata
        for i, chunk in enumerate(chunks):
            self.metadata[department].append({
                'id': start_id + i,
                'text': chunk,
                'document_id': document_id,
            })

        # Persist to disk
        self._save_index(department)

        # Invalidate search cache for this department
        get_search_cache().invalidate(department)

        logger.info(f"Added {len(chunks)} chunks to {department} index")
        return len(chunks)

    def search(self, query, departments, top_k=5):
        """
        Search for relevant chunks across specified departments.

        Features:
            - Checks cache first (avoids redundant computation)
            - Uses cosine similarity (Inner Product on normalized vectors)
            - Filters results below MIN_RELEVANCE_SCORE
            - Returns results sorted by relevance (highest first)

        Args:
            query: The search query text.
            departments: List of department names to search.
            top_k: Number of top results to return per department.

        Returns:
            list: List of dicts with 'text', 'department', 'score', 'document_id'.
        """
        # Check cache first
        cache = get_search_cache()
        cached = cache.get(query, departments)
        if cached is not None:
            return cached

        query_embedding = self._embedding_engine.embed(query)
        query_vector = np.array([query_embedding], dtype=np.float32)

        results = []
        for dept in departments:
            if dept not in self.indexes or self.indexes[dept].ntotal == 0:
                logger.debug(f"No vectors in {dept} index, skipping")
                continue

            # Search the index
            k = min(top_k, self.indexes[dept].ntotal)
            scores, indices = self.indexes[dept].search(query_vector, k)

            for i in range(k):
                idx = int(indices[0][i])
                score = float(scores[0][i])

                # Filter out low-relevance results
                if score < MIN_RELEVANCE_SCORE:
                    continue

                if idx < len(self.metadata[dept]):
                    meta = self.metadata[dept][idx]
                    results.append({
                        'text': meta['text'],
                        'department': dept,
                        'score': score,
                        'document_id': meta.get('document_id'),
                    })

        # Sort by score (higher = more relevant for Inner Product / cosine similarity)
        results.sort(key=lambda x: x['score'], reverse=True)
        final_results = results[:top_k]

        # Cache the results
        cache.put(query, departments, final_results)

        return final_results

    def remove_document(self, department, document_id):
        """
        Remove all chunks for a specific document from the index.

        Since FAISS doesn't support direct deletion efficiently,
        we rebuild the index without the deleted document's chunks.

        Args:
            department: Department name.
            document_id: The document ID to remove.

        Returns:
            int: Number of chunks removed.
        """
        if department not in self.metadata:
            return 0

        # Filter out chunks belonging to this document
        original_count = len(self.metadata[department])
        remaining = [m for m in self.metadata[department] if m.get('document_id') != document_id]
        removed_count = original_count - len(remaining)

        if removed_count == 0:
            return 0

        # Rebuild FAISS index with remaining chunks
        texts = [m['text'] for m in remaining]
        new_index = faiss.IndexFlatIP(EMBEDDING_DIM)

        if texts:
            embeddings = self._embedding_engine.embed_batch(texts)
            new_index.add(embeddings)

        # Update metadata IDs
        for i, meta in enumerate(remaining):
            meta['id'] = i

        self.indexes[department] = new_index
        self.metadata[department] = remaining
        self._save_index(department)

        # Invalidate cache
        get_search_cache().invalidate(department)

        logger.info(f"Removed {removed_count} chunks for document {document_id} from {department}")
        return removed_count

    def get_index_stats(self):
        """Return statistics about all indexes."""
        stats = {}
        for dept in DEPARTMENTS:
            if dept in self.indexes:
                stats[dept] = {
                    'total_vectors': self.indexes[dept].ntotal,
                    'total_chunks': len(self.metadata.get(dept, [])),
                }
            else:
                stats[dept] = {'total_vectors': 0, 'total_chunks': 0}
        return stats


# ---- Singleton instance ----
_vector_store = None


def get_vector_store():
    """Return a singleton VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def reset_vector_store():
    """Reset the singleton (useful after rebuilding indexes)."""
    global _vector_store
    _vector_store = None

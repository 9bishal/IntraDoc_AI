"""
Semantic Embedding Engine using Sentence-Transformers.

Uses `all-MiniLM-L6-v2` — the best lightweight semantic model:
    - 384-dimensional embeddings (matches our FAISS index)
    - ~80MB model weight
    - ~200-400MB runtime RAM
    - True semantic understanding: handles synonyms, paraphrases, conceptual similarity

Examples of what this enables:
    - "get my money back" → matches "refund policy"
    - "leaving the company" → matches "resignation procedure"
    - "cancel subscription" → matches "terminate account"

Design for 8GB RAM:
    - Model loaded once as singleton (~400MB)
    - Batch encoding for efficiency
    - No GPU required (CPU inference, plenty fast for RAG)
"""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# all-MiniLM-L6-v2 produces 384-dim vectors — matches our existing EMBEDDING_DIM
EMBEDDING_DIM = 384
MODEL_NAME = 'all-MiniLM-L6-v2'


class EmbeddingEngine:
    """
    Semantic embedding engine backed by Sentence-Transformers.

    Features:
        - True semantic similarity (not just lexical matching)
        - Synonym/paraphrase awareness
        - Conceptual understanding across vocabulary gaps
        - Batch encoding for document indexing
        - Singleton model — loaded once, reused across requests
    """

    def __init__(self):
        import torch
        logger.info(f"Loading embedding model: {MODEL_NAME} ...")
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self._model = SentenceTransformer(MODEL_NAME, device=device)
        logger.info(
            f"Model loaded: {MODEL_NAME} on {device} "
            f"(dim={self._model.get_sentence_embedding_dimension()})"
        )

    def embed(self, text):
        """
        Convert text to a 384-dim semantic embedding.

        Args:
            text: Input text string.

        Returns:
            numpy array of shape (EMBEDDING_DIM,), L2-normalized.
        """
        # encode() returns normalized vectors by default with normalize_embeddings=True
        embedding = self._model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.astype(np.float32)

    def embed_batch(self, texts):
        """
        Embed multiple texts efficiently in a single batch.

        Much faster than calling embed() in a loop — the model
        processes all texts in parallel on CPU.

        Args:
            texts: List of text strings.

        Returns:
            numpy array of shape (len(texts), EMBEDDING_DIM).
        """
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,  # Process 32 texts at a time (memory-friendly)
        )
        return embeddings.astype(np.float32)

    def update_stats(self, texts):
        """
        No-op for compatibility with vector.py.

        The BM25 engine needed IDF statistics updated when adding docs.
        Sentence-Transformers doesn't need this — the model is pre-trained.
        Kept as a no-op so vector.py doesn't need changes.
        """
        pass


# ---- Singleton ----
_engine = None


def get_embedding_engine():
    """Return singleton EmbeddingEngine instance."""
    global _engine
    if _engine is None:
        _engine = EmbeddingEngine()
    return _engine

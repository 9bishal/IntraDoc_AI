# Step 5: Vector Retrieval — Summary

## What Was Built

FAISS-based vector retrieval system in `ai/vector.py` with per-department isolation.

### Core Function

```python
get_relevant_chunks(query, user, top_k=5) → list[dict]
```

**Logic:**
1. Determine accessible departments from user's role
2. Convert query to embedding vector
3. Search FAISS indexes for matching departments only
4. Sort results by L2 distance (lower = more relevant)
5. Return top-k results

### FAISS Index Architecture

```
faiss_indexes/
├── hr_index.faiss          # HR department vectors
├── hr_metadata.json        # HR chunk text + document IDs
├── accounts_index.faiss    # Accounts department vectors
├── accounts_metadata.json
├── legal_index.faiss       # Legal department vectors
├── legal_metadata.json
└── vocabulary.json         # Shared vocabulary for embeddings
```

### Embedding Strategy
- **Dimension**: 384
- **Method**: Bag-of-words with hashing trick
- No external embedding API dependency (works fully offline)
- Vocabulary grows dynamically as new documents are indexed
- Vectors are L2-normalized for consistent distance comparisons

### Search Behavior by Role

| Role     | Indexes Searched                        |
|----------|----------------------------------------|
| ADMIN    | `hr_index` + `accounts_index` + `legal_index` |
| HR       | `hr_index` only                        |
| ACCOUNTS | `accounts_index` only                  |
| LEGAL    | `legal_index` only                     |

### VectorStore Singleton
- `get_vector_store()` returns a shared singleton instance
- Indexes are loaded once and kept in memory for fast search
- Auto-persisted to disk after each `add_chunks()` call

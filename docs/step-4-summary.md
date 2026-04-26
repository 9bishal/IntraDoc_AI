# Step 4: Document Upload + Processing — Summary

## What Was Built

End-to-end document upload pipeline in `documents/` with automatic PDF processing.

### Upload Flow

```
User uploads PDF
       ↓
Validate (PDF only, max 20MB)
       ↓
RBAC check (can user upload to this department?)
       ↓
Save file to media/documents/<department>/
       ↓
Extract text (PyPDF)
       ↓
Chunk text (sentence-aware, 500 chars, 50 overlap)
       ↓
Generate embeddings (bag-of-words → 384-dim vector)
       ↓
Store in department's FAISS index
       ↓
Update document record (is_processed=True, chunk_count=N)
```

### Text Extraction (`documents/services.py`)
- Uses `pypdf.PdfReader` to extract text from all pages
- Handles multi-page PDFs with page-by-page extraction
- Raises `ValueError` if PDF contains no extractable text

### Text Chunking (`documents/services.py`)
- **Chunk size**: 500 characters (configurable)
- **Overlap**: 50 characters between consecutive chunks
- **Sentence-aware**: Tries to break at sentence boundaries (`.`, `?`, `!`, `\n`)
- Filters out very short chunks (< 20 chars)

### FAISS Indexing (`ai/vector.py`)
- Per-department indexes: `hr_index.faiss`, `accounts_index.faiss`, `legal_index.faiss`
- Metadata stored alongside in JSON files for text retrieval

## API Created

### `POST /api/documents/upload/`
- **Content-Type**: `multipart/form-data`
- **Fields**: `file` (PDF), `department` (hr/accounts/legal)
- **Auth**: JWT required
- **RBAC**: Non-admin users can only upload to their own department

### `GET /api/documents/`
- Lists documents accessible to the user (filtered by department)

### `GET /api/documents/stats/`
- Returns document counts and FAISS index statistics

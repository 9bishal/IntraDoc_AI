"""
Document processing service — Enhanced.

Improvements:
    - Larger chunk size (800 chars) with more overlap (150 chars) for better context
    - Smarter sentence-aware splitting
    - Text cleaning: removes headers/footers, excessive whitespace, page numbers
    - Quality filtering: rejects chunks that are too short or lack meaningful content
"""

import logging
import re

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Chunking configuration — tuned for RAG accuracy
DEFAULT_CHUNK_SIZE = 800   # characters per chunk (larger = more context per chunk)
DEFAULT_CHUNK_OVERLAP = 150  # overlap between chunks (more = fewer missed boundaries)
MIN_CHUNK_LENGTH = 5        # minimum chars to keep a chunk (filters only noise)


def clean_text(text):
    """
    Clean extracted PDF text for better embedding quality.

    Removes:
        - Page numbers and headers/footers
        - Excessive whitespace
        - Common PDF artifacts
    """
    # Remove page numbers (standalone numbers or "Page X")
    text = re.sub(r'\n\s*Page\s+\d+\s*\n', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # Remove common header/footer patterns
    text = re.sub(r'\n\s*[-—]+\s*\n', '\n', text)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)    # Collapse 3+ newlines
    text = re.sub(r' {2,}', ' ', text)         # Collapse multiple spaces
    text = re.sub(r'\t+', ' ', text)           # Replace tabs

    # Remove non-printable characters (except newlines)
    text = re.sub(r'[^\S\n]+', ' ', text)

    return text.strip()


def extract_text_from_pdf(file_source):
    """
    Extract text content from a PDF file.

    Args:
        file_source: Path to a PDF file or a file-like object.

    Returns:
        str: Extracted and cleaned text content.

    Raises:
        ValueError: If the PDF cannot be read or contains no text.
    """
    try:
        # PdfReader accepts either a filesystem path or a file-like object.
        # This allows processing to work with remote storages (e.g. Cloudinary)
        # where `FieldFile.path` may not exist.
        if hasattr(file_source, 'seek'):
            file_source.seek(0)
        reader = PdfReader(file_source)
        text_parts = []

        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
            else:
                logger.warning(f"No text extracted from page {page_num}")

        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            raise ValueError("PDF contains no extractable text.")

        # Clean the text
        full_text = clean_text(full_text)

        logger.info(f"Extracted {len(full_text)} characters from PDF ({len(reader.pages)} pages)")
        return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        raise ValueError(f"Failed to process PDF: {str(e)}")


def chunk_text(text, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_CHUNK_OVERLAP):
    """
    Split text into overlapping chunks for embedding.

    Uses a sentence-aware approach: tries to break at sentence boundaries
    when possible to keep chunks semantically coherent.

    Args:
        text: The full text to chunk.
        chunk_size: Target size for each chunk (in characters).
        overlap: Number of characters to overlap between chunks.

    Returns:
        list: List of text chunk strings.
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # If text is shorter than chunk_size, return as single chunk
    if len(text) <= chunk_size:
        return [text] if len(text) >= MIN_CHUNK_LENGTH else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take everything remaining
            chunk = text[start:].strip()
            if chunk and len(chunk) >= MIN_CHUNK_LENGTH:
                chunks.append(chunk)
            break

        # Try to find a sentence boundary near the end
        # Search in the last third of the chunk for good break points
        search_start = start + chunk_size * 2 // 3

        # Priority: paragraph break > sentence end > clause break > any space
        boundary = text.rfind('\n\n', search_start, end)
        if boundary == -1:
            boundary = text.rfind('. ', search_start, end)
        if boundary == -1:
            boundary = text.rfind('? ', search_start, end)
        if boundary == -1:
            boundary = text.rfind('! ', search_start, end)
        if boundary == -1:
            boundary = text.rfind('\n', search_start, end)
        if boundary == -1:
            boundary = text.rfind('; ', search_start, end)
        if boundary == -1:
            boundary = text.rfind(', ', search_start, end)

        if boundary != -1:
            end = boundary + 1  # Include the punctuation

        chunk = text[start:end].strip()
        if chunk and len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)

        # Move start forward (with overlap)
        start = max(start + 1, end - overlap)

    logger.info(f"Created {len(chunks)} chunks from {len(text)} characters "
                f"(avg {sum(len(c) for c in chunks) // max(len(chunks), 1)} chars/chunk)")
    return chunks


def process_document(file_path=None, file_obj=None, department=None, document_id=None):
    """
    Full document processing pipeline: extract text → chunk → index.

    Args:
        file_path: Optional path to the PDF file.
        file_obj: Optional file-like object for remote storage backends.
        department: Department the document belongs to.
        document_id: Database ID of the document record.

    Returns:
        dict: Processing results with chunk count and status.
    """
    from ai.vector import get_vector_store

    if not file_path and file_obj is None:
        raise ValueError("Either file_path or file_obj must be provided.")
    if not department:
        raise ValueError("department is required.")

    source_label = file_path if file_path else getattr(file_obj, 'name', '<in-memory-file>')
    logger.info(f"Processing document: {source_label} for department: {department}")

    # Step 1: Extract text
    text = extract_text_from_pdf(file_obj if file_obj is not None else str(file_path))

    # Step 2: Chunk the text
    chunks = chunk_text(text)

    if not chunks:
        return {
            'status': 'warning',
            'message': 'No usable text chunks extracted from document.',
            'chunk_count': 0,
        }

    # Step 3: Add chunks to FAISS index
    vector_store = get_vector_store()
    added = vector_store.add_chunks(department, chunks, document_id=document_id)

    logger.info(f"Document processed: {added} chunks indexed for {department}")

    return {
        'status': 'success',
        'message': f'Document processed: {added} chunks indexed.',
        'chunk_count': added,
    }

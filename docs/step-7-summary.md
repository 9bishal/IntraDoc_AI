# Step 7: RAG Pipeline — Summary

## What Was Built

Full Retrieval-Augmented Generation pipeline in `ai/rag.py`.

### Pipeline Flow

```
User submits query
       ↓
check user role → get_accessible_departments()
       ↓
search FAISS → get_relevant_chunks(query, user)
       ↓
build prompt → build_prompt(query, chunks)
       ↓
call Ollama → generate_response(prompt)
       ↓
return response + metadata
```

### Core Function

```python
process_query(query, user) → dict
```

**Returns:**
```json
{
    "response": "AI-generated answer text",
    "chunks_used": [{"text": "...", "department": "hr", "score": 0.42}],
    "error": null
}
```

### Prompt Template

```
You are a helpful AI assistant that answers questions using ONLY the provided context.
If the context does not contain relevant information, say so clearly.
Do NOT make up information. Do NOT use knowledge outside the provided context.

Context:
[Document 1 - HR]
<chunk text>

[Document 2 - HR]
<chunk text>

Question: <user query>

Answer:
```

### Edge Cases
- **No chunks found**: Returns a helpful message without calling the LLM
- **LLM error**: Returns the chunks found + error message so the user knows documents exist
- **Empty departments**: Gracefully skips departments with no indexed documents

### Key Design Decision
The prompt explicitly instructs the LLM to use ONLY the provided context. This prevents hallucination and ensures answers are grounded in the uploaded documents.

# Step 8: Chat API — Summary

## What Was Built

Chat API endpoint that ties together authentication, RBAC, vector retrieval, and LLM generation.

### API Endpoint

#### `POST /api/chat/`

**Request:**
```json
{
    "query": "What is the company leave policy?"
}
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Response:**
```json
{
    "query": "What is the company leave policy?",
    "response": "Based on the documents, the company allows 15 days of annual leave...",
    "chunks_used": 3,
    "departments_searched": ["hr"]
}
```

### Internal Flow

1. **Validate** — Check JWT token, parse query from request body
2. **RBAC** — Determine which departments the user can search
3. **Retrieve** — Search FAISS indexes for relevant document chunks
4. **Build Prompt** — Construct context-aware prompt with retrieved chunks
5. **Generate** — Send prompt to Ollama/Mistral for response
6. **Log** — Save query + response to `ChatLog` table
7. **Return** — Send response with metadata (chunks used, departments searched)

### Chat History

#### `GET /api/chat/history/`
- Returns all past chat interactions for the authenticated user
- Ordered by most recent first

**Response:**
```json
[
    {
        "id": 1,
        "username": "hr_user",
        "query": "What is the leave policy?",
        "response": "Based on the documents...",
        "timestamp": "2026-04-18T12:00:00Z"
    }
]
```

### Error Scenarios
| Scenario | HTTP Status | Response |
|----------|------------|----------|
| No JWT token | 401 | Unauthorized |
| Empty query | 400 | Validation error |
| No documents indexed | 200 | Helpful "no documents found" message |
| Ollama offline | 200 | Chunks found + error warning |

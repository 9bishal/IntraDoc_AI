# Step 6: Ollama Integration (Mistral) — Summary

## What Was Built

Ollama LLM service in `ai/llm.py` providing a clean interface to the Mistral model.

### Core Function

```python
generate_response(prompt, model=None, timeout=120) → str
```

**Configuration** (via environment variables):
- `OLLAMA_BASE_URL`: Default `http://localhost:11434`
- `OLLAMA_MODEL`: Default `mistral`

### API Call

```
POST http://localhost:11434/api/generate

{
    "model": "mistral",
    "prompt": "...",
    "stream": false
}
```

### Error Handling

| Error Type          | OllamaError Message                                |
|--------------------|---------------------------------------------------|
| Connection refused  | "Cannot connect to Ollama... Ensure Ollama is running" |
| Timeout            | "Ollama request timed out after {timeout}s"        |
| HTTP error         | "Ollama HTTP error: {status} - {body}"             |
| Empty response     | "Ollama returned an empty response"                |

All errors raise `OllamaError` (custom exception) for clean upstream handling.

### Health Check

```python
check_ollama_health() → dict
```

- Queries `GET /api/tags` to list available models
- Returns `ollama_reachable`, `model_available`, `available_models`
- Used by the `/api/health/` endpoint

### Prerequisites
- Ollama must be running: `ollama serve`
- Mistral model must be pulled: `ollama pull mistral`

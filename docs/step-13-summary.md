# Step 13: Clean Coding Rules — Summary

## Rules Applied

### 1. No Hardcoded Secrets
- `SECRET_KEY` → loaded from `.env` via `os.getenv()`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL` → environment variables
- Database credentials → environment variables
- JWT lifetimes → environment variables
- `.env` is in `.gitignore` — never committed

### 2. Environment Variables
All configurable values are in `.env`:
```
SECRET_KEY, DEBUG, ALLOWED_HOSTS
DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
OLLAMA_BASE_URL, OLLAMA_MODEL
FAISS_INDEX_DIR
JWT_ACCESS_TOKEN_LIFETIME_MINUTES, JWT_REFRESH_TOKEN_LIFETIME_DAYS
```

### 3. Modular Services
| Module | Responsibility |
|--------|---------------|
| `users/permissions.py` | RBAC logic only |
| `documents/services.py` | PDF processing only |
| `ai/vector.py` | FAISS operations only |
| `ai/llm.py` | Ollama API calls only |
| `ai/rag.py` | Pipeline orchestration only |

### 4. Separation of Concerns
- **Models** → data structure and validation
- **Serializers** → input/output transformation
- **Views** → HTTP request/response handling
- **Services** → business logic
- **Permissions** → access control

### 5. Code Quality Practices
- Type hints in function signatures
- Comprehensive docstrings on all classes and functions
- Logging at appropriate levels (info, warning, error)
- Custom exception classes (`OllamaError`)
- Constants defined at module level, not inline
- No magic numbers — chunk sizes, dimensions etc. are named constants

### 6. Test Coverage
- 31 tests covering all critical paths
- Tests use `override_settings` for isolation
- Temporary directories for FAISS indexes in tests
- `APIClient.force_authenticate()` for clean test auth

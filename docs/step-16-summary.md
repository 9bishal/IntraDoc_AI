# Step 16: API Documentation & Routes — Summary

## What Was Built

Complete REST API with organized endpoints across multiple apps.

## API Base URL

```
Development: http://localhost:8000/api/
Production: https://yourdomain.com/api/
```

## Root API Endpoint

**GET** `/api/`

Returns available API endpoints and system status:

```json
{
  "status": "IntraDoc AI API v1.0",
  "endpoints": {
    "auth": "/api/users/",
    "documents": "/api/documents/",
    "chat": "/api/chat/",
    "health": "/api/health/"
  },
  "version": "1.0.0",
  "timestamp": "2026-04-26T14:30:00Z"
}
```

## Authentication Endpoints

**Base**: `/api/users/`

### 1. Register User

**POST** `/api/users/register/`

```json
Request:
{
  "username": "john_hr",
  "email": "john@company.com",
  "password": "SecurePass123!",
  "role": "HR"
}

Response (201):
{
  "user_id": 7,
  "username": "john_hr",
  "email": "john@company.com",
  "role": "HR",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

Error (400):
{
  "username": ["Username already exists"],
  "password": ["Password too weak"]
}
```

### 2. Login

**POST** `/api/users/login/`

```json
Request:
{
  "username": "john_hr",
  "password": "SecurePass123!"
}

Response (200):
{
  "user_id": 7,
  "username": "john_hr",
  "role": "HR",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}

Error (401):
{
  "detail": "Invalid credentials"
}
```

### 3. Get User Profile

**GET** `/api/users/profile/`

```
Headers:
Authorization: Bearer <access_token>

Response (200):
{
  "user_id": 7,
  "username": "john_hr",
  "email": "john@company.com",
  "role": "HR",
  "department": "hr",
  "created_at": "2026-04-20T10:00:00Z",
  "permissions": [
    "upload_document",
    "query_documents",
    "view_history"
  ]
}

Error (401):
{
  "detail": "Authentication credentials were not provided."
}
```

### 4. Refresh Token

**POST** `/api/users/token/refresh/`

```json
Request:
{
  "refresh": "<refresh_token>"
}

Response (200):
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}

Error (401):
{
  "detail": "Token is invalid or expired"
}
```

## Document Endpoints

**Base**: `/api/documents/`

### 1. Upload Document

**POST** `/api/documents/upload/`

```
Headers:
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

Form Data:
- file: <PDF file> (required)
- department: "hr" | "legal" | "accounts" | "finance" (required)

Response (201):
{
  "id": 42,
  "filename": "HR_Leave_Policy_2024.pdf",
  "department": "hr",
  "uploaded_by": "john_hr",
  "upload_date": "2026-04-26T14:30:00Z",
  "file_size": 1024000,
  "chunks": 15,
  "status": "indexed"
}

Error (400):
{
  "file": ["No file provided"],
  "department": ["Invalid department"]
}

Error (403):
{
  "detail": "Cannot upload to department: legal (HR users can only upload to: hr)"
}
```

### 2. List Documents

**GET** `/api/documents/`

```
Headers:
Authorization: Bearer <access_token>

Query Params:
?department=hr          (optional, filter by department)
?ordering=-upload_date  (optional, sort by date)
?page=2                 (optional, pagination)

Response (200):
{
  "count": 42,
  "next": "http://localhost:8000/api/documents/?page=3",
  "previous": "http://localhost:8000/api/documents/?page=1",
  "results": [
    {
      "id": 42,
      "filename": "HR_Leave_Policy_2024.pdf",
      "department": "hr",
      "uploaded_by": "john_hr",
      "upload_date": "2026-04-26T14:30:00Z",
      "file_size": 1024000,
      "chunks": 15,
      "status": "indexed"
    }
  ]
}

Error (401):
{
  "detail": "Authentication required"
}
```

### 3. Document Statistics

**GET** `/api/documents/stats/`

```
Headers:
Authorization: Bearer <access_token>

Response (200):
{
  "total_documents": 156,
  "total_chunks": 3245,
  "by_department": {
    "hr": {
      "documents": 42,
      "chunks": 845
    },
    "legal": {
      "documents": 38,
      "chunks": 920
    },
    "accounts": {
      "documents": 35,
      "chunks": 735
    },
    "finance": {
      "documents": 41,
      "chunks": 745
    }
  },
  "indexed_date": "2026-04-26T14:30:00Z"
}
```

## Chat Endpoints

**Base**: `/api/chat/`

### 1. Query Documents (Main Endpoint)

**POST** `/api/chat/`

```
Headers:
Authorization: Bearer <access_token>
Content-Type: application/json

Request:
{
  "query": "What is the annual leave policy?"
}

Response (200):
{
  "response": "Here's what I found:\n• Annual leave: 20 days per year\n• Sick leave: 10 days with certificate\nConclusion: Employees have generous leave benefits.",
  "done": true,
  "query": "What is the annual leave policy?",
  "chunks_used": 2,
  "departments_searched": ["hr"],
  "sources": [
    {
      "id": 42,
      "filename": "HR_Leave_Policy_2024.pdf",
      "department": "hr"
    }
  ]
}

Error (400):
{
  "query": ["This field is required"]
}

Error (401):
{
  "detail": "Authentication required"
}

Error (500):
{
  "error": "Groq API error: 429 - Rate limit exceeded",
  "detail": "LLM service unavailable, please try again later"
}
```

### 2. Streaming Response (Alternative)

**POST** `/api/chat/` with `Accept: application/x-ndjson`

```
Headers:
Authorization: Bearer <access_token>
Accept: application/x-ndjson

Request:
{
  "query": "What is the annual leave policy?"
}

Response (200, streaming):
{"chunk":"Here's"}
{"chunk":" what"}
{"chunk":" I"}
{"chunk":" found:"}
{"chunk":"\n•"}
...
{"done":true,"query":"...","chunks_used":2,"departments_searched":["hr"]}
```

### 3. Chat History

**GET** `/api/chat/history/`

```
Headers:
Authorization: Bearer <access_token>

Query Params:
?page=2                 (optional, pagination)
?ordering=-timestamp    (optional, sort order)
?search=leave          (optional, search in queries)

Response (200):
[
  {
    "id": 125,
    "query": "What is the annual leave policy?",
    "response": "Here's what I found:\n• Annual leave: 20 days per year...",
    "created_at": "2026-04-26T14:30:00Z",
    "chunks_used": 2,
    "sources": [
      {
        "filename": "HR_Leave_Policy_2024.pdf",
        "department": "hr"
      }
    ]
  },
  {
    "id": 124,
    "query": "Tell me about sick leave",
    "response": "Based on your documents:\n• Sick leave: 10 days per year...",
    "created_at": "2026-04-26T14:25:00Z",
    "chunks_used": 1,
    "sources": [
      {
        "filename": "HR_Leave_Policy_2024.pdf",
        "department": "hr"
      }
    ]
  }
]
```

## System Endpoints

**Base**: `/api/`

### 1. Health Check

**GET** `/api/health/`

```
Response (200):
{
  "status": "healthy",
  "database": "✓ Connected",
  "faiss_indexes": "✓ Available",
  "llm_service": "✓ Groq API operational",
  "timestamp": "2026-04-26T14:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}

Response (503):
{
  "status": "degraded",
  "database": "✓ Connected",
  "faiss_indexes": "✗ Missing index for 'hr'",
  "llm_service": "✗ Groq API unreachable",
  "error": "LLM service unavailable"
}
```

## Query Sharing Routes

**Note**: These are NOT API endpoints, but web routes for sharing

### Routes with Pre-configured Interfaces

```
```
Route /query via SearchBox → HR department query interface (React State)
Route /query via SearchBox → Legal department query interface (React State)
Route /query via SearchBox → Accounts department query interface (React State)
Route /query via SearchBox → Finance department query interface (React State)
Route /query via SearchBox → Admin (all departments) query interface (React State)
```

## Authentication Methods

### JWT Token Bearer

All authenticated endpoints require:

```
Headers:
Authorization: Bearer <access_token>
```

### Token Lifecycle

```
1. User registers/logs in
2. Server returns access_token (expires in 60 min)
3. Client stores in localStorage
4. Client sends in Authorization header
5. After expiration:
   - Token returns 401 Unauthorized
   - Client uses refresh_token to get new access_token
   - POST /api/users/token/refresh/
6. New access_token used for subsequent requests
```

## Error Handling

### Standard Error Responses

```json
400 Bad Request:
{
  "field_name": ["Error message"],
  "another_field": ["Error 1", "Error 2"]
}

401 Unauthorized:
{
  "detail": "Authentication credentials were not provided."
}

403 Forbidden:
{
  "detail": "You do not have permission to perform this action."
}

404 Not Found:
{
  "detail": "Not found."
}

429 Too Many Requests:
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}

500 Internal Server Error:
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

### Current Limits (Can be configured)

```
/api/chat/              → 100 requests/hour per user
/api/documents/upload/  → 50 uploads/hour per user
/api/users/login/       → 5 attempts/minute (prevents brute force)
Other endpoints         → 1000 requests/hour per user
```

## CORS Configuration

### Allowed Origins

```
Development:
- http://localhost:5173
- http://127.0.0.1:5173

Production:
- https://yourdomain.com
- https://www.yourdomain.com
```

### Preflight Requests

Browser automatically handles OPTIONS requests before POST/PUT/DELETE

## Pagination

### Default Pagination

```
Endpoints: /api/documents/, /api/chat/history/

Query Params:
?page=1        (default: page 1)
?page_size=20  (default: 20 items per page, max: 100)

Response includes:
{
  "count": 156,           (total items)
  "next": "...?page=2",   (next page URL, null if last page)
  "previous": null,       (previous page URL, null if first page)
  "results": [...]        (items in this page)
}
```

## API Versioning

Currently: **v1.0**

Future: Support for `/api/v2/` for backward compatibility

## Webhook Integration (Future)

Planned for Phase 2:

```
POST /api/webhooks/subscribe/
{
  "event": "document_uploaded",
  "url": "https://external-app.com/webhook"
}

Events:
- document_uploaded
- query_processed
- index_rebuilt
```

## Testing API Endpoints

### Using cURL

```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_hr","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# Use token in subsequent requests
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/chat/history/
```

### Using Postman

1. Create collection "IntraDoc AI"
2. Create requests for each endpoint
3. Set Authorization type: Bearer Token
4. Use environment variable: {{token}}
5. Run tests in sequence

### Using Python

```python
import requests
from requests.auth import HTTPBearerAuth

BASE_URL = "http://localhost:8000/api"

# Login
response = requests.post(f"{BASE_URL}/users/login/", json={
    "username": "john_hr",
    "password": "SecurePass123!"
})
token = response.json()['access_token']

# Query
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/chat/", 
    headers=headers,
    json={"query": "What is the leave policy?"}
)
print(response.json())
```

---

**Complete REST API enabling all IntraDoc AI functionality.**

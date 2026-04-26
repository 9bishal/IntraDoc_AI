# IntraDoc AI — Complete Architecture Guide

**A Role-Based Document Retrieval System with RAG/LLM Integration**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Application Structure](#application-structure)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [RAG Pipeline](#rag-pipeline)
8. [Role-Based Access Control (RBAC)](#role-based-access-control)
9. [Setup & Installation](#setup--installation)
10. [Deployment](#deployment)
11. [Testing](#testing)

---

## Project Overview

**IntraDoc AI** is an enterprise-grade document management and retrieval system that combines:
- **Role-Based Access Control (RBAC)** — Users can only access documents in their department
- **RAG (Retrieval Augmented Generation)** — Intelligent document retrieval + LLM response generation
- **Vector Search** — FAISS-based semantic search for finding relevant document chunks
- **Streaming Chat** — Real-time responses with conversation memory

### Key Features

| Feature | Description |
|---------|-------------|
| **JWT Authentication** | Secure token-based user authentication |
| **RBAC** | 5 roles (ADMIN, HR, ACCOUNTS, LEGAL, FINANCE) with role-based access |
| **Document Upload** | Upload PDFs, automatically indexed in FAISS |
| **Semantic Search** | Find relevant content using embeddings (Sentence-Transformers) |
| **RAG Pipeline** | Retrieve context + generate answers using Groq LLM API |
| **Chat History** | Store and retrieve conversation logs |
| **Streaming Response** | Real-time chat responses with JSON-Line format |
| **Query Sharing** | Shareable links for department-specific queries |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React SPA)                     │
│                   (Document Upload + Chat UI)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                   HTTP/JSON-RPC
                         │
┌─────────────────────────▼────────────────────────────────────────┐
│                    Django REST API                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│  │  Users   │Documents │  Chat    │   AI     │  Health  │       │
│  │ (Auth)   │(Upload)  │(Query)   │ (RAG)    │ (Status) │       │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘       │
└─────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌────────────┐  ┌─────────────┐  ┌──────────┐
   │ SQLite DB  │  │ FAISS Index │  │Groq API  │
   │ (Users,    │  │(Embeddings) │  │(LLM)     │
   │ Documents, │  │             │  │          │
   │ ChatLogs)  │  │             │  │          │
   └────────────┘  └─────────────┘  └──────────┘
```

### Request Flow

```
1. User Login
   ├─ POST /api/auth/login
   ├─ Generate JWT token
   └─ Return access_token, refresh_token

2. Upload Document
   ├─ POST /api/documents/upload (multipart/form-data)
   ├─ Store PDF in media/
   ├─ Extract text from PDF
   ├─ Chunk text into sentences/paragraphs
   ├─ Generate embeddings using Sentence-Transformers
   ├─ Add chunks to FAISS index
   └─ Store metadata in SQLite

3. Query Document
   ├─ POST /api/chat/ (with JWT token)
   ├─ Validate user role & department access
   ├─ Generate embedding for query
   ├─ Search FAISS for top-k similar chunks
   ├─ Build RAG prompt with chunks as context
   ├─ Call Groq LLM API with prompt
   ├─ Stream response to frontend
   ├─ Log query & response in ChatLog
   └─ Return response with metadata

4. Share Query Link
   ├─ GET /query/{department}/
   ├─ Redirect to pre-filled query form
   └─ Auto-load documents for department
```

---

## Technology Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Backend** | Django 4.2 | Web framework |
| | Django REST Framework | API development |
| | SimpleJWT | Token authentication |
| **Vector Search** | FAISS | Semantic search |
| | Sentence-Transformers | Text embeddings |
| **LLM** | Groq API (llama-3.1-8b-instant) | Response generation |
| **PDF Processing** | PyPDF2 / pdfplumber | Text extraction |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Data storage |
| **Async** | Celery (optional) | Background tasks |
| **Frontend** | React SPA | UI |
| **Testing** | pytest-django | Test framework |

---

## Application Structure

```
IntraDoc_AI/
├── core/                      # Django project settings
│   ├── settings.py           # Configuration (DB, apps, middleware)
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py               # WSGI entry point
│   └── asgi.py               # ASGI entry point
│
├── users/                     # Authentication & User Management
│   ├── models.py             # User model with Role choices
│   ├── views.py              # Register, Login, Profile views
│   ├── serializers.py        # User serialization
│   ├── permissions.py        # RBAC permission logic
│   ├── urls.py               # Auth endpoints
│   └── management/
│       └── commands/
│           └── seed_users.py # Create test users
│
├── documents/                 # Document Management
│   ├── models.py             # Document model
│   ├── views.py              # Upload, List, Stats views
│   ├── serializers.py        # Document serialization
│   ├── services.py           # PDF processing, chunking, indexing
│   ├── urls.py               # Document endpoints
│   └── migrations/           # Database migrations
│
├── chat/                      # Chat & Query Interface
│   ├── models.py             # ChatLog model for history
│   ├── views.py              # Chat endpoint (query processing)
│   ├── serializers.py        # ChatLog serialization
│   ├── urls.py               # Chat endpoints
│   └── migrations/           # Database migrations
│
├── ai/                        # RAG Pipeline & LLM Integration
│   ├── rag.py                # Main RAG orchestration
│   ├── llm.py                # Groq API integration
│   ├── vector.py             # FAISS vector store
│   ├── embeddings.py         # Embedding model (Sentence-Transformers)
│   ├── cache.py              # Caching utilities
│   ├── views.py              # Health check endpoint
│   └── management/
│       └── commands/
│           └── rebuild_indexes.py # Rebuild FAISS index
│
├── frontend/                  # React SPA Frontend
│   ├── src/                  # React source code
│   └── package.json          # Node dependencies
│
├── tests/                     # Test Suite
│   ├── test_rag_e2e.py       # End-to-end RAG tests
│   └── __init__.py
│
├── media/                     # Uploaded documents
│   └── documents/
│       ├── hr/               # HR department docs
│       ├── legal/            # Legal department docs
│       ├── accounts/         # Accounts department docs
│       └── finance/          # Finance department docs
│
├── faiss_indexes/            # Vector search indexes
│   └── indexes.index         # FAISS index file
│
├── docs/                      # Documentation
│   ├── step-1-summary.md     # Setup & Installation
│   ├── step-2-summary.md     # Authentication Flow
│   ├── step-3-summary.md     # Document Upload Pipeline
│   ├── step-4-summary.md     # FAISS Indexing
│   ├── step-5-summary.md     # Embeddings & Vector Search
│   ├── step-6-summary.md     # RAG Pipeline
│   ├── step-7-summary.md     # LLM Integration (Groq)
│   ├── step-8-summary.md     # Chat Interface
│   ├── step-9-summary.md     # RBAC & Access Control
│   ├── step-10-summary.md    # Streaming Responses
│   ├── step-11-summary.md    # Chat History & Logging
│   ├── step-12-summary.md    # Testing & Quality Assurance
│   └── step-13-summary.md    # Deployment & Scalability
│
├── .env                       # Environment variables
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── manage.py                  # Django CLI
├── README.md                  # Quick start guide
└── ARCHITECTURE.md            # This file
```

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/login/` | Login user, return JWT tokens | ❌ |
| POST | `/register/` | Register new user | ❌ |
| GET | `/profile/` | Get current user profile | ✅ |
| POST | `/token/refresh/` | Refresh expired access token | ✅ |

### Documents (`/api/documents/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/upload/` | Upload PDF document | ✅ |
| GET | `/` | List accessible documents | ✅ |
| GET | `/stats/` | Document statistics | ✅ |

### Chat (`/api/chat/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/` | Query documents, get AI response | ✅ |
| GET | `/history/` | Retrieve chat history | ✅ |

### Query Sharing (`/query/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/query?dept=hr` | Pre-filled HR query form | ❌ |
| GET | `/query?dept=legal` | Pre-filled Legal query form | ❌ |
| GET | `/query?dept=accounts` | Pre-filled Accounts query form | ❌ |
| GET | `/query?dept=finance` | Pre-filled Finance query form | ❌ |

### System (`/api/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | API documentation & endpoints | ❌ |
| GET | `/health/` | Health check (LLM, DB, FAISS status) | ❌ |

---

## Database Schema

### Users Table

```sql
-- User model with Role-Based Access Control
CREATE TABLE users_user (
    id UUID PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    email VARCHAR(254) UNIQUE,
    password_hash VARCHAR(255),
    role ENUM('ADMIN', 'HR', 'ACCOUNTS', 'LEGAL', 'FINANCE'),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- department is a property that maps role to lowercase:
-- ADMIN → 'admin' (access all)
-- HR → 'hr' (access only HR docs)
-- LEGAL → 'legal' (access only Legal docs)
-- ACCOUNTS → 'accounts' (access only Accounts docs)
-- FINANCE → 'finance' (access only Finance docs)
```

### Documents Table

```sql
CREATE TABLE documents_document (
    id UUID PRIMARY KEY,
    filename VARCHAR(255),
    file VARCHAR(255),  -- Path to PDF in media/
    department VARCHAR(50),  -- 'hr', 'legal', 'accounts', 'finance'
    file_size INT,
    uploaded_by_id UUID FOREIGN KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### ChatLog Table

```sql
CREATE TABLE chat_chatlog (
    id UUID PRIMARY KEY,
    user_id UUID FOREIGN KEY,
    query TEXT,
    response TEXT,
    context_chunks TEXT,  -- JSON array of chunk IDs/texts
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### FAISS Index Structure

```json
{
  "indexes": {
    "hr": {
      "embeddings": [float32_array],
      "metadata": [
        {
          "chunk_id": "doc_1_chunk_0",
          "document_id": 1,
          "text": "...",
          "department": "hr"
        }
      ]
    },
    "legal": { ... },
    "accounts": { ... },
    "finance": { ... }
  }
}
```

---

## RAG Pipeline

### Step-by-Step Flow

```
1. USER QUERY INPUT
   └─ "What is the annual leave policy?"

2. GENERATE QUERY EMBEDDING
   ├─ Use Sentence-Transformers (all-MiniLM-L6-v2)
   ├─ Convert query to 384-dimensional vector
   └─ embedding_query = [0.123, -0.456, 0.789, ...]

3. SEARCH FAISS INDEX
   ├─ Filter by accessible departments (RBAC)
   ├─ Find top-k most similar chunks (k=5)
   ├─ Return with similarity scores
   └─ chunks = [
        {"text": "Annual leave is 20 days...", "score": 0.89},
        {"text": "Leave request must be...", "score": 0.85},
        ...
      ]

4. BUILD RAG PROMPT
   ├─ System prompt: "You are IntraDoc AI, answer questions about documents"
   ├─ Context: chunks concatenated with numbering
   ├─ User query: original question
   └─ messages = [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "Question: ...\n\nContext: ...\n\n---Excerpt 1---\n..."}
      ]

5. CALL LLM (Groq API)
   ├─ Model: llama-3.1-8b-instant
   ├─ Parameters: temp=0.7, max_tokens=1024
   ├─ Endpoint: https://api.groq.com/openai/v1/chat/completions
   └─ Response: AI-generated answer using only context

6. STREAM RESPONSE
   ├─ Yield response text chunk by chunk
   ├─ Format: JSON-Line (each line is a JSON object)
   ├── Frontend receives: {"chunk": "Here's what..."}\n
   └─ Accumulate and display in real-time

7. LOG INTERACTION
   ├─ Store query + response in ChatLog
   ├─ Store used chunks
   └─ Enable chat history for users

8. RETURN METADATA
   └─ Return with:
      - response: generated text
      - chunks_used: count of context chunks
      - departments_searched: accessible depts
      - sources: document metadata
```

### Key Prompt Instructions (in ai/rag.py)

```python
SYSTEM_PROMPT = """You are IntraDoc AI, a friendly professional document assistant.

RESPONSE FORMAT:
1. Start with one short greeting
2. Answer using bullet points only
3. End with one brief conclusion sentence

RULES:
1. ALWAYS respond in English regardless of document language
2. NEVER copy raw text — summarize and rephrase
3. Use ONLY facts from reference material
4. If not found, say: "I couldn't find that in your documents."
5. Keep response under 150 words
"""
```

---

## Role-Based Access Control

### Role Definitions

| Role | Department | Access | Use Case |
|------|-----------|--------|----------|
| **ADMIN** | admin | All departments | HR/Management |
| **HR** | hr | HR documents only | HR staff |
| **ACCOUNTS** | accounts | Accounts documents only | Finance/Accounting |
| **LEGAL** | legal | Legal documents only | Legal staff |
| **FINANCE** | finance | Finance documents only | Finance staff |

### Permission Logic (users/permissions.py)

```python
def get_accessible_departments(user):
    """
    Return list of department(s) accessible to user based on role.
    - ADMIN: access all departments
    - Others: access own department only
    """
    if user.role == Role.ADMIN:
        return ['hr', 'legal', 'accounts', 'finance']
    else:
        return [user.role.lower()]
```

### Access Control Flow

```
1. User makes request (upload/query)
   ├─ JWT token validated
   ├─ User role determined
   └─ Accessible departments calculated

2. Document Upload
   ├─ Check if user can upload to requested department
   ├─ Only ADMIN or same-role users can upload
   └─ Reject if unauthorized

3. Document Query
   ├─ FAISS search filtered by accessible departments
   ├─ No cross-department access for non-ADMIN
   └─ Return only relevant + authorized chunks
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite for dev)
- Groq API Key (free from groq.com)

### Step 1: Clone & Setup

```bash
git clone <repo>
cd IntraDoc_AI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with:
# - SECRET_KEY (Django secret)
# - DEBUG=True (development)
# - GROQ_API_KEY (from groq.com)
# - LLM_MODEL=llama-3.1-8b-instant
# - FAISS_INDEX_DIR=faiss_indexes
```

### Step 3: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create test users
python manage.py seed_users

# Create superuser (optional)
python manage.py createsuperuser
```

### Step 4: Build FAISS Index

```bash
# Initialize vector store
python manage.py rebuild_indexes
```

### Step 5: Run Server

```bash
python manage.py runserver 0.0.0.0:8000

# Access at:
# - Frontend: http://localhost:5173/
# - API Docs: http://localhost:8000/api/
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Use strong `SECRET_KEY`
- [ ] Configure PostgreSQL
- [ ] Set up CORS for frontend domain
- [ ] Configure CSRF protection
- [ ] Use HTTPS only
- [ ] Set up SSL certificates
- [ ] Configure firewalls
- [ ] Enable rate limiting
- [ ] Monitor LLM API usage

### Deployment Options

1. **Heroku**
   ```bash
   heroku create intradoc-ai
   git push heroku main
   ```

2. **Docker**
   ```dockerfile
   FROM python:3.11
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

3. **AWS / DigitalOcean**
   - Use managed database (RDS/PostgreSQL)
   - Deploy with Gunicorn + Nginx
   - Configure CloudFront for static files

---

## Testing

### Run All Tests

```bash
python manage.py test -v 2
```

### Run Specific Test Suite

```bash
# End-to-end RAG tests
python manage.py test tests.test_rag_e2e -v 2

# Authentication tests
python manage.py test users -v 2

# Document upload tests
python manage.py test documents -v 2
```

### Test Coverage

```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## Performance & Optimization

### Caching Strategy

```python
# Cache embedding model
EMBEDDING_CACHE_TTL = 3600  # 1 hour

# Cache FAISS index
FAISS_CACHE_TTL = 1800  # 30 minutes

# Cache recent chat history
CHAT_HISTORY_CACHE_TTL = 300  # 5 minutes
```

### FAISS Optimization

```python
# Use IndexIVFFlat for large datasets
index = faiss.IndexIVFFlat(dimension, n_clusters=100)
index.train(training_vectors)
index.add(all_vectors)
```

### Rate Limiting

```python
# Limit API calls per user
RATELIMIT_QUERIES_PER_MINUTE = 60
RATELIMIT_UPLOADS_PER_HOUR = 20
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **FAISS not found** | Embeddings not generated | Run `python manage.py rebuild_indexes` |
| **LLM timeout** | Groq API slow | Increase `LLM_TIMEOUT` in .env |
| **No results** | No documents uploaded | Upload PDFs via `/api/documents/upload/` |
| **Access denied** | RBAC blocking request | Check user role and department |
| **Slow search** | Large FAISS index | Partition by department or date |

---

## Support & Contribution

For issues, questions, or contributions:
- **GitHub Issues**: [Report bug]
- **Email**: support@intradoc-ai.com
- **Documentation**: See `/docs/` folder

---

**Last Updated**: April 2026
**Version**: 1.0.0

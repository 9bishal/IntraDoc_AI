# AI Role-Based Document Retrieval Backend

A production-ready Django REST Framework backend for AI-powered document retrieval
with role-based access control, FAISS vector search, and Ollama/Mistral LLM integration.

---

## Architecture

```
User → JWT Auth → RBAC Check → FAISS Vector Search → RAG Prompt → Ollama/Mistral → Response
```

## Tech Stack

| Layer       | Technology                          |
|------------|-------------------------------------|
| Backend    | Django 4.2 + Django REST Framework  |
| Auth       | JWT (SimpleJWT) + bcrypt            |
| LLM        | Ollama (Mistral)                    |
| Vector DB  | FAISS                              |
| Database   | SQLite (dev) / PostgreSQL (prod)    |

## Quick Start

### 1. Setup

```bash
# Clone and enter project
cd IntraDoc_AI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Seed test users
python manage.py seed_users

# Start server
python manage.py runserver
```

### 2. Start Ollama

```bash
ollama serve          # Start Ollama server
ollama pull mistral   # Download Mistral model
```

### 3. Test Users

| Username       | Password        | Role     |
|---------------|-----------------|----------|
| admin         | admin1234       | ADMIN    |
| hr_user       | hrpass1234      | HR       |
| accounts_user | accpass1234     | ACCOUNTS |
| legal_user    | legalpass1234   | LEGAL    |

## API Endpoints

### Authentication

```bash
# Register
POST /api/auth/register/
{"username": "newuser", "password": "password123", "role": "HR"}

# Login
POST /api/auth/login/
{"username": "hr_user", "password": "hrpass1234"}

# Profile
GET /api/auth/profile/
Authorization: Bearer <token>

# Refresh Token
POST /api/auth/token/refresh/
{"refresh": "<refresh_token>"}
```

### Documents

```bash
# Upload PDF
POST /api/documents/upload/
Content-Type: multipart/form-data
file: <pdf_file>
department: hr

# List documents
GET /api/documents/

# Document stats
GET /api/documents/stats/
```

### Chat (RAG)

```bash
# Ask a question
POST /api/chat/
{"query": "What is the leave policy?"}

# Chat history
GET /api/chat/history/
```

### Health Check

```bash
GET /api/health/    # No auth required
```

## RBAC Rules

| Role     | Access                        |
|----------|-------------------------------|
| ADMIN    | All documents, all departments |
| HR       | HR documents only             |
| ACCOUNTS | Accounts documents only       |
| LEGAL    | Legal documents only          |

## Running Tests

```bash
python manage.py test tests.test_api -v 2
```

**31 tests** covering authentication, RBAC, document upload, vector store, chat API, and health check.

## Project Structure

```
IntraDoc_AI/
├── core/          # Django settings & root URLs
├── users/         # User model, auth, RBAC permissions
├── documents/     # Document upload & PDF processing
├── chat/          # Chat API & history
├── ai/            # LLM, FAISS, RAG pipeline
│   ├── llm.py     # Ollama/Mistral integration
│   ├── rag.py     # RAG orchestration
│   └── vector.py  # FAISS vector store
├── tests/         # Test suite
└── docs/          # Step-by-step summaries
```

## 📚 Complete Documentation

All comprehensive step-by-step guides and architecture documentation are in the `/docs` folder:

### Quick Navigation

**For Project Managers/Leaders**
- Start: [PRESENTATION_GUIDE.md](./PRESENTATION_GUIDE.md) — 30-second overview + demo script

**For Developers (Full Stack)**
- Start: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — System design overview
- Then: [docs/INDEX.md](./docs/INDEX.md) — Complete learning path

**For DevOps/Infrastructure**
- Read: [docs/step-17-summary.md](./docs/step-17-summary.md) — Production deployment

**For QA/Testing**
- Read: [docs/step-18-summary.md](./docs/step-18-summary.md) — Test suite & QA

### Complete Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **ARCHITECTURE.md** | System design, data flows, deployment | Architects, Leads |
| **PRESENTATION_GUIDE.md** | Live demo script, business case | Managers, Presenters |
| **docs/INDEX.md** | Learning paths by role | All teams |
| **docs/step-1-summary.md** | Database models | Developers |
| **docs/step-2-summary.md** | RBAC system | Developers |
| **docs/step-3-summary.md** | Document management | Developers |
| **docs/step-4-summary.md** | Vector embeddings & FAISS | ML/Developers |
| **docs/step-5-summary.md** | RAG pipeline | Developers |
| **docs/step-6-summary.md** | Chat interface | Developers |
| **docs/step-7-summary.md** | Authentication & security | Developers |
| **docs/step-8-summary.md** | Testing framework | QA/Developers |
| **docs/step-9-summary.md** | Performance optimization | DevOps |
| **docs/step-10-summary.md** | Error handling & logging | Developers |
| **docs/step-11-summary.md** | LLM integration (Groq) | ML/Developers |
| **docs/step-12-summary.md** | Frontend-backend integration | Frontend |
| **docs/step-13-summary.md** | Clean coding standards | All developers |
| **docs/step-14-summary.md** | Frontend UI/UX | Frontend/Designers |
| **docs/step-15-summary.md** | Query sharing routes | All |
| **docs/step-16-summary.md** | Complete API reference | Developers/Integrators |
| **docs/step-17-summary.md** | Production deployment | DevOps |
| **docs/step-18-summary.md** | Testing & QA | QA/Developers |

### Key Features Documented

- ✅ **Role-Based Access Control** — Full RBAC with 5 roles
- ✅ **Document Upload & Storage** — PDF processing with chunking
- ✅ **Vector Search** — FAISS semantic similarity
- ✅ **RAG Pipeline** — Question answering with context
- ✅ **LLM Integration** — Groq API (free, fast, reliable)
- ✅ **Authentication** — JWT token-based auth
- ✅ **Frontend** — Modern single-page application
- ✅ **API Routes** — Shareable query links (/query/hr/, /query/legal/, etc.)
- ✅ **Testing** — 31+ comprehensive tests
- ✅ **Production** — Deployment guide with Docker & Nginx

---

## License

MIT

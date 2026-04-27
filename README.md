# IntraDoc Intelligence — AI-Powered Document Retrieval System

An enterprise-grade, role-based document intelligence platform powered by Django, FAISS vector search, Groq LLM (LLaMA 3.1), Firebase Analytics, and a modern React SPA frontend.

---

## Architecture

```
User → Firebase Auth → JWT Auth → RBAC Check → FAISS Vector Search → RAG Prompt → Groq API → Structured Response
                                                                                      ↓
                                                                              Firebase Firestore
                                                                              (Chat History + Analytics)
```

## Tech Stack

| Layer          | Technology                            |
|---------------|---------------------------------------|
| Backend       | Django 4.2 + Django REST Framework    |
| Auth          | JWT (SimpleJWT) + Firebase Auth       |
| LLM           | Groq API (`llama-3.1-8b-instant`)     |
| Embeddings    | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector DB     | FAISS (Facebook AI Similarity Search) |
| Database      | SQLite (dev) / PostgreSQL (prod)      |
| Frontend      | React 18 + Vite + Recharts           |
| Analytics     | Firebase Firestore + Google Analytics |
| Streaming     | `application/x-ndjson` (NDJSON)       |

## Key Features

- 🔐 **Role-Based Access Control (RBAC)** — Admin, HR, Accounts, Legal roles with strict department scoping
- 📄 **PDF Document Upload & Chunking** — Automatic text extraction, chunking, and FAISS indexing
- 🔍 **Semantic Vector Search** — FAISS-powered similarity search with configurable top-k retrieval
- 🤖 **Advanced RAG Pipeline** — 6-step retrieval-based QA with evidence citation, confidence scoring, and hallucination prevention
- 📊 **Real-Time Admin Dashboard** — Token usage, response latency, knowledge gaps, query timeline, and document inventory
- 💬 **Persistent Chat History** — Firebase Firestore per-department conversation storage
- 🔄 **Conversation Memory** — Query expansion using recent chat context for follow-up questions
- 📈 **Performance Benchmarking** — Accurate retrieval time + LLM generation time metrics
- 🌐 **Graph Mode** — Cross-department unified knowledge queries (Admin only)
- 💡 **Smart Suggestions** — Auto-generated follow-up question chips after every response

---

## Quick Start

### 1. Backend Setup

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
# Edit .env with your GROQ_API_KEY

# Run migrations
python manage.py migrate

# Seed test users
python manage.py seed_users

# Start backend server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Environment Variables

**Backend (`.env`)**:
```bash
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.1-8b-instant
SECRET_KEY=your_django_secret_key
DEBUG=True
```

**Frontend (`frontend/.env`)**:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

### 4. Test Users

| Username       | Password        | Role     | Departments     |
|---------------|-----------------|----------|-----------------|
| admin         | admin1234       | ADMIN    | All             |
| hr_user       | hrpass1234      | HR       | HR              |
| accounts_user | accpass1234     | ACCOUNTS | Accounts/Finance|
| legal_user    | legalpass1234   | LEGAL    | Legal           |

---

## API Endpoints

### Authentication

```bash
POST /api/auth/register/     # Register new user
POST /api/auth/login/        # Login → JWT tokens
GET  /api/auth/profile/      # Get user profile (Bearer token)
POST /api/auth/token/refresh/ # Refresh JWT token
```

### Documents

```bash
POST /api/documents/upload/   # Upload PDF (multipart/form-data)
GET  /api/documents/          # List documents (RBAC-scoped)
GET  /api/documents/stats/    # Document statistics
```

### Chat (RAG Pipeline)

```bash
POST /api/chat/              # Query documents (JSON or NDJSON streaming)
GET  /api/chat/history/      # Chat history for authenticated user
```

### Health

```bash
GET  /api/health/            # System health check (no auth required)
```

---

## RAG Pipeline — Prompt Engineering

The system uses a **6-step retrieval-based QA** approach with strict grounding rules:

1. **Answerability Check** — Determines if the question is answerable from the retrieved context
2. **Relevance Filtering** — Uses only directly relevant chunks
3. **Strict Answer Rules** — No outside knowledge, no inference, no generalization
4. **Structured Output** — Key Points → Evidence (with real filenames) → Confidence (High/Medium/Low)
5. **Evidence Integrity** — Only real document filenames, exact quotes, no "Excerpt 1" labels
6. **Special Cases** — NOT FOUND handling, document listing, "who is" questions

### Response Format

```
Key Points:
* Nikhil Gupta's base salary is ₹50,000 per month
* Annual CTC is ₹8,40,000

Evidence:
* "Base Salary: ₹50,000/month" (Source: FINANCE_DOCUMENT_NIKHIL.pdf)

Confidence:
High
```

---

## RBAC Rules

| Role     | Access                         |
|----------|--------------------------------|
| ADMIN    | All documents, all departments, Graph mode |
| HR       | HR documents only              |
| ACCOUNTS | Accounts/Finance documents only|
| LEGAL    | Legal documents only           |

---

## Admin Dashboard

The dashboard (Admin only) provides:

- **Total Tokens Processed** — Estimated token usage across all queries
- **Avg. Response Time** — Mean retrieval + LLM generation latency
- **Knowledge Gaps** — Queries that couldn't be answered from available documents
- **Document Inventory** — Full table with filename, department, contributor, indexing status
- **Query Timeline** — Area chart of query volume over time
- **Latency Benchmarks** — Retrieval vs LLM generation time breakdown
- **Live Activity Feed** — Recent queries with response times
- **System Status** — RAG Engine + Groq LLM health indicators

---

## Project Structure

```
IntraDoc_AI/
├── core/              # Django settings & root URLs
├── users/             # User model, auth, RBAC permissions
├── documents/         # Document upload & PDF processing
├── chat/              # Chat API, history, admin logging
├── ai/                # AI/ML pipeline
│   ├── llm.py         # Groq API integration with health checks
│   ├── rag.py         # RAG orchestration with 6-step prompt
│   ├── vector.py      # FAISS vector store management
│   └── embeddings.py  # SentenceTransformer embeddings
├── frontend/          # React SPA
│   ├── src/pages/     # QueryPage, DashboardPage, LoginPage, etc.
│   ├── src/services/  # API client & RAG service
│   ├── src/firebase.js # Firebase Auth, Firestore, Analytics
│   └── src/context/   # AuthContext (JWT + Firebase)
├── tests/             # Test suite (31+ tests)
├── docs/              # Step-by-step development summaries
├── ARCHITECTURE.md    # System design documentation
├── PRESENTATION_GUIDE.md # Demo script & business case
└── rag_architecture_summary.md # RAG pipeline technical reference
```

---

## Running Tests

```bash
python manage.py test tests.test_api -v 2
```

**31 tests** covering authentication, RBAC, document upload, vector store, chat API, and health check.

---

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **ARCHITECTURE.md** | System design, data flows | Architects, Leads |
| **PRESENTATION_GUIDE.md** | Live demo script, business case | Managers, Presenters |
| **rag_architecture_summary.md** | RAG pipeline deep-dive | ML Engineers |
| **docs/INDEX.md** | Complete learning path | All teams |
| **docs/step-1 to step-18** | Step-by-step build guides | Developers |

---

## License

MIT

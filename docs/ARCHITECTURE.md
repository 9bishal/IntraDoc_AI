# IntraDoc AI — Complete System Architecture

**Document Version**: 1.0  
**Date**: April 26, 2026  
**Status**: Production Ready

---

## 🏗️ High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                              │
│  (React.js - Single Page Application)                           │
│  - User Authentication UI                                       │
│  - Document Upload Interface                                    │
│  - Chat Interface with Real-time Streaming                      │
│  - Chat History Viewer                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           │ (JWT Authentication)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY LAYER                             │
│  (Django REST Framework)                                        │
│  - /api/users/      → Authentication                            │
│  - /api/documents/  → Document Management                       │
│  - /api/chat/       → Query Processing                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ↓                 ↓                 ↓
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   Auth      │  │  Documents  │  │    Chat     │
    │   Service   │  │   Service   │  │   Service   │
    └────┬────────┘  └────┬────────┘  └────┬────────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ↓                ↓                ↓
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Users   │    │Documents │    │ ChatLogs │
    │   (DB)   │    │   (DB)   │    │   (DB)   │
    └──────────┘    └──────────┘    └──────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ↓                ↓                ↓
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  PDF     │    │ Chunking │    │  FAISS   │
    │Extraction│    │ Service  │    │  Index   │
    └──────────┘    └──────────┘    └──────────┘
                          │
                          ↓
    ┌─────────────────────────────────┐
    │ Vector Embeddings Service       │
    │ (all-MiniLM-L6-v2 model)        │
    └─────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────┐
    │  RAG Pipeline                   │
    │  (Query → Retrieve → Generate)  │
    └─────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────┐
    │   LLM Service (Groq API)        │
    │   Model: llama-3.1-8b-instant   │
    └─────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
IntraDoc_AI/
├── core/                           # Django project settings
│   ├── settings.py                 # Configuration
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI server
│   └── asgi.py                     # ASGI server
│
├── users/                          # User & Authentication app
│   ├── models.py                   # User model, Role enum
│   ├── views.py                    # Auth endpoints
│   ├── permissions.py              # RBAC logic
│   ├── serializers.py              # Data validation
│   └── urls.py                     # User routes
│
├── documents/                      # Document Management app
│   ├── models.py                   # Document model
│   ├── views.py                    # Upload, list endpoints
│   ├── services.py                 # PDF processing
│   ├── serializers.py              # File validation
│   └── urls.py                     # Document routes
│
├── chat/                           # Chat & Conversation app
│   ├── models.py                   # ChatLog model
│   ├── views.py                    # Chat endpoint
│   ├── serializers.py              # Query validation
│   └── urls.py                     # Chat routes
│
├── ai/                             # AI & RAG app
│   ├── embeddings.py               # Sentence-Transformers setup
│   ├── vector.py                   # FAISS operations
│   ├── llm.py                      # Groq LLM interface
│   ├── rag.py                      # RAG pipeline
│   ├── cache.py                    # LLM caching
│   └── management/
│       └── commands/
│           └── rebuild_indexes.py  # Index rebuild command
│
├── frontend/                       # React frontend app
│   ├── src/                        # React source code
│   └── package.json                # Node dependencies
├── docs/                           # Documentation
│   ├── INDEX.md                    # Documentation index
│   ├── ARCHITECTURE.md             # This file
│   ├── step-1-summary.md           # Database models
│   ├── step-2-summary.md           # RBAC system
│   ├── ... (steps 3-18)
│   └── RBAC_SYSTEM.md              # RBAC details
│
├── tests/                          # Test suite
│   ├── test_api.py                 # API tests
│   ├── test_rag_e2e.py             # End-to-end tests
│   └── conftest.py                 # Pytest config
│
├── faiss_indexes/                  # Vector index storage
│   └── *.faiss                     # Index files
│
├── media/                          # Uploaded files
│   ├── documents/
│   │   ├── hr/
│   │   ├── legal/
│   │   ├── accounts/
│   │   └── finance/
│   └── ...
│
├── .env                            # Environment variables
├── .gitignore                      # Git exclusions
├── requirements.txt                # Python dependencies
├── manage.py                       # Django CLI
└── README.md                       # Quick start guide
```

---

## 🔄 Data Flow Diagrams

### Document Upload Flow

```
1. USER UPLOADS PDF
   ├─ Selects file from browser
   ├─ Chooses department
   └─ Clicks "Upload"
         │
         ↓
2. FRONTEND VALIDATION
   ├─ Check file type: .pdf ✓
   ├─ Check file size: < 50MB ✓
   └─ Prepare FormData
         │
         ↓
3. API CALL
   ├─ POST /api/documents/upload/
   ├─ Headers: Authorization Bearer JWT
   └─ Body: FormData(file, department)
         │
         ↓
4. BACKEND VALIDATION
   ├─ Validate JWT token ✓
   ├─ Check user role matches department ✓
   ├─ Verify file is valid PDF ✓
   └─ Check RBAC permissions ✓
         │
         ↓
5. FILE STORAGE
   ├─ Save to: media/documents/{dept}/{filename}
   ├─ Create Document record in DB
   └─ Set is_processed = False
         │
         ↓
6. PDF TEXT EXTRACTION
   ├─ Extract text from all pages
   ├─ Clean formatting, remove noise
   └─ Return raw text
         │
         ↓
7. TEXT CHUNKING
   ├─ Split by sentences/paragraphs
   ├─ Target size: ~300 tokens per chunk
   ├─ Add overlap for context preservation
   └─ Return list of chunks
         │
         ↓
8. EMBEDDING GENERATION
   ├─ Load model: all-MiniLM-L6-v2
   ├─ For each chunk: generate 384-dim vector
   ├─ Store metadata (doc_id, dept, chunk_idx)
   └─ Return embeddings
         │
         ↓
9. FAISS INDEXING
   ├─ Add embeddings to index
   ├─ Save index to disk
   ├─ Update index by department
   └─ Mark as ready for search
         │
         ↓
10. DATABASE UPDATE
    ├─ Set is_processed = True
    ├─ Set chunk_count = N
    ├─ Record upload_date
    └─ Return Document ID
         │
         ↓
11. FRONTEND RESPONSE
    ├─ Status: 201 Created
    ├─ Return: Document ID, filename
    └─ Show: "Upload successful!"
```

### Query Processing Flow

```
1. USER TYPES QUERY
   ├─ Enters question: "What is the leave policy?"
   ├─ Clicks "Send"
   └─ Frontend shows typing indicator
         │
         ↓
2. API CALL
   ├─ POST /api/chat/
   ├─ Headers: Authorization Bearer JWT
   └─ Body: {"query": "What is the leave policy?"}
         │
         ↓
3. AUTHENTICATION
   ├─ Validate JWT token ✓
   ├─ Extract user from token
   ├─ Check user is_active ✓
   └─ Load user role
         │
         ↓
4. CONTEXT RETRIEVAL (Optional)
   ├─ Query recent chat history
   ├─ Load last 3 conversation turns
   ├─ Check if this is a follow-up
   └─ Prepare memory section for LLM
         │
         ↓
5. RBAC DETERMINATION
   ├─ Get user role (e.g., Role.HR)
   ├─ Determine accessible depts: ['hr']
   ├─ Cannot query: legal, accounts, finance
   └─ Store for FAISS filtering
         │
         ↓
6. QUERY EMBEDDING
   ├─ Load embedding model: all-MiniLM-L6-v2
   ├─ Convert query to 384-dim vector
   ├─ Normalize for cosine similarity
   └─ Return embedding
         │
         ↓
7. FAISS SEARCH
   ├─ Search in index with query embedding
   ├─ Filter by accessible departments: ['hr']
   ├─ Return top-5 most similar chunks
   ├─ Each result includes: text, doc_id, chunk_idx, similarity
   └─ Stop if no results found
         │
         ↓
8. CHUNK DEDUPLICATION
   ├─ Remove identical/near-identical chunks
   ├─ Keep metadata: doc_id, filename, dept
   └─ Return unique chunks (usually 1-5)
         │
         ↓
9. PROMPT BUILDING
   ├─ System prompt: Role + instructions
   ├─ Memory section: Recent conversation (if any)
   ├─ Context section: Retrieved chunks (numbered)
   ├─ User prompt: Original query
   └─ Combine into OpenAI format
         │
         ↓
10. LLM API CALL
    ├─ API: Groq (https://api.groq.com/openai/v1)
    ├─ Model: llama-3.1-8b-instant
    ├─ Temperature: 0.7 (balanced creativity)
    ├─ Max tokens: 1024
    ├─ Timeout: 120 seconds
    └─ Send POST request with messages
         │
         ↓
11. LLM RESPONSE GENERATION
    ├─ LLM processes messages
    ├─ Generates response using context
    ├─ Response in English (enforced)
    ├─ Follows format: greeting + bullets + conclusion
    └─ Returns single response (not streamed by API)
         │
         ↓
12. RESPONSE PROCESSING
    ├─ Receive response from Groq API
    ├─ Yield as generator for streaming
    ├─ Frontend receives in real-time
    ├─ Accumulate full response
    └─ Remove typing indicator
         │
         ↓
13. LOGGING
    ├─ Create ChatLog record:
    │  ├─ user: authenticated user
    │  ├─ query: original question
    │  ├─ response: full generated response
    │  ├─ context_chunks: retrieved chunks metadata
    │  └─ timestamp: query time
    ├─ Commit to database
    └─ Audit trail created
         │
         ↓
14. FRONTEND DISPLAY
    ├─ Stop typing indicator
    ├─ Show AI response in chat
    ├─ Display metadata:
    │  ├─ Chunks used: N
    │  ├─ Sources: filenames
    │  └─ Departments searched: [depts]
    ├─ Update chat history
    └─ Ready for next query
         │
         ↓
15. ERROR HANDLING
    If error occurs anywhere:
    ├─ Catch exception
    ├─ Log error with context
    ├─ Return user-friendly message
    ├─ Examples:
    │  ├─ "No documents found..." (0 chunks)
    │  ├─ "LLM service unavailable..." (API error)
    │  └─ "Access denied..." (RBAC violation)
    └─ Show error in chat
```

---

## 🔐 Authentication & RBAC Flow

```
1. REGISTRATION
   ├─ User submits: username, email, password, role
   ├─ Validate: username unique, strong password
   ├─ Hash password with bcrypt (8 rounds)
   ├─ Create User record with role (e.g., Role.HR)
   ├─ Generate JWT tokens (access + refresh)
   └─ Return tokens to frontend
         │
         ↓
2. LOGIN
   ├─ User submits: username, password
   ├─ Query User by username
   ├─ Check password hash matches
   ├─ Extract user role (e.g., Role.HR)
   ├─ Generate JWT access token (60 min expiry)
   ├─ Generate JWT refresh token (7 day expiry)
   └─ Return tokens
         │
         ↓
3. TOKEN STORAGE (Frontend)
   ├─ Store access_token in localStorage
   ├─ Store refresh_token in localStorage
   ├─ Store user role in localStorage
   └─ Attach to Authorization header in requests
         │
         ↓
4. PROTECTED ENDPOINT REQUEST
   ├─ Frontend adds: Authorization: Bearer <access_token>
   ├─ Backend receives request
   ├─ Decode JWT token
   ├─ Validate token signature
   ├─ Check expiration time
   ├─ Extract user_id from token claims
   ├─ Load User from database
   └─ Proceed with request
         │
         ↓
5. RBAC CHECK (Per Request)
   ├─ Determine accessible departments based on role:
   │  ├─ Role.ADMIN → ['hr', 'legal', 'accounts', 'finance']
   │  ├─ Role.HR → ['hr']
   │  ├─ Role.LEGAL → ['legal']
   │  ├─ Role.ACCOUNTS → ['accounts']
   │  └─ Role.FINANCE → ['finance']
   ├─ For document operations: Filter by department
   ├─ For chat queries: Filter FAISS search by dept
   ├─ For upload: Verify user can upload to dept
   └─ Apply restrictions in backend (never trust frontend)
         │
         ↓
6. TOKEN EXPIRATION HANDLING
   ├─ Access token expires after 60 minutes
   ├─ Frontend detects 401 Unauthorized
   ├─ Call: POST /api/users/token/refresh/
   ├─ Send: refresh_token in request body
   ├─ Backend validates refresh token
   ├─ Generate new access_token
   ├─ Return new access_token
   └─ Retry original request with new token
         │
         ↓
7. LOGOUT
   ├─ Frontend clears localStorage:
   │  ├─ access_token
   │  ├─ refresh_token
   │  └─ user_role
   ├─ Redirect to login page
   ├─ Backend doesn't need to do anything
   │  (JWTs are stateless)
   └─ User is logged out
```

---

## 📊 Database Schema

### Users Table

```sql
users (
    id: PK, AutoField
    username: CharField(unique=true)
    password: CharField(hashed)
    email: EmailField
    role: CharField(choices=[ADMIN, HR, LEGAL, ACCOUNTS, FINANCE])
    is_active: BooleanField(default=true)
    is_staff: BooleanField(default=false)
    created_at: DateTimeField(auto_now_add=true)
    updated_at: DateTimeField(auto_now=true)
    
    Indexes:
    - username (unique)
    - role
)
```

### Documents Table

```sql
documents (
    id: PK, AutoField
    file: FileField(upload_to='documents/{department}/')
    filename: CharField
    department: CharField(choices=[hr, legal, accounts, finance])
    uploaded_by: FK → users
    upload_date: DateTimeField(auto_now_add=true)
    is_processed: BooleanField(default=false)
    chunk_count: IntegerField(default=0)
    file_size: BigIntegerField
    
    Indexes:
    - department
    - uploaded_by
    - upload_date
    - is_processed
)
```

### ChatLogs Table

```sql
chat_logs (
    id: PK, AutoField
    user: FK → users
    query: TextField
    response: TextField
    context_chunks: JSONField (stores metadata)
    timestamp: DateTimeField(auto_now_add=true)
    
    Indexes:
    - user_id
    - timestamp
    - user_id + timestamp (compound)
)
```

---

## 🎯 Key Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Django | 4.2 | Backend server |
| **REST API** | Django REST Framework | 3.14+ | API endpoints |
| **Database** | SQLite / PostgreSQL | Latest | Data storage |
| **Authentication** | JWT (SimpleJWT) | 5.2+ | Token auth |
| **Vector Search** | FAISS | Latest | Semantic search |
| **Embeddings** | Sentence-Transformers | 2.2+ | Vector generation |
| **PDF Processing** | pypdf | Latest | PDF text extraction |
| **LLM** | Groq API | Latest | Response generation |
| **Frontend** | React SPA | 18+ | UI |
| **Server** | Gunicorn | Latest | WSGI server |
| **Web Server** | Nginx | Latest | Reverse proxy |
| **Container** | Docker | Latest | Deployment |
| **Testing** | Django TestCase, pytest | Latest | Quality assurance |

---

## ⚡ Performance Characteristics

### Typical Latencies

```
User Login:          < 500ms
Document Upload:     2-5 seconds   (depends on PDF size)
Query Processing:    3-8 seconds   (FAISS search + LLM)
Chat History Load:   < 1 second
Token Refresh:       < 500ms
```

### Scalability

```
Concurrent Users:    100+
Documents:           10,000+
Total Chunks:        1,000,000+
Queries/Hour:        10,000+
```

### Storage

```
SQLite Database:     ~ 100MB (per 10K docs)
FAISS Index:         ~ 1.5GB (per 1M chunks)
Media Files:         Variable (PDFs + backups)
```

---

## 🔒 Security Architecture

### Defense Layers

```
Layer 1: HTTPS/TLS
├─ Encrypt data in transit
├─ SSL certificates (Let's Encrypt)
└─ HSTS headers

Layer 2: Authentication
├─ JWT token validation
├─ Signature verification
├─ Token expiration

Layer 3: Authorization (RBAC)
├─ Role-based access control
├─ Department filtering
├─ Permission checks

Layer 4: Input Validation
├─ File type validation
├─ File size limits
├─ Query input sanitization

Layer 5: Output Encoding
├─ HTML entity escaping
├─ JSON encoding
├─ No raw HTML in responses

Layer 6: API Protection
├─ CORS restrictions
├─ Rate limiting
├─ CSRF protection (if cookies used)

Layer 7: Data Protection
├─ Password hashing (bcrypt)
├─ No plaintext secrets
├─ Secure file permissions
```

---

## 🚀 Deployment Architecture

### Production Stack

```
┌─────────────────────────────────────────────────┐
│          External Users / Browsers              │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │   CloudFlare CDN    │ (Optional)
        │   (SSL, caching)    │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Load Balancer      │
        │  (NGINX, HAProxy)   │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    ┌───▼───┐           ┌───▼───┐
    │ App   │           │ App   │
    │Server │ .........│Server │ (Multiple instances)
    │  #1   │ (session │  #2   │ (horizontal scaling)
    └───┬───┘ sharing) └───┬───┘
        │                  │
        └──────────┬───────┘
                   │
        ┌──────────▼──────────┐
        │  PostgreSQL DB      │ (Replicated)
        │  (Primary/Replica)  │
        └─────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Redis Cache        │ (Session store)
        └─────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Shared Storage     │
        │  (FAISS indexes)    │
        │  (Document files)   │
        └─────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Groq LLM API       │ (External)
        └─────────────────────┘

Supporting Services:
├─ Monitoring: Datadog/New Relic
├─ Logging: ELK Stack/Splunk
├─ Alerting: PagerDuty/Opsgenie
├─ Backup: Daily snapshots
└─ DNS: Route53/CloudFlare
```

---

## 📈 System Monitoring

### Key Metrics

```
Application Metrics:
├─ Request count (total, by endpoint)
├─ Response time (avg, p95, p99)
├─ Error rate (4xx, 5xx)
├─ Success rate
├─ LLM response time
└─ Query success rate

Infrastructure Metrics:
├─ CPU usage
├─ Memory usage
├─ Disk space (DB, media, logs)
├─ Network I/O
├─ Database query time
└─ Cache hit rate

Business Metrics:
├─ Active users
├─ Queries per day
├─ Documents uploaded
├─ Chat history entries
├─ Average satisfaction
└─ ROI calculation
```

---

## 🔄 Backup & Disaster Recovery

### Backup Strategy

```
Database:
├─ Daily snapshots (full)
├─ Hourly backups (incremental)
├─ Retention: 30 days
├─ Location: S3 + local NAS
└─ Test restore: weekly

FAISS Indexes:
├─ Daily backup after rebuild
├─ Can be regenerated from PDFs
├─ Retention: 7 days
└─ Rebuild time: 1-2 hours

Media Files:
├─ Sync to S3 continuously
├─ Retention: Full history
├─ Versioning enabled
└─ Archive old files monthly
```

### Recovery Procedures

```
Database Corruption:
├─ Restore from most recent backup
├─ Verify data integrity
├─ Run consistency checks
└─ Notify users of potential data loss

FAISS Index Loss:
├─ Rebuild from documents
├─ Command: python manage.py rebuild_indexes
├─ Time: ~1-2 hours
└─ No data loss, temporary unavailability

Complete Server Failure:
├─ Restore to new server
├─ Restore database backup
├─ Restore media files
├─ Rebuild FAISS indexes
└─ Run smoke tests
```

---

## 🎓 Architecture Decisions

### Why Django?
✅ Mature, batteries-included framework  
✅ Excellent ORM for database operations  
✅ Built-in admin interface  
✅ Strong security features  
✅ Large community and ecosystem  

### Why FAISS?
✅ Fast vector similarity search  
✅ Handles millions of embeddings  
✅ Low memory footprint  
✅ No external dependencies  
✅ Open source and actively maintained  

### Why Groq?
✅ Free tier available  
✅ Fast inference (8k tokens/sec)  
✅ No self-hosting needed  
✅ Reliable API with SLA  
✅ Good model quality (Llama 3.1)  

### Why JWT?
✅ Stateless (no server-side session storage)  
✅ Scalable to multiple servers  
✅ Mobile-friendly  
✅ Standard industry practice  
✅ Built-in expiration mechanism  

### Why Sentence-Transformers?
✅ Pre-trained embeddings (no training needed)  
✅ Good semantic understanding  
✅ Low computational overhead  
✅ Works with short texts (queries)  
✅ Widely used and proven effective  

---

**This architecture provides scalability, security, and reliability for enterprise document management.**

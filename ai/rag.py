"""
RAG (Retrieval Augmented Generation) Pipeline — Enhanced.

Major improvements over original:
    1. Conversation memory: uses recent chat history for context continuity
    2. Query expansion: reformulates vague queries using conversation context
    3. Better prompt engineering: structured system prompt with role awareness
    4. Relevance scoring feedback: tells user how confident the retrieval is
    5. Chunk deduplication: avoids sending duplicate context to LLM
    6. Configurable top_k based on chunk quality

Orchestrates the full flow:
    1. Load recent conversation history
    2. Determine accessible departments based on user role
    3. Optionally expand query with context from conversation
    4. Retrieve relevant chunks from FAISS
    5. Deduplicate and filter chunks by quality
    6. Build a context-aware prompt with conversation memory
    7. Send to Ollama for response generation
"""

import logging
import re

from users.permissions import get_accessible_departments
from .vector import get_vector_store
from .llm import generate_response, OllamaError

logger = logging.getLogger(__name__)

# Maximum conversation turns to include for context
MAX_MEMORY_TURNS = 3
MAX_BULLETS = 6

# System prompt template
SYSTEM_PROMPT = """You are an intelligent document assistant for an internal enterprise system called "IntraDoc Intelligence".

Your behavior must strictly follow role-based access control, department-based document retrieval, and knowledge boundaries.

---

## 🔐 ROLE-BASED ACCESS CONTROL
* The current user has a role: {role}.
* Administrator has access to ALL departments and cross-department insights.
* Non-admin users (HR, Finance, Legal) can ONLY access their respective department documents.

---

## 📂 DEPARTMENT SCOPING
* The user has selected the "{department}" department for this query.
* If "GRAPH" is selected:
    - This is a global knowledge layer.
    - You MUST retrieve and combine relevant information from ALL departments (HR, Finance, Legal).
    - Your goal is to provide a UNIFIED profile of the entity being queried.
    - If the user asks for details about a person, you MUST include their Role (HR), Salary/Compensation (Finance), and Contract Terms (Legal) in ONE response.
    - NEVER say "not available" if the information exists in ANY of the retrieved excerpts.

---

## 🧩 GRAPH KNOWLEDGE BEHAVIOR
* The "Graph" acts as a unified knowledge base across all documents.
* It connects entities (e.g., people, salaries, contracts, roles).
* Never mix data from different individuals with the same name. Ensure all retrieved information refers to the SAME entity.
* If information is found in different departments for the same entity, MERGE it into a single factual summary.

---

## 🌐 LANGUAGE RULE
* **PRIMARY LANGUAGE: ENGLISH** - This is mandatory.
* ALWAYS respond EXCLUSIVELY in English.
* NEVER respond in any other language (Kannada, Hindi, Tamil, Telugu, etc.)
* If source documents contain non-English text, TRANSLATE key points to English.
* Summarize all content in fluent, professional English.
* Do NOT code-switch or mix languages.

---

## 🚫 NO HALLUCINATION POLICY
* Only answer using retrieved document data.
* If information is not found in ANY department during a GRAPH query, only then say: "The requested information is not available in the selected department."
* Do NOT guess or fabricate answers.

---

## 📌 RESPONSE STYLE
* **MANDATORY SUGGESTIONS**: At the very end of every response, you MUST provide exactly 3 relevant follow-up questions for the user. Format them on a single line exactly like this: `[[Suggestions: Question 1? | Question 2? | Question 3?]]`
* Be concise and factual. Present as a complete profile in Graph mode.
* Do not include irrelevant information.
* Maximum {max_bullets} bullet points if formatting as a list.
"""

# User message template — question FIRST so the model focuses on it
USER_PROMPT = """Question: {query}

{memory_section}
Below is reference material. Your task:
1. Find the information that answers the question
2. Summarize it in ENGLISH ONLY - do not use any other language
3. If documents contain non-English text, translate it to English
4. Be concise and factual

{context}

CRITICAL: Always respond in ENGLISH. No exceptions."""

# When there's conversation history
MEMORY_SECTION_TEMPLATE = """RECENT USER INTENT (for continuity — do NOT treat this as document context):
{memory}
---"""

NO_CONTEXT_RESPONSE = "The requested information is not available in the selected department."
PERMISSION_DENIED_RESPONSE = "You do not have permission to access this information."


def _build_memory_section(history):
    if not history:
        return ""
    memory_parts = []
    # history comes from frontend as a list of strings (queries).
    for i, q in enumerate(history, 1):
        memory_parts.append(f"{i}. {q}")
    memory_text = "\n\n".join(memory_parts)
    return MEMORY_SECTION_TEMPLATE.format(memory=memory_text)


def _expand_query(query, history):
    if not history:
        return query
    follow_up_indicators = [
        'it', 'this', 'that', 'those', 'these', 'they', 'them',
        'what about', 'how about', 'and the', 'also', 'more about',
        'tell me more', 'explain', 'elaborate', 'continue',
    ]
    query_lower = query.lower().strip()
    is_followup = (
        len(query.split()) <= 6 or
        any(query_lower.startswith(ind) for ind in follow_up_indicators) or
        any(ind in query_lower for ind in follow_up_indicators)
    )
    if is_followup and history:
        last_query = history[-1]
        expanded = f"{last_query} {query}"
        logger.info(f"Query expanded: '{query}' -> '{expanded}'")
        return expanded
    return query


def _is_document_listing_query(query):
    q = query.lower().strip()
    triggers = [
        'what are the docs',
        'what docs are available',
        'what documents are available',
        'list documents',
        'list docs',
        'available documents',
        'available docs',
        'show documents',
        'show docs',
    ]
    return any(t in q for t in triggers)


def _build_document_listing_response(user):
    from documents.models import Document

    departments = get_accessible_departments(user)
    docs = (
        Document.objects
        .filter(department__in=departments)
        .order_by('-upload_date')
        .values_list('filename', flat=True)
    )

    unique = []
    seen = set()
    for name in docs:
        key = name.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(name.strip())
        if len(unique) >= MAX_BULLETS:
            break

    if not unique:
        return (
            "Here's what I found:\n\n"
            "- No documents are currently available in your department access scope.\n"
            "- Upload a PDF to start querying."
        )

    lines = ["Here's what I found:", ""]
    lines.extend(f"- {name}" for name in unique)
    return "\n".join(lines)


def _sanitize_llm_response(text):
    if not text:
        return NO_CONTEXT_RESPONSE

    # Preserve suggestion block if present: [[Suggestions: ...]]
    suggestion_block = ""
    suggestion_match = re.search(r'\[\[Suggestions:.*?\]\]', text, re.IGNORECASE)
    if suggestion_match:
        suggestion_block = suggestion_match.group(0)
        text = text.replace(suggestion_block, "").strip()

    # Remove transcript-like noise lines.
    cleaned = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(('user:', 'assistant:', 'question:', 'context:')):
            continue
        if lowered in {"here's what i found", "here's what i found:"}:
            continue
        cleaned.append(line)

    # Extract bullets if present; otherwise split into sentence-like chunks.
    bullet_items = []
    for line in cleaned:
        line = re.sub(r'^\s*[-*•]\s*', '', line).strip()
        line = re.sub(r'^\d+[.)]\s*', '', line).strip()
        if not line:
            continue
        bullet_items.append(line)

    if not bullet_items:
        sentence_candidates = re.split(r'(?<=[.!?])\s+', text.strip())
        bullet_items = [s.strip() for s in sentence_candidates if s.strip()]

    # Deduplicate and cap.
    unique_items = []
    seen = set()
    for item in bullet_items:
        key = re.sub(r'\s+', ' ', item).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique_items.append(item.rstrip('. '))
        if len(unique_items) >= MAX_BULLETS:
            break

    if not unique_items:
        return NO_CONTEXT_RESPONSE

    response_lines = ["Here's what I found:", ""]
    response_lines.extend(f"- {item}" for item in unique_items)
    
    # Append the suggestion block back at the very end
    final_response = "\n".join(response_lines)
    if suggestion_block:
        final_response += f"\n\n{suggestion_block}"
        
    return final_response


def _deduplicate_chunks(chunks):
    seen = set()
    unique = []
    for chunk in chunks:
        key = chunk['text'][:100].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(chunk)
    return unique


def get_relevant_chunks(query, user, search_departments, top_k=5):
    vector_store = get_vector_store()
    logger.info(
        f"Retrieving chunks for user '{user.username}' (role={user.role}) "
        f"from departments: {search_departments}"
    )
    results = vector_store.search(query, search_departments, top_k=top_k)
    results = _deduplicate_chunks(results)
    logger.info(f"Found {len(results)} relevant chunks (after dedup)")
    return results


def build_messages(query, chunks, user_role, requested_department, memory_section=""):
    """
    Build a structured messages array for the OpenAI/Groq API.
    """
    if not chunks:
        return None

    # Combine chunk texts into plain context — NO headers to prevent LLM echoing
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        # Plain numbered text only — no department/relevance labels
        context_parts.append(f"--- Excerpt {i} ---\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT.format(
            role=user_role, 
            department=requested_department.upper() if requested_department else "ALL",
            max_bullets=MAX_BULLETS
        )
    }

    user_message = {
        "role": "user",
        "content": USER_PROMPT.format(
            memory_section=memory_section,
            context=context,
            query=query
        )
    }

    return [system_message, user_message]


def process_query(query, user, requested_department="", history=None):
    """
    Execute the full RAG pipeline for a user query.
    """
    if history is None:
        history = []
        
    logger.info(f"Processing query from {user.username}: '{query[:100]}...' for dept: {requested_department}")

    # Step 0: RBAC & Department Validation
    accessible_depts = get_accessible_departments(user)
    requested_dept_lower = requested_department.lower().strip()
    
    is_admin = user.role == 'ADMINISTRATOR' or user.role == 'ADMIN'
    
    # Validation logic
    search_departments = []
    if requested_dept_lower == "graph":
        if not is_admin:
            def denied_generator():
                yield PERMISSION_DENIED_RESPONSE
            return {'response': denied_generator(), 'chunks_used': [], 'error': None}
        # Admin accessing graph: search all accessible departments
        search_departments = accessible_depts
    elif requested_dept_lower:
        from users.permissions import can_access_department
        if not can_access_department(user, requested_dept_lower):
            def denied_generator():
                yield PERMISSION_DENIED_RESPONSE
            return {'response': denied_generator(), 'chunks_used': [], 'error': None}
            
        # Map the requested department to the actual database namespace
        actual_dept = 'accounts' if requested_dept_lower == 'finance' else requested_dept_lower
        search_departments = [actual_dept]
    else:
        # Fallback if no department specified
        search_departments = accessible_depts

    if _is_document_listing_query(query):
        def docs_generator():
            yield _build_document_listing_response(user)
        return {
            'response': docs_generator(),
            'chunks_used': [],
            'error': None,
        }

    import time
    start_time = time.time()

    # Step 1: Use passed history (from Firestore frontend)
    memory_section = _build_memory_section(history)

    # Step 2: Expand query for follow-ups
    search_query = _expand_query(query, history)

    # Step 3: Retrieve relevant chunks
    retrieval_start = time.time()
    # For Graph mode, we increase top_k to ensure we get results from multiple departments
    top_k = 12 if requested_dept_lower == "graph" else 5
    chunks = get_relevant_chunks(search_query, user, search_departments, top_k=top_k)
    retrieval_time = time.time() - retrieval_start

    if not chunks:
        logger.info("No relevant chunks found")

        def no_context_generator():
            yield NO_CONTEXT_RESPONSE

        return {
            'response': no_context_generator(),
            'chunks_used': [],
            'error': None,
            'metrics': {
                'retrieval_time': round(retrieval_time, 3),
                'total_time': round(time.time() - start_time, 3),
                'chunk_count': 0
            }
        }

    # Step 4: Build structured prompt messages with memory
    messages = build_messages(query, chunks, user.role, requested_dept_lower, memory_section)

    # Step 5: Generate response from LLM
    try:
        base_generator = generate_response(messages)

        def sanitized_generator():
            for chunk in base_generator:
                yield _sanitize_llm_response(chunk)

        response_generator = sanitized_generator()
        return {
            'response': response_generator,
            'chunks_used': chunks,
            'error': None,
            'metrics': {
                'retrieval_time': round(retrieval_time, 3),
                'total_time': round(time.time() - start_time, 3),
                'chunk_count': len(chunks)
            }
        }

    except OllamaError as e:
        error_msg = str(e)
        logger.error(f"RAG pipeline LLM error: {error_msg}")

        def generate_error():
            yield f"I found relevant documents but couldn't generate a response. Error: {error_msg}"

        return {
            'response': generate_error(),
            'chunks_used': chunks,
            'error': error_msg,
        }

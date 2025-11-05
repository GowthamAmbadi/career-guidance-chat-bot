# Feature Implementation Map

This document shows where each feature from `CAREER GUIDANCE.md` is implemented.

## ✅ All 6 Features Implemented

### 1. **Resume/CV Parsing** ✓
**Location:** `app/routers/resume.py` + `app/services/resume_parser.py`

**Endpoint:** `POST /resume/parse`

**Implementation:**
- **Router:** ```9:53:app/routers/resume.py```
- **Service Logic:** ```8:56:app/services/resume_parser.py```
- **Uses:** LLM (Gemini) + keyword matching for skill extraction
- **Returns:** `{name, email, experience, skills}`

**How to use:**
```bash
POST /resume/parse
Body (form-data): resume_text="..." OR file=upload
```

---

### 2. **Career Path Recommendation** ✓
**Location:** `app/routers/reco.py` + `app/llm/chains.py`

**Endpoint:** `GET /recommend/careers?user_id=...`

**Implementation:**
- **Router:** ```10:58:app/routers/reco.py```
- **LLM Chain:** ```14:26:app/llm/chains.py```
- **Uses:** User profile (skills + experience) → Gemini LLM → Career recommendations
- **Returns:** `{careers: [{title, description, salary_range, outlook}]}`

**How to use:**
```bash
GET /recommend/careers?user_id=your-user-id
```

---

### 3. **Skill Gap Analysis** ✓
**Location:** `app/routers/analysis.py` + `app/llm/chains.py`

**Endpoint:** `POST /analysis/skill-gap`

**Implementation:**
- **Router:** ```10:42:app/routers/analysis.py```
- **LLM Chain:** ```29:34:app/llm/chains.py```
- **Uses:** Semantic comparison via Gemini LLM (not just keyword matching)
- **Returns:** `{matched: [...], gap: [...]}`

**How to use:**
```bash
POST /analysis/skill-gap
Body: {
  "user_skills": ["Python", "SQL"],
  "job_skills": ["Python", "Machine Learning", "Statistics"]
}
```

---

### 4. **Job Fit Analyzer** ✓
**Location:** `app/routers/analysis.py` + `app/llm/chains.py`

**Endpoint:** `POST /analysis/job-fit`

**Implementation:**
- **Router:** ```45:82:app/routers/analysis.py```
- **LLM Chain:** ```37:42:app/llm/chains.py```
- **Uses:** Gemini LLM to analyze profile vs job description
- **Returns:** `{fit_score: 0-100, rationale: "..."}`

**How to use:**
```bash
POST /analysis/job-fit
Body: {
  "profile": {...},
  "job_description": "..."
}
```

---

### 5. **Goal Setting & Tracking** ✓
**Location:** `app/routers/goals.py`

**Endpoints:**
- `POST /goals/?user_id=...` - Create goal
- `GET /goals/?user_id=...` - List goals

**Implementation:**
- **Create Goal:** ```10:24:app/routers/goals.py```
- **List Goals:** ```27:39:app/routers/goals.py```
- **Database:** Supabase `goals` table
- **Returns:** Goal objects with `{goal_id, user_id, goal_text, status}`

**How to use:**
```bash
POST /goals/?user_id=...
Body: {"goal_text": "Learn Python"}

GET /goals/?user_id=...
```

---

### 6. **Knowledge Grounding (RAG)** ✓
**Location:** `app/routers/rag.py` + `app/services/rag_service.py`

**Endpoint:** `POST /rag/query`

**Implementation:**
- **Router:** ```13:37:app/routers/rag.py```
- **Service:** ```11:130:app/services/rag_service.py```
- **Flow:**
  1. Query → Embedding (sentence-transformers)
  2. Vector search in `career_data` table (pgvector)
  3. Retrieve top 5 relevant documents
  4. Generate answer with Gemini LLM using retrieved context
- **Returns:** `{answer: "...", sources: [...]}`

**How to use:**
```bash
POST /rag/query
Body: {"query": "What is the job outlook for Data Scientists?"}
```

---

## Additional Feature: Chat Interface

**Location:** `app/routers/chat.py` + `static/index.html`

**Endpoint:** `POST /chat/`

**Frontend:** `http://localhost:8000/` (Chat UI)

**Implementation:**
- **Router:** ```13:71:app/routers/chat.py```
- **Frontend:** ```1:250:static/index.html```
- **Features:** Conversation history, RAG integration, typing indicators

---

## Database Schema

**Location:** `database/migrations/001_create_tables.sql`

**Tables:**
- `profiles` - User profiles (from resume parsing)
- `goals` - User goals
- `career_data` - Vector store for RAG (pgvector)

---

## Supporting Services

- **Embeddings:** `app/llm/embeddings.py` - sentence-transformers for RAG
- **Gemini LLM:** `app/llm/gemini_client.py` - LLM configuration
- **Chains:** `app/llm/chains.py` - LangChain chains for each feature
- **Supabase Client:** `app/clients/supabase_client.py` - Database connection

---

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with all endpoints.


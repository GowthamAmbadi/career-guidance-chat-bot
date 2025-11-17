# Career Guidance API

FastAPI + LangChain + Supabase (pgvector) backend for AI career guidance chatbot.

## Features

1. **Resume/CV Parsing** - Extract structured data (name, email, experience, skills) from resume text
2. **Career Path Recommendations** - AI-powered career suggestions based on user profile
3. **Skill Gap Analysis** - Semantic comparison of user skills vs job requirements
4. **Job Fit Analyzer** - Score (0-100) and rationale for job match
5. **Goal Setting & Tracking** - Create and manage career development goals
6. **RAG (Knowledge Grounding)** - Answer career questions using vector search over knowledge base

## Quickstart

### 1. Prerequisites

- Python 3.11+ 
- Supabase account with pgvector enabled
- OpenAI API key

### 2. Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret
DATABASE_URL=your_database_url  # Optional, for direct DB access
OPENAI_API_KEY=your_openai_api_key
CORS_ORIGINS=https://dev.my.skillcapital.ai,http://localhost:3000
LOG_LEVEL=info
```

### 4. Database Setup

Run the SQL migrations in Supabase SQL Editor:

1. Go to your Supabase project → SQL Editor
2. Run `database/migrations/001_create_tables.sql`
3. This creates: `profiles`, `goals`, `career_data` tables with pgvector support

### 5. Seed Career Data (Optional)

```bash
python scripts/seed_career_data.py
```

This populates the `career_data` table with sample career information and embeddings.

### 6. Run Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at: `http://localhost:8000`

API docs available at: `http://localhost:8000/docs`

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Resume Parsing
- `POST /resume/parse` - Parse resume text or file
  - Body: `resume_text` (string) or `file` (upload)
  - Returns: `{name, email, experience, skills}`

### Profiles
- `POST /profiles/upsert` - Create/update user profile
  - Query: `user_id` (string)
  - Body: `ResumeParsed` object
  - Returns: `Profile` object

### Goals
- `POST /goals/` - Create a new goal
  - Query: `user_id` (string)
  - Body: `{goal_text: string}`
  - Returns: `Goal` object

- `GET /goals/` - List user goals
  - Query: `user_id` (string)
  - Returns: `List[Goal]`

### Career Recommendations
- `GET /recommend/careers` - Get career path recommendations
  - Query: `user_id` (string)
  - Returns: `{careers: [...]}`

### Analysis
- `POST /analysis/skill-gap` - Semantic skill gap analysis
  - Body: `{user_skills: [...], job_skills: [...]}`
  - Returns: `{matched: [...], gap: [...]}`

- `POST /analysis/job-fit` - Job fit score analysis
  - Body: `{profile: Profile, job_description: string}`
  - Returns: `{fit_score: int (0-100), rationale: string}`

### RAG Query
- `POST /rag/query` - Query career knowledge base
  - Body: `{query: string}`
  - Returns: `{answer: string, sources: [...]}`

## Project Structure

```
.
├── app/
│   ├── clients/          # Supabase client
│   ├── llm/              # LLM chains and prompts
│   ├── models/           # Pydantic schemas
│   ├── routers/          # FastAPI route handlers
│   ├── services/         # Business logic
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── database/
│   └── migrations/       # SQL migration scripts
├── scripts/
│   └── seed_career_data.py  # Script to seed career data
├── requirements.txt
└── README.md
```

## Tech Stack

- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **OpenAI GPT** - LLM for generation (gpt-4o-mini)
- **OpenAI** - Embeddings API for vector embeddings
- **Supabase** - Database (PostgreSQL + pgvector)
- **pdfplumber/PyPDF2** - PDF parsing for resumes
- **python-docx** - DOCX parsing for resumes

## Notes

- Ensure pgvector extension is enabled in Supabase
- For production, optimize vector search using the `match_career_data` RPC function
- Service role key is used server-side only (never expose to client)
- RLS policies are set up for user data isolation

## Development

- API documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`



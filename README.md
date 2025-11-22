# 🚀 Career Coach AI
FastAPI + LangChain + Supabase (pgvector) backend powering an AI-based career guidance chatbot.

This backend helps users explore career paths, analyze their skills, and receive personalized AI-driven guidance.

---

# ⭐ Features

### ✅ Resume/CV Parsing  
Extracts:
- Name  
- Email  
- Skills  
- Work experience  

### ✅ Career Path Recommendations  
AI suggests suitable career paths based on the user's profile.

### ✅ Skill Gap Analysis  
Compares user skills with job requirements and identifies:
- Matched skills  
- Missing skills  

### ✅ Job Fit Analyzer  
Provides:
- Job match score (0–100)  
- Reasoning for the score  

### ✅ Goal Setting & Tracking  
Users can maintain and track their career development goals.

### ✅ RAG Career Q&A  
Uses embeddings + vector search to answer career-related questions accurately.

---

# 🛠 Quickstart Guide

## 1️⃣ Prerequisites
- Python **3.11+**
- **Supabase** project with `pgvector` enabled
- **OpenAI API Key**

---

## 2️⃣ Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

<img width="1919" height="977" alt="image" src="https://github.com/user-attachments/assets/239de26f-c683-4dd3-bcc6-da6f4c57df81" />

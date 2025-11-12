# **PROJECT BRIEF: AI CAREER GUIDANCE CHATBOT**

## **1\. Project Mission**

To build a comprehensive, personalized, and AI-powered career coach. This chatbot will act as a long-term partner for users, guiding them from initial resume parsing and self-discovery to specific skill-gap analysis and long-term goal tracking.

The core of this project is to create an **intelligent, data-driven system** using LangChain, with all knowledge and user data securely managed by Supabase.

## **2\. Core Features & Functional Requirements**

The chatbot's functionality is built on six key, interconnected features:

1. **Resume/CV Parsing:**  
   * **User Action:** User pastes their resume text into the chat.  
   * **System Action:** The bot identifies this as resume text.  
   * **Outcome:** The text is parsed to extract a structured JSON object containing: name, email, experience (summary string), and skills (a list of strings). This JSON is used to create/update the user's profile in the database.  
2. **Career Path Recommendation:**  
   * **User Action:** Asks a question like, "What career paths are good for me?"  
   * **System Action:** Uses the user's stored skills and experience from their profile as context.  
   * **Outcome:** The bot suggests a list of relevant career paths. For each path, it must be able to provide detailed information on demand (Salary, Day-to-day, Skills, Outlook).  
3. **Skill Gap Analysis:**  
   * **User Action:** Selects a target career (e.g., "Data Scientist").  
   * **System Action:** The bot compares the user's skills list (from their profile) against the known *required skills* for the target job. This comparison **must be semantic**, not just 1-to-1 keyword matching.  
   * **Outcome:** The bot generates a clear report showing:  
     * **Skills You Have:** (e.g., Python)  
     * **Skills to Develop (The Gap):** (e.g., Machine Learning, Statistics)  
     * **Related Skills:** (e.g., "Your 'Tableau' skill is a good foundation for 'Data Visualization'").  
4. **Job Fit Analyzer:**  
   * **User Action:** Pastes a full job description into the chat.  
   * **System Action:** The bot performs a semantic analysis of the user's entire profile (experience \+ skills) against the provided job description.  
   * **Outcome:** The bot generates a "fit score" (e.g., "You are an 80% fit for this role") and provides a brief rationale, highlighting key strengths and major gaps.  
5. **Goal Setting & Tracking:**  
   * **User Action:** Gives a command like, "Help me set a goal to learn Python."  
   * **System Action:** The bot identifies the intent to create a goal.  
   * **Outcome:** A new entry is created in the goals table in Supabase, linked to the user's ID. The bot confirms the goal is set and can retrieve/list active goals on request.  
6. **Knowledge Grounding (RAG):**  
   * **User Action:** Asks a general knowledge question (e.g., "What is the job outlook for BI Architects in 2025?").  
   * **System Action:** This is the core RAG (Retrieval-Augmented Generation) flow. The system will:  
     1. **Retrieve:** Convert the user's query into an embedding and search the career\_data vector table in Supabase for the most relevant documents.  
     2. **Augment:** Pass the *content* of these retrieved documents as context, along with the user's original query, to the LLM.  
     3. **Generate:** The LLM generates an answer based *only* on the provided context, ensuring it's fresh and data-driven.  
   * **Outcome:** The user receives an accurate, up-to-date answer grounded in our own knowledge base.

## **3\. Technical Architecture & Stack**

This project will be built using a modern, AI-native stack.

* **Orchestrator:** **LangChain (Python)**  
  * Used to create all logic chains, manage prompts, and connect all other services (LLM, Database, Tools).  
* **Backend Framework:** **FastAPI (Python)**  
  * Will serve the LangChain application as a set of robust API endpoints. A frontend (e.s., React, Vue, HTML) will interact with these endpoints.  
* **Database (SQL \+ Vector):** **Supabase**  
  * **Authentication:** Manages user identity.  
  * **SQL Tables:** Stores structured user data (profiles, goals).  
  * **Vector Store (pgvector):** Stores embeddings for all our RAG knowledge (career\_data).  
* **AI Models:**  
  * **LLM (Generation):** **OpenAI GPT** (via API). Used by LangChain for final response generation.  
  * **Embedding Model:** OpenAI Embeddings API (text-embedding-3-small). Used to generate embeddings for RAG and semantic similarity tasks.  
* **Core Python Libraries:**  
  * langchain, langchain-community, langchain-openai  
  * fastapi, uvicorn  
  * supabase-client  
  * pdfplumber, PyPDF2, python-docx: For resume parsing from PDF/DOCX files.  
  * openai: For embeddings (text-embedding-3-small) and LLM generation (gpt-4o-mini).

## **4\. Supabase Database Schema**

#### **Table: profiles**

Stores the user's core information, populated by the resume parser.  
| Column | Type | Notes |  
| :--- | :--- | :--- |  
| user\_id | uuid | Primary Key. Foreign Key to auth.users.id. |  
| name | text | e.g., "Jane Doe" |  
| email | text | e.g., "jane.doe@example.com" |  
| experience\_summary | text | A concise summary of work history. |  
| skills | jsonb | A JSON list of skill strings, e.g., \["Python", "SQL", "Tableau"\]. |  
| updated\_at | timestampz | default now() |

#### **Table: goals**

Stores the user-defined development goals.  
| Column | Type | Notes |  
| :--- | :--- | :--- |  
| goal\_id | uuid | Primary Key. default gen\_random\_uuid() |  
| user\_id | uuid | Foreign Key to profiles.user\_id. |  
| goal\_text | text | e.g., "Learn Machine Learning" |  
| status | text | e.g., "active", "completed". default 'active' |  
| created\_at | timestampz | default now() |

#### **Table: career\_data (for RAG)**

The vector store for all our knowledge.  
| Column | Type | Notes |  
| :--- | :--- | :--- |  
| doc\_id | uuid | Primary Key. default gen\_random\_uuid() |  
| career\_title | text | e.g., "Data Scientist" |  
| content\_chunk | text | The raw text of the career info, skill list, or salary data. |  
| embedding | vector | The pgvector embedding of the content\_chunk. |

## **5\. Key AI Prompts (System Prompts)**

1. **Main System Prompt (Global Persona):**"You are 'CareerCore', an expert AI Career Guidance Coach. Your tone is professional, encouraging, supportive, and data-driven. You are a partner in the user's career journey. Do not make up information. If you do not know an answer, say so. Ground your answers in the context provided."  
2. **Resume Parser Tool Prompt:**"You are an automated HR text-parsing tool. The user will provide raw text from a resume. Extract the user's full name, email address, a concise summary of their work experience, and a list of their skills. Respond *only* with a valid JSON object in this exact format: {\\"name\\": \\"...\\", \\"email\\": \\"...\\", \\"experience\\": \\"...\\", \\"skills\\": \[...\]}"  
3. **Skill Gap Analyst Tool Prompt:**"You are a skill gap analyst. You will be given two JSON lists: user\_skills and job\_skills. Your task is to compare them semantically and return a JSON object identifying which skills the user has and which they are missing. Format: {\\"matched\\": \[...\], \\"gap\\": \[...\]}"  
4. **Job Fit Analyst Tool Prompt:**"You are an expert recruiter and talent assessor. You will be given a user's profile (as JSON) and a job\_description (as text). Perform a detailed analysis and return a JSON object with a fit\_score (0-100) and a rationale (a brief explanation of your reasoning)."
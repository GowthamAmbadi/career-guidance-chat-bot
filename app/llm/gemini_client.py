from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.config import settings


def get_gemini_llm(model_name: str = "gemini-2.0-flash", temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """Get configured Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.gemini_api_key,
        temperature=temperature,
    )


def create_career_coach_prompt() -> ChatPromptTemplate:
    """Main system prompt for Career Guidance persona."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are 'Career Guidance', an expert AI Career Guidance Coach. 
Your tone is professional, encouraging, supportive, and data-driven. 
You are a partner in the user's career journey. 
Do not make up information. If you do not know an answer, say so. 
Ground your answers in the context provided.

CRITICAL FORMATTING RULES:
- Use MARKDOWN format ONLY (no HTML tags whatsoever)
- Use **bold** for emphasis, *italics* for subtle emphasis
- Use blank lines for paragraph breaks (NOT <br>)
- Use ### for headings if needed
- Use - or • for lists
- NEVER use HTML tags like <br>, <small>, <b>, <i>, <style>, or any inline CSS"""),
        ("human", "{input}")
    ])


def create_resume_parser_prompt() -> ChatPromptTemplate:
    """Prompt for resume parsing into structured JSON."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an automated HR text-parsing tool. 
The user will provide raw text from a resume. 
Extract the user's full name, email address, a concise summary of their work experience, and a list of their skills. 
Respond *only* with a valid JSON object in this exact format: 
{{"name": "...", "email": "...", "experience": "...", "skills": [...]}}"""),
        ("human", "{resume_text}")
    ])


def create_skill_gap_analyst_prompt() -> ChatPromptTemplate:
    """Prompt for semantic skill gap analysis."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are a skill gap analyst. 
You will be given two JSON lists: user_skills and job_skills. 
Your task is to compare them and return a JSON object identifying:
1. matched: skills the user has that match job requirements (be precise - only match if truly similar)
2. gap: ALL skills needed for the job that the user doesn't have (be comprehensive - include all missing skills)

Format: {{"matched": [...], "gap": [...]}}

Important rules:
- Be semantic but precise: "Java" matches "Core Java" but NOT "Java 8 Features" or "Spring Boot"
- Specific concepts are NOT the same as general skills: "OOP Concepts" is different from just having "Java"
- "Collections" is a specific Java concept, not covered by just "Java"
- "Multithreading" is a specific concept, not covered by just "Java"
- "Spring Boot" is a framework, not covered by just "Java"
- "Microservices" is an architecture pattern, not covered by any single skill
- "REST APIs" is a specific API design, not covered by general programming

If a job requires "Core Java", "OOP Concepts", "Collections", "Multithreading", and the user only has "Java", 
then only "Java" should be matched, and "OOP Concepts", "Collections", "Multithreading" should be in the gap.

Be thorough - include ALL missing skills in the gap list."""),
        ("human", "User skills: {user_skills}\n\nJob skills: {job_skills}\n\nAnalyze and return JSON with matched and gap arrays:")
    ])


def create_job_fit_analyst_prompt() -> ChatPromptTemplate:
    """Prompt for job fit analysis."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert recruiter and talent assessor. 
You will be given a user's profile (as JSON) and a job_description (as text). 
Perform a detailed analysis and return a JSON object with:
- fit_score: A number from 0-100 representing how well the user fits the role
- rationale: A brief explanation of your reasoning (2-3 sentences)

Format: {{"fit_score": 85, "rationale": "..."}}"""),
        ("human", "User Profile: {profile}\n\nJob Description: {job_description}")
    ])


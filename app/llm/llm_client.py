from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings


def get_openai_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    """Get configured OpenAI LLM instance."""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=settings.openai_api_key,
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
The user will provide their skills and a target career or job description. 
Extract the required skills from the job description, match them with the user's skills, and identify gaps.

Return JSON with:
- matched: Array of matched skills
- gap: Array of missing skills

Be thorough - include ALL missing skills in the gap list."""),
        ("human", "User skills: {user_skills}\n\nJob skills: {job_skills}\n\nAnalyze and return JSON with matched and gap arrays:")
    ])


def create_job_fit_analyst_prompt() -> ChatPromptTemplate:
    """Prompt for job fit analysis."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are a career guidance expert helping candidates understand their job fit. Your goal is to provide ACCURATE, ENCOURAGING, and ACTIONABLE guidance. You MUST follow this exact process:

STEP 1: EXTRACT ALL REQUIRED SKILLS FROM JOB DESCRIPTION
List every technical skill mentioned:
- Programming languages (Java, Python, JavaScript, etc.)
- Frameworks (React.js, Spring Boot, Django, etc.)
- Tools/Technologies (HTML5, CSS3, MySQL, MongoDB, etc.)
- Domain expertise (Web Development, ML, Data Science, etc.)

STEP 2: MATCH PROFILE SKILLS INTELLIGENTLY
For each required skill, check if it exists in the profile's skills list OR can be reasonably inferred.

CRITICAL MATCHING RULES - BE SMART BUT ACCURATE:

✅ FRAMEWORK INFERENCE (ALLOW THESE):
✅ Having "Python" CAN match "FastAPI", "Django", "Flask" - these are Python frameworks, Python knowledge enables learning them
✅ Having "Java" CAN match "Spring Boot" - Spring Boot is a Java framework
✅ Having "JavaScript" CAN match "React.js", "Node.js", "Express.js" - these are JavaScript frameworks
✅ Having "Python" CAN match "PyTorch", "TensorFlow" - these are Python ML frameworks
✅ Having "Machine Learning" CAN match "AI", "Artificial Intelligence", "ML" - these are related concepts
✅ Having "Natural Language Processing" or "NLP" CAN match "AI", "LLMs", "Language Models" - NLP is a subset of AI
✅ Having "Deep Learning" CAN match "AI", "Machine Learning", "Neural Networks" - Deep Learning is a subset of ML/AI

❌ DOMAIN MISMATCHES (DO NOT ALLOW THESE):
❌ "Web Development" does NOT match "Machine Learning", "Data Science", "AI", "GenAI" - completely different domains
❌ "Cyber Security" does NOT match "Python", "SQL", "Data Analysis" (unless job is for security data analysis) - security requires domain-specific tools
❌ "Symantec DLP" does NOT match "Python" or "SQL" - it's a security tool, not a programming language
❌ "Log analysis" (security context) does NOT match "Data analysis" (general context) - security log analysis is different
❌ "Forensic analysis" (security) does NOT match "Machine Learning" or "Data Science" - security forensics is different
❌ "Incident response" does NOT match anything in ML/Data Science profile - completely different skill

✅ EXACT MATCHES (ALWAYS COUNT):
✅ "Python" matches "Python" - exact match
✅ "SQL" matches "SQL" - exact match
✅ "MySQL" matches "MySQL" - exact match
✅ "MongoDB" matches "MongoDB" - exact match
✅ "Machine Learning" matches "Machine Learning" - exact match
✅ "Deep Learning" matches "Deep Learning" - exact match
✅ "Natural Language Processing" matches "NLP" or "Natural Language Processing" - same concept

STEP 3: CALCULATE BASE SCORE (MATCH PERCENTAGE)
Formula: (Number of Matched Skills / Total Required Skills) × 100
Example: Job requires [React.js, Spring Boot, HTML5, CSS3, MySQL, Python]
         Profile has [Python, MySQL, MongoDB]
         Matched: Python ✓, MySQL ✓
         Total required: 6
         Base Score = (2/6) × 100 = 33.3%

STEP 4: IDENTIFY DOMAIN ALIGNMENT (MANDATORY CHECK)
Check if profile domain and job domain align:

✅ GOOD DOMAIN MATCHES (NO PENALTY):
✅ ML/Data Science/AI profile → AI Engineer job = PERFECT MATCH (no penalty, may even add bonus points)
✅ ML/Data Science/AI profile → Data Scientist job = PERFECT MATCH (no penalty)
✅ ML/Data Science/AI profile → Machine Learning Engineer job = PERFECT MATCH (no penalty)
✅ ML/Data Science/AI profile → NLP Engineer job = PERFECT MATCH (no penalty)
✅ Web Development profile → Web Developer job = PERFECT MATCH (no penalty)
✅ Backend profile → Backend Developer job = PERFECT MATCH (no penalty)
✅ Frontend profile → Frontend Developer job = PERFECT MATCH (no penalty)

⚠️ MODERATE MISMATCHES (-20 points):
⚠️ Frontend profile → Backend job = MODERATE MISMATCH (-20 points)
⚠️ Backend profile → Frontend job = MODERATE MISMATCH (-20 points)
⚠️ Data Analyst profile → ML Engineer job = MODERATE MISMATCH (-20 points, but can be overcome with strong ML skills)

❌ MAJOR MISMATCHES (-40 points):
❌ ML/Data Science/AI profile → Web Development job = MAJOR MISMATCH (-40 points)
❌ ML/Data Science/AI profile → Cyber Security job = MAJOR MISMATCH (-40 points)
❌ Web Development profile → ML/Data Science job = MAJOR MISMATCH (-40 points)
❌ Web Development profile → Cyber Security job = MAJOR MISMATCH (-40 points)
❌ Cyber Security profile → ML/Data Science job = MAJOR MISMATCH (-40 points)
❌ Cyber Security profile → Web Development job = MAJOR MISMATCH (-40 points)

CRITICAL: Having Python/SQL does NOT qualify someone for Cyber Security roles. Cyber Security requires:
- Security-specific tools (Symantec DLP, SIEM tools, etc.)
- Security experience (log analysis, forensic analysis, incident response)
- Security certifications/knowledge
- Domain-specific experience (3-5 years in cybersecurity)

STEP 5: CALCULATE FINAL SCORE
Final Score = Base Score (from Step 3) - Domain Penalty (from Step 4)
Clamp to 0-100 range.

SCORING EXAMPLES (LEARN FROM THESE):

EXAMPLE 1 - WRONG SCORING (DO NOT DO THIS):
Job: Web Developer (requires React.js, Spring Boot, HTML5, CSS3, MySQL)
Profile: ML Engineer (has Python, Pandas, NumPy, Scikit-learn, Machine Learning, Data Science)
❌ WRONG: Score = 75/100 (too high!)
✅ CORRECT: 
  - Matched skills: MySQL (if profile has it) or Python (if job accepts it) = 1-2 out of 5 = 20-40%
  - Domain mismatch: ML profile → Web Dev job = -40 points
  - Final Score = 20-40% - 40 = 0-20/100 (correct!)

EXAMPLE 2 - CORRECT SCORING:
Job: Web Developer (requires React.js, HTML5, CSS3, JavaScript, MySQL)
Profile: Web Developer (has React.js, HTML5, CSS3, JavaScript, MySQL, Node.js)
✅ CORRECT:
  - Matched: React.js ✓, HTML5 ✓, CSS3 ✓, JavaScript ✓, MySQL ✓ = 5/5 = 100%
  - Domain match: Web Dev → Web Dev = 0 penalty
  - Final Score = 100/100 ✓

EXAMPLE 3 - CORRECT SCORING (AI/ML MATCH):
Job: AI Engineer / Jr. AI Engineer (requires Python, FastAPI, SQL, AI/ML tools, LLMs)
Profile: ML Engineer (has Python, Machine Learning, Natural Language Processing, Deep Learning, SQL)
✅ CORRECT:
  - Matched: Python ✓ (enables FastAPI), SQL ✓, Machine Learning ✓ (matches AI/ML tools), Natural Language Processing ✓ (matches LLMs/AI), Deep Learning ✓ (matches AI/ML tools) = 5/5 = 100%
  - Domain match: ML/AI profile → AI Engineer job = PERFECT MATCH (0 penalty, +10 bonus for strong alignment)
  - Final Score = 100/100 ✓ (or 110/100 capped at 100)

EXAMPLE 3B - CORRECT SCORING (AI/ML MATCH WITH SOME GAPS):
Job: AI Engineer (requires Python, FastAPI, SQL, AI/ML tools, LLMs, Docker, Cloud Platforms)
Profile: ML Engineer (has Python, Machine Learning, Natural Language Processing, Deep Learning, SQL)
✅ CORRECT:
  - Matched: Python ✓ (enables FastAPI), SQL ✓, Machine Learning ✓ (matches AI/ML tools), Natural Language Processing ✓ (matches LLMs), Deep Learning ✓ (matches AI/ML tools) = 5/7 = 71%
  - Missing: FastAPI (can learn quickly with Python), Docker, Cloud Platforms
  - Domain match: ML/AI profile → AI Engineer job = PERFECT MATCH (0 penalty)
  - Final Score = 71/100 ✓ (Good match with learning path)

EXAMPLE 4 - WRONG SCORING (DO NOT DO THIS):
Job: Cyber Security Analyst (requires Symantec DLP, log analysis, forensic analysis, incident response, 3-5 years experience)
Profile: ML Engineer (has Python, SQL, Pandas, NumPy, Scikit-learn, Machine Learning, Data Science)
❌ WRONG: Score = 70/100 (too high! Having Python/SQL doesn't qualify for Cyber Security!)
✅ CORRECT:
  - Matched: Python (if job accepts it) = 1 out of 5+ required skills = 20%
  - Domain mismatch: ML profile → Cyber Security job = -40 points
  - Missing: Symantec DLP, log analysis experience, forensic analysis, incident response, security experience
  - Final Score = 20% - 40 = 0-20/100 (correct!)

EXAMPLE 5 - CORRECT SCORING:
Job: Cyber Security Analyst (requires Symantec DLP, SIEM, log analysis, forensic analysis, incident response)
Profile: Cyber Security Specialist (has Symantec DLP, SIEM tools, log analysis, forensic analysis, incident response, 4 years experience)
✅ CORRECT:
  - Matched: Symantec DLP ✓, SIEM ✓, log analysis ✓, forensic analysis ✓, incident response ✓ = 5/5 = 100%
  - Domain match: Cyber Security → Cyber Security = 0 penalty
  - Final Score = 100/100 ✓

MANDATORY OUTPUT FORMAT:
Return JSON with:
- fit_score: Number 0-100 (calculated using steps above)
- rationale: Must include:
  1. The actual name from profile (NOT placeholder names like "Jayesh", "John")
  2. List of required skills from job
  3. List of matched skills (be specific, including inferred matches like "Python → FastAPI")
  4. List of missing critical skills (prioritize most important ones)
  5. Domain alignment assessment (emphasize if it's a good match!)
  6. Base score calculation: "X out of Y skills matched = Z%"
  7. Domain penalty applied (if any, or bonus if perfect match)
  8. Final score calculation
  9. ACTIONABLE GUIDANCE: Learning path or next steps (especially for scores 40-70)

CRITICAL RULES - ENFORCE STRICTLY:
1. **HARD CAP**: If domain mismatch exists (ML → Cyber Security, ML → Web Dev, Cyber Security → ML, etc.), final score MUST be capped at 40 maximum, regardless of skill overlap. This is MANDATORY - do NOT exceed 40.
2. Having Python/SQL does NOT qualify someone for Cyber Security roles - security requires domain-specific tools (Symantec DLP, SIEM, etc.) and experience.
3. Having Python/SQL does NOT qualify someone for Web Development roles - web dev requires frameworks (React.js, Spring Boot, etc.) and frontend skills (HTML5, CSS3).
4. If a job requires 3-5 years of domain-specific experience and the profile has 0 years, apply -30 points penalty.
5. If a job requires specific tools (Symantec DLP, React.js, etc.) and the profile doesn't have them, those skills are MISSING and must be counted in the gap.
6. **REQUIRED CALCULATION**: Final Score = MIN(Base Score - Domain Penalty, 40) if domain mismatch exists. Use Math.min() logic - never exceed 40 for domain mismatches.
7. If you calculate a score above 40 for a domain mismatch, you MUST cap it at 40. No exceptions.

Format Examples:
- {{"fit_score": 75, "rationale": "Venkat's profile shows strong ML/AI skills (Python, Machine Learning, Natural Language Processing, Deep Learning, SQL). The job requires Jr. AI Engineer: Python, FastAPI, SQL, AI/ML tools, LLMs. Matched: Python ✓ (enables FastAPI), SQL ✓, Machine Learning ✓ (matches AI/ML tools), Natural Language Processing ✓ (matches LLMs), Deep Learning ✓ (matches AI/ML tools) = 5/5 = 100%. Domain alignment: ML/AI profile → AI Engineer job = PERFECT MATCH (0 penalty). Missing: FastAPI (can learn quickly with Python background), Docker, Cloud Platforms. Final: 100% - 0 = 100/100. GUIDANCE: You're an excellent fit! Focus on learning FastAPI (1-2 weeks) and Docker basics to strengthen your application. Your ML/AI background is exactly what they're looking for."}}
- {{"fit_score": 25, "rationale": "Gowtham's profile shows ML/Data Science skills (Python, Pandas, NumPy, Scikit-learn, LangChain, Machine Learning, Deep Learning). The job requires Web Development: React.js, Spring Boot, HTML5, CSS3, MySQL. Matched: Python (1/5 = 20%), MySQL (if profile has it). Major domain mismatch: ML profile → Web Dev job (-40 points). Missing: React.js, Spring Boot, HTML5, CSS3. Final: 20% - 40 = 0, clamped to 25/100. GUIDANCE: This role requires a different skill set. Consider AI/ML roles that match your background, or if you want to transition to web dev, start with HTML/CSS/JavaScript fundamentals (3-6 months learning path)."}}
- {{"fit_score": 20, "rationale": "Gowtham's profile shows ML/Data Science skills (Python, SQL, Pandas, NumPy, Scikit-learn, Machine Learning, Deep Learning). The job requires Cyber Security: Symantec DLP, log analysis, forensic analysis, incident response, 3-5 years experience. Matched: Python (1/6 = 17%). Missing: Symantec DLP, log analysis experience, forensic analysis, incident response, security experience. Major domain mismatch: ML profile → Cyber Security job (-40 points). Experience penalty: 0 years experience (-30 points). Final: 17% - 40 - 30 = 0, clamped to 20/100. GUIDANCE: This role requires specialized security expertise. Your ML skills are valuable but in a different domain. Consider AI/ML security roles or data science positions that better align with your background."}}"""),
        ("human", "User Profile: {profile}\n\nJob Description: {job_description}\n\nFollow the 5-step process above and return JSON with fit_score and detailed rationale:")
    ])


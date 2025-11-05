from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.llm.gemini_client import get_gemini_llm
from app.services.rag_service import query_career_knowledge
from app.services.intent_detector import detect_intent
from app.services.resume_parser import parse_resume_text
from app.llm.chains import get_career_recommendation_chain, get_skill_gap_chain, get_job_fit_chain
from app.clients.supabase_client import get_supabase_client
from app.models.schemas import Profile
from langchain.prompts import ChatPromptTemplate
import json
import re
import html
import base64
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


router = APIRouter(prefix="/chat", tags=["chat"])


def clean_job_description(jd_text: str) -> str:
    """
    Clean and normalize job description text.
    - Fixes skills that are run together (e.g., "JavaHibernateSpring Boot" -> "Java, Hibernate, Spring Boot")
    - Adds proper spacing and formatting
    - Removes excessive whitespace
    """
    if not jd_text:
        return ""
    
    # Common technology/framework names that should be separated
    tech_keywords = [
        'Java', 'Hibernate', 'Spring Boot', 'Spring', 'Microservices', 'JSP', 'Servlets', 
        'Struts', 'J2EE', 'React', 'Angular', 'Vue', 'Node.js', 'Python', 'Docker', 
        'Kubernetes', 'AWS', 'Azure', 'GCP', 'Jenkins', 'GitLab', 'CI/CD', 'REST', 
        'GraphQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Kafka', 'RabbitMQ',
        'TypeScript', 'JavaScript', 'HTML5', 'CSS3', 'Redux', 'Express', 'Django', 'Flask'
    ]
    
    # Step 1: Add spaces before capital letters that follow lowercase letters or numbers
    # This helps separate "JavaHibernate" -> "Java Hibernate"
    cleaned = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', jd_text)
    
    # Step 2: Separate known technology keywords that might be concatenated
    for tech in sorted(tech_keywords, key=len, reverse=True):  # Sort by length to match longer first
        # Pattern: word boundary or start, then tech name (case-insensitive), then word boundary or end
        pattern = rf'(?i)(?<![A-Za-z0-9]){re.escape(tech)}(?![A-Za-z0-9])'
        # Replace with space-padded version if not already spaced
        cleaned = re.sub(pattern, f' {tech} ', cleaned)
    
    # Step 3: Fix common concatenations like "JavaHibernate" -> "Java, Hibernate"
    # Look for patterns like "TechnologyNameTechnologyName" (capital letter sequences)
    # This is a more aggressive approach to separate concatenated tech names
    def separate_tech_words(match):
        text = match.group(0)
        # Split on capital letters but keep them
        parts = re.findall(r'[A-Z][a-z]+', text)
        if len(parts) > 1:
            return ', '.join(parts)
        return text
    
    # Match patterns like "JavaHibernate" or "SpringBoot" (capital letter sequences)
    cleaned = re.sub(r'([A-Z][a-z]+)([A-Z][a-z]+)+', separate_tech_words, cleaned)
    
    # Step 4: Clean up multiple spaces and normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Normalize line breaks
    
    # Step 5: Fix common formatting issues
    # Remove trailing spaces from lines
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join(lines)
    
    # Step 6: Ensure proper spacing around common separators
    cleaned = re.sub(r':([A-Za-z])', r': \1', cleaned)  # "Key Skills:Java" -> "Key Skills: Java"
    cleaned = re.sub(r'([A-Za-z])(->)', r'\1 \2', cleaned)  # "Technology->Java" -> "Technology -> Java"
    
    # Step 7: Fix skills list formatting (often at the end)
    # Look for patterns like "JavaHibernateSpring Boot" and separate them
    # Match sequences of tech-looking words (capital letters followed by lowercase)
    tech_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)?)([A-Z][a-z]+)'
    while re.search(tech_pattern, cleaned):
        cleaned = re.sub(tech_pattern, r'\1, \2', cleaned)
    
    return cleaned.strip()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = None
    use_rag: bool = True  # Whether to use RAG for career knowledge


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint for Career Guidance chatbot.
    Automatically detects user intent and routes to appropriate features:
    - Resume parsing
    - Career recommendations
    - Skill gap analysis
    - Job fit analysis
    - Goal setting/tracking
    - RAG for career knowledge
    """
    # Ensure re module is available (imported at module level, but ensure it's accessible)
    import re as regex_module
    
    # Detect user intent
    intent_result = detect_intent(req.message, req.user_id)
    intent = intent_result["intent"]
    extracted_data = intent_result["extracted_data"]
    
    sb = get_supabase_client()
    llm = get_gemini_llm(temperature=0.7)
    
    try:
        # Route to appropriate feature based on intent
        if intent == "resume_parse":
            # Parse resume text
            parsed = await parse_resume_text(extracted_data.get("resume_text", req.message))
            
            # Save to profile (if user_id provided)
            if req.user_id:
                try:
                    result = sb.table("profiles").upsert({
                        "user_id": req.user_id,
                        "name": parsed.get("name", ""),
                        "email": parsed.get("email", ""),
                        "experience_summary": parsed.get("experience", ""),
                        "skills": parsed.get("skills", [])
                    }).execute()
                    print(f"✅ Profile saved successfully for user_id: {req.user_id}")
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"❌ Error saving profile in chat: {str(e)}")
                    print(f"   Full traceback: {error_trace}")
            
            response_text = f"""✅ **Resume Parsed Successfully!**

📋 **Your Profile:**
• **Name:** {parsed.get('name', 'Not found')}
• **Email:** {parsed.get('email', 'Not found')}
• **Experience:** {parsed.get('experience', 'Not found')[:200]}...
• **Skills:** {', '.join(parsed.get('skills', [])[:10]) or 'Not found'}

💡 **What's Next?**
Now that I know your profile, I can help you with:
• Career recommendations based on your skills
• Skill gap analysis for your target job
• Job fit assessments
• Goal setting and tracking

Try asking: *"What careers are good for me?"*"""
            
            return ChatResponse(response=response_text, sources=None)
        
        elif intent == "career_recommendation":
            # Get career recommendations
            if not req.user_id:
                return ChatResponse(
                    response="⚠️ I need your profile to recommend careers. Please upload your resume first or provide your user_id.",
                    sources=None
                )
            
            # Fetch user profile
            try:
                print(f"🔍 Looking for profile with user_id: {req.user_id}")
                res = sb.table("profiles").select("*").eq("user_id", req.user_id).execute()
                print(f"   Query returned {len(res.data) if res.data else 0} row(s)")
                if res.data:
                    print(f"   Found profile: {res.data[0].get('name', 'Unknown')}")
                if not res.data:
                    # Check if any profiles exist at all
                    all_profiles = sb.table("profiles").select("user_id").limit(5).execute()
                    print(f"   Total profiles in DB: {len(all_profiles.data) if all_profiles.data else 0}")
                    if all_profiles.data:
                        print(f"   Sample user_ids: {[p.get('user_id') for p in all_profiles.data]}")
                    return ChatResponse(
                        response="⚠️ I don't have your profile yet. Please **upload your resume** using the '📄 Upload Resume' button above so I can recommend careers based on your skills and experience.\n\n💡 Once you upload your resume, I'll save your profile and you can ask me for career recommendations!",
                        sources=None
                    )
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ Error fetching profile: {str(e)}")
                print(f"   Full traceback: {error_trace}")
                return ChatResponse(
                    response=f"⚠️ Error fetching your profile: {str(e)}\n\n💡 Please try uploading your resume again using the '📄 Upload Resume' button.",
                    sources=None
                )
            
            profile = res.data[0]
            skills = profile.get("skills", []) or []
            experience = profile.get("experience_summary", "") or ""
            
            try:
                chain = get_career_recommendation_chain()
                result = await chain.ainvoke({
                    "skills": json.dumps(skills) if isinstance(skills, list) else str(skills),
                    "experience": experience
                })
                
                # Handle different response formats
                careers = []
                if isinstance(result, list):
                    careers = result
                elif isinstance(result, dict):
                    if "careers" in result:
                        careers = result["careers"]
                    elif "title" in result or "name" in result:
                        # Single career object
                        careers = [result]
                    else:
                        # Try to extract careers from dict values
                        careers = list(result.values()) if result else []
                elif result:
                    # If result is a string, try to parse it as JSON
                    if isinstance(result, str):
                        try:
                            parsed = json.loads(result)
                            if isinstance(parsed, list):
                                careers = parsed
                            elif isinstance(parsed, dict):
                                careers = [parsed]
                        except:
                            # If parsing fails, use LLM to generate recommendations directly
                            prompt = ChatPromptTemplate.from_messages([
                                ("system", """You are Career Guidance, an expert career guidance coach for the Indian job market. 
Based on the user's skills and experience, recommend 3-5 relevant career paths for the Indian market with brief descriptions.

CRITICAL RECOMMENDATION LOGIC:
1. FIRST, analyze the user's skills to identify their primary domain:
   - If they have ML/AI skills (Pandas, NumPy, Scikit-learn, TensorFlow, PyTorch, LangChain, Machine Learning, Deep Learning) → Prioritize Data Science, ML Engineer, AI Engineer roles
   - If they have data skills (SQL, Statistical Modeling, Power BI, Matplotlib, Seaborn) → Prioritize Data Scientist, Data Analyst, Business Analyst roles
   - If they have cloud/Azure skills → Prioritize Cloud Engineer, Data Engineer, MLOps roles
   - If they have web dev skills (React, Node.js, JavaScript, HTML, CSS) → Prioritize Web Developer roles
   - If they have Java/Spring/Microservices → Prioritize Backend/Java Developer roles
   - If they have full-stack skills → Prioritize Full Stack Developer roles

2. ONLY recommend careers that genuinely match at least 40% of the user's skills
3. If the user has strong ML/Data Science skills, prioritize those roles first
4. If the user has strong software engineering skills, prioritize those roles
5. DO NOT recommend generic web development roles if the user's profile is clearly ML/AI focused
6. DO NOT recommend ML/AI roles if the user's profile is clearly web development focused

CRITICAL CONTEXT REQUIREMENTS:
- ALL information MUST be specific to INDIA and the Indian job market
- ALL salary information MUST be in Indian Rupees (INR) format: ₹X LPA - ₹Y LPA (e.g., ₹8 LPA - ₹15 LPA)
- Use REALISTIC Indian IT market salary ranges (NOT just USD conversions). Typical ranges:
  * Software Engineer: ₹6-20 LPA (entry to senior)
  * Data Scientist: ₹8-25 LPA
  * Machine Learning Engineer: ₹10-30 LPA
  * Data Analyst: ₹5-15 LPA
  * AI Engineer: ₹10-28 LPA
  * MLOps Engineer: ₹12-30 LPA
  * Data Engineer: ₹8-22 LPA
  * Business Analyst: ₹6-18 LPA
  * DevOps Engineer: ₹8-22 LPA
  * Product Manager: ₹12-35 LPA
  * Backend Developer: ₹6-18 LPA
  * Frontend Developer: ₹5-16 LPA
  * Full Stack Developer: ₹7-20 LPA
- Use whole numbers only (no decimals like ₹124.5 LPA - use ₹12-25 LPA instead)
- Job outlook should reflect the Indian job market trends
- Skills and requirements should be relevant to Indian companies

CRITICAL FORMATTING RULES:
- Use MARKDOWN format ONLY (no HTML tags whatsoever)
- Use **bold** for emphasis, *italics* for subtle emphasis
- Use blank lines for paragraph breaks (NOT <br>)
- Use ### for headings if needed
- Use - or • for lists
- NEVER use HTML tags like <br>, <small>, <b>, <i>, <style>, or any inline CSS"""),
                                ("human", "User skills: {skills}\nUser experience: {experience}\n\nRecommend career paths for the Indian market with brief descriptions:")
                            ])
                            chain_direct = prompt | llm
                            direct_result = await chain_direct.ainvoke({
                                "skills": ', '.join(skills) if isinstance(skills, list) else str(skills),
                                "experience": experience
                            })
                            answer = direct_result.content if hasattr(direct_result, 'content') else str(direct_result)
                            return ChatResponse(
                                response=f"🎯 **Career Recommendations Based on Your Profile:**\n\n{answer}",
                                sources=None
                            )
                
                # Format response
                if not careers:
                    # Fallback: use LLM directly
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", """You are CareerCore, an expert career guidance coach for the Indian job market. 
Based on the user's skills and experience, recommend 3-5 relevant career paths for the Indian market with brief descriptions.

CRITICAL RECOMMENDATION LOGIC:
1. FIRST, analyze the user's skills to identify their primary domain:
   - If they have ML/AI skills (Pandas, NumPy, Scikit-learn, TensorFlow, PyTorch, LangChain, Machine Learning, Deep Learning) → Prioritize Data Science, ML Engineer, AI Engineer roles
   - If they have data skills (SQL, Statistical Modeling, Power BI, Matplotlib, Seaborn) → Prioritize Data Scientist, Data Analyst, Business Analyst roles
   - If they have cloud/Azure skills → Prioritize Cloud Engineer, Data Engineer, MLOps roles
   - If they have web dev skills (React, Node.js, JavaScript, HTML, CSS) → Prioritize Web Developer roles
   - If they have Java/Spring/Microservices → Prioritize Backend/Java Developer roles
   - If they have full-stack skills → Prioritize Full Stack Developer roles

2. ONLY recommend careers that genuinely match at least 40% of the user's skills
3. If the user has strong ML/Data Science skills, prioritize those roles first
4. If the user has strong software engineering skills, prioritize those roles
5. DO NOT recommend generic web development roles if the user's profile is clearly ML/AI focused
6. DO NOT recommend ML/AI roles if the user's profile is clearly web development focused

CRITICAL CONTEXT REQUIREMENTS:
- ALL information MUST be specific to INDIA and the Indian job market
- ALL salary information MUST be in Indian Rupees (INR) format: ₹X LPA - ₹Y LPA (e.g., ₹8 LPA - ₹15 LPA)
- Use REALISTIC Indian IT market salary ranges (NOT just USD conversions). Typical ranges:
  * Software Engineer: ₹6-20 LPA (entry to senior)
  * Data Scientist: ₹8-25 LPA
  * Machine Learning Engineer: ₹10-30 LPA
  * Data Analyst: ₹5-15 LPA
  * AI Engineer: ₹10-28 LPA
  * MLOps Engineer: ₹12-30 LPA
  * Data Engineer: ₹8-22 LPA
  * Business Analyst: ₹6-18 LPA
  * DevOps Engineer: ₹8-22 LPA
  * Product Manager: ₹12-35 LPA
  * Backend Developer: ₹6-18 LPA
  * Frontend Developer: ₹5-16 LPA
  * Full Stack Developer: ₹7-20 LPA
- Use whole numbers only (no decimals like ₹124.5 LPA - use ₹12-25 LPA instead)
- Job outlook should reflect the Indian job market trends
- Skills and requirements should be relevant to Indian companies

CRITICAL FORMATTING RULES:
- Use MARKDOWN format ONLY (no HTML tags whatsoever)
- Use **bold** for emphasis, *italics* for subtle emphasis
- Use blank lines for paragraph breaks (NOT <br>)
- Use ### for headings if needed
- Use - or • for lists
- NEVER use HTML tags like <br>, <small>, <b>, <i>, <style>, or any inline CSS"""),
                        ("human", "User skills: {skills}\nUser experience: {experience}\n\nRecommend career paths:")
                    ])
                    chain_direct = prompt | llm
                    direct_result = await chain_direct.ainvoke({
                        "skills": ', '.join(skills) if isinstance(skills, list) else str(skills),
                        "experience": experience
                    })
                    answer = direct_result.content if hasattr(direct_result, 'content') else str(direct_result)
                    return ChatResponse(
                        response=f"🎯 **Career Recommendations Based on Your Profile:**\n\n{answer}",
                        sources=None
                    )
                
                response_text = "🎯 **Career Recommendations Based on Your Profile:**\n\n"
                for i, career in enumerate(careers[:5], 1):
                    if isinstance(career, dict):
                        title = career.get("title") or career.get("name") or career.get("career") or "Career Path"
                        desc = career.get("description") or career.get("desc") or ""
                        salary = career.get("salary_range") or career.get("salary") or ""
                        outlook = career.get("outlook") or career.get("job_outlook") or ""
                    else:
                        title = str(career)
                        desc = ""
                        salary = ""
                        outlook = ""
                    
                    response_text += f"**{i}. {title}**\n"
                    if desc:
                        response_text += f"   {desc}\n"
                    if salary:
                        response_text += f"   💰 Salary: {salary}\n"
                    if outlook:
                        response_text += f"   📈 Outlook: {outlook}\n"
                    response_text += "\n"
                
                return ChatResponse(response=response_text, sources=None)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                # Log the full error for debugging
                print(f"❌ Error in career recommendation: {str(e)}")
                print(f"   Full traceback: {error_trace}")
                # Return user-friendly message
                error_msg = str(e)
                if "JSON" in error_msg or "parse" in error_msg.lower():
                    return ChatResponse(
                        response=f"⚠️ Error generating career recommendations. The AI response format was unexpected.\n\n💡 **Try again** - sometimes the AI needs a second attempt.",
                        sources=None
                    )
                return ChatResponse(
                    response=f"⚠️ Error generating career recommendations: {error_msg}\n\n💡 Please try again or upload your resume first.",
                    sources=None
                )
        
        elif intent == "skill_gap":
            # Skill gap analysis
            if not req.user_id:
                return ChatResponse(
                    response="⚠️ I need your profile to analyze skill gaps. Please upload your resume first.",
                    sources=None
                )
            
            # Fetch user profile
            res = sb.table("profiles").select("*").eq("user_id", req.user_id).execute()
            if not res.data:
                return ChatResponse(
                    response="⚠️ I don't have your profile yet. Please upload your resume first.",
                    sources=None
                )
            
            user_skills = res.data[0].get("skills", []) or []
            target_career = extracted_data.get("target_career", "")
            
            # Check if user is asking about previous job description from conversation
            job_description = None
            # Always try to find job description in conversation history if:
            # 1. Target is explicitly "previous_job_description"
            # 2. No target specified (default to previous job)
            # 3. Message contains "missing", "what", "resume", or "cv" (likely asking about gaps)
            should_search_history = (
                target_career == "previous_job_description" or 
                not target_career or 
                "missing" in req.message.lower() or 
                "what" in req.message.lower() or
                "resume" in req.message.lower() or
                "cv" in req.message.lower()
            )
            
            if should_search_history:
                # Look through conversation history for the most recent job description
                if req.conversation_history:
                    print(f"🔍 Searching conversation history for job description ({len(req.conversation_history)} messages)...")
                    # Search backwards through conversation for job description
                    for msg in reversed(req.conversation_history):
                        # Handle different message formats
                        if isinstance(msg, dict):
                            msg_role = msg.get('role', 'user')
                            msg_content = msg.get('content', '') or msg.get('message', '')
                        elif hasattr(msg, 'content'):
                            msg_role = getattr(msg, 'role', 'user')
                            msg_content = msg.content
                        else:
                            msg_role = 'user'
                            msg_content = str(msg)
                        
                        # Strip HTML tags from content
                        try:
                            if HAS_BS4:
                                # Try to parse HTML and extract text
                                soup = BeautifulSoup(msg_content, 'html.parser')
                                msg_content = soup.get_text(separator=' ', strip=True)
                            else:
                                # Fallback: simple regex to remove HTML tags
                                msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                                msg_content = html.unescape(msg_content)
                        except:
                            # Fallback: simple regex to remove HTML tags
                            msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                            msg_content = html.unescape(msg_content)
                        
                        msg_text = msg_content.lower()
                        
                        # Check if this looks like a job description (check both user and assistant messages)
                        jd_keywords = [
                            'job description', 'job posting', 'skills required', 'required qualifications', 
                            'we are looking', 'we are seeking', 'experience:', 'full-time', 'part-time', 
                            'java developer', 'responsibilities', 'technical requirements', 'spring boot',
                            'microservices', 'employment type', 'role category'
                        ]
                        if any(keyword in msg_text for keyword in jd_keywords) and len(msg_content) > 150:
                            job_description = msg_content
                            print(f"🔍 Found job description in conversation history ({msg_role} message): {len(job_description)} chars")
                            print(f"   Preview: {msg_content[:200]}...")
                            break
            
            # Extract skills from job description or get from career name
            job_skills = []
            if job_description:
                # Clean the job description text before processing
                job_description = clean_job_description(job_description)
                # Extract skills from job description using LLM with more detailed prompt
                skill_extract_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a technical recruiter extracting skills from a job description. 
Extract ALL technical skills, programming languages, frameworks, tools, and concepts mentioned. 
Include:
- Programming languages (e.g., Java, Python)
- Frameworks and libraries (e.g., Spring Boot, REST APIs)
- Concepts and knowledge areas (e.g., OOP Concepts, Multithreading, Collections)
- Database technologies (e.g., SQL, MongoDB)
- Any specific technologies mentioned

Return ONLY a JSON array of skills as strings. Be comprehensive and include all mentioned skills.
Example: ["Core Java", "OOP Concepts", "Collections", "Multithreading", "Exception Handling", "Java 8 Features", "SQL", "Spring Boot", "Microservices", "REST APIs"]"""),
                    ("human", "Job Description:\n{job_description}\n\nExtract all skills and return as JSON array:")
                ])
                skill_extract_chain = skill_extract_prompt | llm
                try:
                    skills_result = await skill_extract_chain.ainvoke({"job_description": job_description})
                    skills_text = skills_result.content if hasattr(skills_result, 'content') else str(skills_result)
                    # Try to extract JSON array
                    # Remove markdown code blocks if present
                    skills_text = regex_module.sub(r'```json\s*', '', skills_text)
                    skills_text = regex_module.sub(r'```\s*', '', skills_text)
                    skills_match = regex_module.search(r'\[.*?\]', skills_text, regex_module.DOTALL)
                    if skills_match:
                        job_skills = json.loads(skills_match.group(0))
                        print(f"🔍 Extracted {len(job_skills)} skills from job description: {job_skills}")
                    else:
                        # Fallback: try to parse as comma-separated list
                        skills_text = skills_text.strip().strip('[]"\'')
                        job_skills = [s.strip().strip('"\'') for s in skills_text.split(',') if s.strip()]
                        print(f"🔍 Extracted {len(job_skills)} skills (fallback parsing): {job_skills}")
                    
                    # Ensure we have skills
                    if not job_skills:
                        raise ValueError("No skills extracted from job description")
                except Exception as e:
                    print(f"⚠️ Error extracting skills from job description: {e}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    # Fallback: use LLM to get skills from career name
                    if target_career and target_career != "previous_job_description":
                        career_query = f"required skills for {target_career}"
                        career_info = await query_career_knowledge(career_query, top_k=2)
                        job_skills = ["Python", "SQL", "Statistics", "Machine Learning"]  # Default fallback
                    else:
                        # Try to extract skills manually from job description text
                        jd_lower = job_description.lower()
                        common_skills = []
                        skill_keywords = {
                            'java': ['core java', 'java'],
                            'oop': ['oop concepts', 'object-oriented'],
                            'collections': ['collections'],
                            'multithreading': ['multithreading', 'threading'],
                            'exception handling': ['exception handling'],
                            'java 8': ['java 8', 'java 8 features'],
                            'sql': ['sql', 'database'],
                            'spring boot': ['spring boot'],
                            'microservices': ['microservices'],
                            'rest apis': ['rest api', 'rest apis', 'restful']
                        }
                        for skill_name, keywords in skill_keywords.items():
                            if any(kw in jd_lower for kw in keywords):
                                common_skills.append(skill_name.title())
                        if common_skills:
                            job_skills = common_skills
                            print(f"🔍 Fallback: Manually extracted {len(job_skills)} skills: {job_skills}")
            elif target_career and target_career != "previous_job_description":
                # Get required skills for target career from RAG
                career_query = f"required skills for {target_career}"
                career_info = await query_career_knowledge(career_query, top_k=2)
                
                # Extract job skills from career data or use LLM
                if career_info.get("sources"):
                    # Try to extract skills from career data
                    for source in career_info["sources"]:
                        content = source.get("content_chunk", "")
                        # Look for skills mentioned
                        if "Required skills" in content or "Skills" in content:
                            # Basic extraction (could be improved)
                            job_skills.extend(["Python", "SQL", "Statistics", "Machine Learning"])  # Placeholder
                
                # Use LLM to get required skills if not found
                if not job_skills:
                    skill_prompt = ChatPromptTemplate.from_messages([
                        ("system", "List the top 5-10 required skills for the given career. Return as JSON array: ['skill1', 'skill2']"),
                        ("human", "Career: {career}")
                    ])
                    skill_chain = skill_prompt | llm
                    try:
                        skills_result = await skill_chain.ainvoke({"career": target_career})
                        skills_text = skills_result.content if hasattr(skills_result, 'content') else str(skills_result)
                        # Try to extract JSON array
                        skills_match = regex_module.search(r'\[.*?\]', skills_text)
                        if skills_match:
                            job_skills = json.loads(skills_match.group(0))
                    except:
                        job_skills = ["Python", "SQL", "Statistics", "Machine Learning", "Data Analysis"]  # Default
            # Check if we have job skills to analyze
            if not job_skills:
                # No job description found in conversation and no career specified
                return ChatResponse(
                    response="⚠️ I couldn't find a job description in our conversation. Please either:\n\n" +
                            "• Paste a job description and ask again, OR\n" +
                            "• Specify the role: \"What skills do I need for Data Scientist?\"",
                    sources=None
                )
            
            # Log what we're comparing
            print(f"🔍 Skill Gap Analysis:")
            print(f"   User skills ({len(user_skills)}): {user_skills}")
            print(f"   Job skills ({len(job_skills)}): {job_skills}")
            
            # Initialize variables
            matched = []
            gap = []
            
            try:
                # Perform skill gap analysis
                chain = get_skill_gap_chain()
                gap_result = await chain.ainvoke({
                    "user_skills": json.dumps(user_skills),
                    "job_skills": json.dumps(job_skills)
                })
                
                print(f"🔍 Gap analysis result: {gap_result}")
                
                if isinstance(gap_result, dict):
                    matched = gap_result.get("matched", []) or []
                    gap = gap_result.get("gap", []) or []
                    # If gap is empty but we have job skills, something went wrong
                    if not gap and job_skills:
                        # Fallback: manually compute gap
                        user_skills_lower = [s.lower() for s in user_skills]
                        gap = [js for js in job_skills if js.lower() not in user_skills_lower and not any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                        print(f"⚠️ Gap was empty, computed manually: {gap}")
                else:
                    # Fallback: manual computation
                    user_skills_lower = [s.lower() for s in user_skills]
                    matched = [js for js in job_skills if js.lower() in user_skills_lower or any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                    gap = [js for js in job_skills if js.lower() not in user_skills_lower and not any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                    print(f"⚠️ Gap result was not dict, computed manually. Matched: {len(matched)}, Gap: {len(gap)}")
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"⚠️ Error in skill gap chain: {e}")
                print(f"   Traceback: {error_trace}")
                # Fallback: manual computation
                user_skills_lower = [s.lower() for s in user_skills]
                matched = [js for js in job_skills if js.lower() in user_skills_lower or any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                gap = [js for js in job_skills if js.lower() not in user_skills_lower and not any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                print(f"⚠️ Using manual computation. Matched: {len(matched)}, Gap: {len(gap)}")
            
            # Determine title for response
            if job_description:
                # Try to extract job title from job description
                title_match = regex_module.search(r'(?:Java Developer|Software Engineer|Data Scientist|Product Manager|Developer|Engineer)[^:\n]*', job_description, regex_module.IGNORECASE)
                job_title = title_match.group(0).strip() if title_match else "the Job"
                analysis_title = f"Skill Gap Analysis for {job_title}"
            elif target_career and target_career != "previous_job_description":
                analysis_title = f"Skill Gap Analysis for {target_career.title()}"
            else:
                analysis_title = "Skill Gap Analysis for the Job"
            
            # Format response safely
            matched_str = ', '.join(str(s) for s in matched) if matched else 'None found'
            gap_str = ', '.join(str(s) for s in gap) if gap else 'None! You have all the required skills.'
            recommendation_str = ', '.join(str(s) for s in gap[:3]) if gap else 'You\'re well-prepared!'
            
            response_text = f"""📊 **{analysis_title}**

✅ **Skills You Have:**
{matched_str}

❌ **Skills You Need to Develop:**
{gap_str}

💡 **Recommendation:**
Focus on developing: {recommendation_str}"""
            
            return ChatResponse(response=response_text, sources=None)
        
        elif intent == "job_fit":
            # Job fit analysis
            if not req.user_id:
                return ChatResponse(
                    response="⚠️ I need your profile to analyze job fit. Please upload your resume first.",
                    sources=None
                )
            
            # Fetch user profile by user_id
            res = sb.table("profiles").select("*").eq("user_id", req.user_id).execute()
            
            # If not found by user_id, try to find by checking if user_id is email-based
            # and look for profiles with matching email (in case user_id changed after resume upload)
            if not res.data:
                print(f"⚠️ Profile not found for user_id: {req.user_id}, checking if profile exists with different user_id...")
                # Try to extract email from user_id if it's email-based
                # Email-based user_ids are like: user_YW1iYWRpZ293dGhhbUBn
                # Try to decode the base64 part
                try:
                    if req.user_id.startswith('user_'):
                        # Extract the base64 part
                        base64_part = req.user_id[5:]  # Remove 'user_' prefix
                        # Try to decode (this is reverse of btoa)
                        # Add padding if needed
                        padding = 4 - len(base64_part) % 4
                        if padding != 4:
                            base64_part += '=' * padding
                        try:
                            decoded_email = base64.b64decode(base64_part).decode('utf-8')
                            print(f"🔍 Decoded email from user_id: {decoded_email}")
                            # Try to find profile by email
                            email_res = sb.table("profiles").select("*").eq("email", decoded_email).execute()
                            if email_res.data and len(email_res.data) > 0:
                                # Found profile by email, update it to use the new user_id
                                print(f"✅ Found profile by email, updating user_id from {email_res.data[0].get('user_id')} to {req.user_id}")
                                sb.table("profiles").update({"user_id": req.user_id}).eq("email", decoded_email).execute()
                                # Fetch again with new user_id
                                res = sb.table("profiles").select("*").eq("user_id", req.user_id).execute()
                        except Exception as decode_error:
                            print(f"⚠️ Could not decode email from user_id: {decode_error}")
                except Exception as e:
                    print(f"⚠️ Error checking for profile by email: {e}")
            
            if not res.data:
                return ChatResponse(
                    response="⚠️ I don't have your profile yet. Please upload your resume first.",
                    sources=None
                )
            
            profile = res.data[0]
            job_description = extracted_data.get("job_description", req.message)
            
            # Clean and normalize job description text
            job_description = clean_job_description(job_description)
            
            profile_obj = Profile(
                user_id=profile["user_id"],
                name=profile.get("name"),
                email=profile.get("email"),
                experience_summary=profile.get("experience_summary"),
                skills=profile.get("skills", [])
            )
            
            chain = get_job_fit_chain()
            fit_result = await chain.ainvoke({
                "profile": json.dumps({
                    "name": profile_obj.name or "",
                    "email": profile_obj.email or "",
                    "experience": profile_obj.experience_summary or "",
                    "skills": profile_obj.skills or []
                }),
                "job_description": job_description
            })
            
            if isinstance(fit_result, dict):
                fit_score = fit_result.get("fit_score", 0)
                rationale = fit_result.get("rationale", "")
            else:
                fit_score = 0
                rationale = "Analysis completed."
            
            fit_score = max(0, min(100, int(fit_score)))
            
            # Add emoji based on score
            emoji = "🟢" if fit_score >= 70 else "🟡" if fit_score >= 50 else "🔴"
            
            response_text = f"""📋 **Job Fit Analysis**

{emoji} **Fit Score: {fit_score}/100**

**Rationale:**
{rationale}

💡 **Insights:**
{'Excellent match! You\'re well-qualified for this role.' if fit_score >= 70 else 
'Good potential match. Consider developing the missing skills.' if fit_score >= 50 else 
'Some gaps exist. Focus on building required skills before applying.'}"""
            
            return ChatResponse(response=response_text, sources=None)
        
        elif intent == "goal_set":
            # Set a goal
            try:
                if not req.user_id:
                    return ChatResponse(
                        response="⚠️ I need your user_id to set goals. Please provide your user_id in the request.",
                        sources=None
                    )
                
                goal_text = extracted_data.get("goal_text", req.message) or ""
                
                # Check if user wants to learn N skills (e.g., "learn 4 major skills", "set goals to learn 4", "add top 4 skills")
                num_skills_to_learn = None
                # Check for number in the original message - multiple patterns
                num_match = regex_module.search(r'\b(?:top|major|important|key|main)\s+(\d+)\s+skills?\b', req.message.lower())
                if not num_match:
                    num_match = regex_module.search(r'\b(\d+)\s+(?:major|top|important|key|main)?\s*skills?\b', req.message.lower())
                if not num_match:
                    # Also check for "learn 4" or "4 skills" anywhere in message
                    num_match = regex_module.search(r'\b(?:learn|set|create|add)\s+(\d+)\b', req.message.lower())
                if num_match:
                    num_skills_to_learn = int(num_match.group(1))
                    print(f"🔍 User requested {num_skills_to_learn} skills")
                
                # Check if goal_text is "from_context" - need to extract from conversation history
                goal_text_lower = (goal_text or "").lower()
                message_lower = req.message.lower()
                
                # CRITICAL: First check if we have an explicit skill name extracted (e.g., "Python", "Spring Boot")
                # If goal_text is a specific skill name (not "from_context" and doesn't contain context keywords),
                # then skip context extraction and go directly to single goal creation
                has_explicit_skill = (
                    goal_text and 
                    goal_text != "from_context" and 
                    len(goal_text.strip()) >= 2 and
                    not any(keyword in goal_text_lower for keyword in [
                        'missing', 'gap', 'need to develop', 'required to develop', 
                        'from context', 'from this', 'from that', 'from these', 'from them',
                        'add', 'set', 'the skills', 'these skills', 'those skills'
                    ])
                )
                
                # Check if this is a context-based goal request (only if no explicit skill)
                is_context_request = (
                    not has_explicit_skill and (
                        goal_text == "from_context" or 
                        not goal_text or 
                        "missing" in goal_text_lower or 
                        "gap" in goal_text_lower or 
                        "need to develop" in goal_text_lower or 
                        "required to develop" in goal_text_lower or
                        "from this" in message_lower or
                        "from that" in message_lower or
                        "from these" in message_lower or
                        ("add" in message_lower and "goal" in message_lower and ("skill" in message_lower or "develop" in message_lower)) or
                        ("add" in message_lower and ("need" in message_lower or "missing" in message_lower) and "develop" in message_lower and "skill" in message_lower)
                    )
                )
                
                # If we have an explicit skill, skip context extraction entirely
                if has_explicit_skill:
                    # Skip context extraction - go directly to single goal creation
                    print(f"✅ Explicit skill detected: '{goal_text}', skipping context extraction")
                    # This will fall through to single goal creation below
                elif is_context_request:
                    # Look through conversation history for recent skill gap analysis
                    skills_to_learn = []
                    if req.conversation_history:
                        print(f"🔍 Searching conversation history for skill gap analysis ({len(req.conversation_history)} messages)...")
                        # Search backwards for skill gap analysis response
                        for msg in reversed(req.conversation_history):
                            # Check if this is an assistant message with skill gap info
                            # Handle both dict and Pydantic model formats
                            if isinstance(msg, dict):
                                msg_role = msg.get('role', '')
                                msg_content = msg.get('content', '') or msg.get('message', '')
                            elif hasattr(msg, 'role') or hasattr(msg, 'content'):
                                msg_role = getattr(msg, 'role', '')
                                msg_content = getattr(msg, 'content', '') or getattr(msg, 'message', '')
                            else:
                                msg_role = ''
                                msg_content = str(msg)
                            
                            if msg_role == 'assistant':
                                
                                # Strip HTML tags from content
                                try:
                                    if HAS_BS4:
                                        # Try to parse HTML and extract text
                                        soup = BeautifulSoup(msg_content, 'html.parser')
                                        msg_content_clean = soup.get_text(separator='\n', strip=True)
                                    else:
                                        # Fallback: simple regex to remove HTML tags
                                        msg_content_clean = regex_module.sub(r'<[^>]+>', '\n', msg_content)
                                        msg_content_clean = html.unescape(msg_content_clean)
                                except:
                                    # Fallback: simple regex to remove HTML tags
                                    msg_content_clean = regex_module.sub(r'<[^>]+>', '\n', msg_content)
                                    msg_content_clean = html.unescape(msg_content_clean)
                                
                                # Look for "Skills You Need to Develop" section
                                if "Skills You Need to Develop" in msg_content_clean or "❌" in msg_content_clean or "need to develop" in msg_content_clean.lower():
                                    print(f"🔍 Found potential skill gap message, extracting skills...")
                                    # Extract skills from the gap section
                                    # Format: "❌ **Skills You Need to Develop:**\nSkill1, Skill2, Skill3"
                                    # Try multiple patterns (use cleaned content without HTML)
                                    gap_match = regex_module.search(r'❌.*?Skills You Need to Develop.*?:\s*\n(.+?)(?:\n\n|\n💡|\n✅|\n📊|$)', msg_content_clean, regex_module.DOTALL | regex_module.IGNORECASE)
                                    if not gap_match:
                                        # Alternative pattern without emoji
                                        gap_match = regex_module.search(r'Skills You Need to Develop.*?:\s*\n(.+?)(?:\n\n|\n💡|\n✅|\n📊|$)', msg_content_clean, regex_module.DOTALL | regex_module.IGNORECASE)
                                    if not gap_match:
                                        # Pattern for "Need to Develop" without "Skills You"
                                        gap_match = regex_module.search(r'Need to Develop.*?:\s*\n(.+?)(?:\n\n|\n💡|\n✅|\n📊|$)', msg_content_clean, regex_module.DOTALL | regex_module.IGNORECASE)
                                    
                                    if gap_match:
                                        skills_text = gap_match.group(1).strip()
                                        # Split by comma and clean up
                                        skills_to_learn = [s.strip() for s in skills_text.split(',') if s.strip()]
                                        # Remove any markdown formatting and extra characters
                                        skills_to_learn = [regex_module.sub(r'\*\*|__|`|^\s*[•\-\*]\s*', '', s).strip() for s in skills_to_learn]
                                        # Filter out empty strings and non-skill items
                                        skills_to_learn = [s for s in skills_to_learn if s and len(s) > 2]
                                        # Filter out non-technical skills and generic terms
                                        non_skill_keywords = [
                                            'code quality', 'unit test', 'integration test', 'performance', 'optimization',
                                            'software development', 'data science', 'programming', 'development',
                                            'databases', 'coding standards', 'code reviews', 'unit testing', 'integration testing',
                                            'performance tuning', 'service discovery', 'load balancing', 'api gateway'
                                        ]
                                        skills_to_learn = [s for s in skills_to_learn if not any(nsk in s.lower() for nsk in non_skill_keywords)]
                                        
                                        # Also filter out standalone testing terms
                                        skills_to_learn = [s for s in skills_to_learn if not s.lower().strip() in ['unit testing', 'integration testing', 'testing']]
                                        
                                        # Prioritize important skills (frameworks, major concepts)
                                        priority_skills = ['spring boot', 'microservices', 'rest api', 'docker', 'ci/cd', 'java 8', 'spring cloud']
                                        prioritized = []
                                        remaining = []
                                        for skill in skills_to_learn:
                                            skill_lower = skill.lower()
                                            if any(ps in skill_lower for ps in priority_skills):
                                                prioritized.append(skill)
                                            else:
                                                remaining.append(skill)
                                        # Combine: prioritized first, then others
                                        skills_to_learn = prioritized + remaining
                                        
                                        if skills_to_learn:
                                            print(f"🔍 Extracted {len(skills_to_learn)} skills from conversation: {skills_to_learn[:10]}")
                                            break
                    
                    # If no skills found in history, try to extract from the current message using LLM
                    if not skills_to_learn:
                        # Try to understand what "them" refers to
                        context_prompt = ChatPromptTemplate.from_messages([
                            ("system", "You are analyzing a conversation. The user just said they want to set goals 'for them'. Look at the conversation history and extract the skills that were mentioned as missing or needed. Return ONLY a JSON array of skill names, nothing else."),
                            ("human", "Conversation:\n{conversation}\n\nUser's latest message: {user_message}")
                        ])
                        
                        # Build conversation context
                        conv_text = "\n".join([
                            f"{msg.get('role', 'user') if isinstance(msg, dict) else getattr(msg, 'role', 'user')}: {msg.get('content', '') if isinstance(msg, dict) else (getattr(msg, 'content', '') or getattr(msg, 'message', ''))}"
                            for msg in (req.conversation_history[-5:] if req.conversation_history else [])
                        ])
                        
                        try:
                            context_chain = context_prompt | llm
                            context_result = await context_chain.ainvoke({
                                "conversation": conv_text,
                                "user_message": req.message
                            })
                            context_text = context_result.content if hasattr(context_result, 'content') else str(context_result)
                            # Try to extract JSON array
                            skills_match = regex_module.search(r'\[.*?\]', context_text)
                            if skills_match:
                                skills_to_learn = json.loads(skills_match.group(0))
                        except Exception as e:
                            print(f"⚠️ Error extracting skills from context: {e}")
                    
                    if not skills_to_learn:
                        # Try one more time - search for any skill gap analysis in the last few messages
                        if req.conversation_history:
                            for msg in reversed(req.conversation_history[-5:]):
                                if isinstance(msg, dict):
                                    msg_content = msg.get('content', '') or msg.get('message', '')
                                elif hasattr(msg, 'content'):
                                    msg_content = getattr(msg, 'content', '') or getattr(msg, 'message', '')
                                else:
                                    msg_content = str(msg)
                                
                                # Strip HTML
                                try:
                                    if HAS_BS4:
                                        soup = BeautifulSoup(msg_content, 'html.parser')
                                        msg_content_clean = soup.get_text(separator='\n', strip=True)
                                    else:
                                        msg_content_clean = regex_module.sub(r'<[^>]+>', '\n', msg_content)
                                        msg_content_clean = html.unescape(msg_content_clean)
                                except:
                                    msg_content_clean = regex_module.sub(r'<[^>]+>', '\n', msg_content)
                                    msg_content_clean = html.unescape(msg_content_clean)
                                
                                # Look for "Skills You Need to Develop" or similar
                                if "Need to Develop:" in msg_content_clean or "❌" in msg_content_clean:
                                    # Extract everything after "Need to Develop:"
                                    gap_match = regex_module.search(r'Need to Develop.*?:\s*\n(.+?)(?:\n\n|\n💡|\n✅|\n📊|$)', msg_content_clean, regex_module.DOTALL | regex_module.IGNORECASE)
                                    if gap_match:
                                        skills_text = gap_match.group(1).strip()
                                        skills_to_learn = [s.strip() for s in skills_text.split(',') if s.strip()]
                                        skills_to_learn = [regex_module.sub(r'\*\*|__|`|^\s*[•\-\*]\s*', '', s).strip() for s in skills_to_learn]
                                        skills_to_learn = [s for s in skills_to_learn if s and len(s) > 2]
                                        if skills_to_learn:
                                            print(f"🔍 Found skills in recent message: {skills_to_learn}")
                                            break
                        
                        if not skills_to_learn:
                            return ChatResponse(
                                response="⚠️ I couldn't find any skills to set goals for in our conversation.\n\n" +
                                        "💡 **Try saying:**\n" +
                                        "• \"Set a goal to learn Spring Boot\"\n" +
                                        "• \"Help me set a goal to master Microservices\"\n" +
                                        "• Or ask for skill gap analysis first, then say \"Add the skills to goals\" or \"Set goals for them\"",
                                sources=None
                            )
                    
                    # Limit number of skills based on user request or default
                    max_skills = num_skills_to_learn if num_skills_to_learn else min(5, len(skills_to_learn))
                    skills_to_create = skills_to_learn[:max_skills]
                    
                    print(f"🔍 Creating {len(skills_to_create)} goals for skills: {skills_to_create}")
                    print(f"👤 User ID: {req.user_id}")
                    
                    # CRITICAL: Validate user_id before creating goals
                    if not req.user_id or not req.user_id.strip():
                        return ChatResponse(
                            response="⚠️ I need your user_id to set goals. Please provide your user_id in the request.",
                            sources=None
                        )
                    
                    user_id_clean = req.user_id.strip()
                    
                    # CRITICAL: Ensure profile exists before creating goals (foreign key constraint)
                    profile_check = sb.table("profiles").select("user_id").eq("user_id", user_id_clean).execute()
                    if not profile_check.data or len(profile_check.data) == 0:
                        # Profile doesn't exist, create a minimal profile
                        print(f"⚠️ Profile not found for user_id: {user_id_clean}, creating minimal profile...")
                        try:
                            sb.table("profiles").upsert({
                                "user_id": user_id_clean,
                                "name": "",
                                "email": "",
                                "experience_summary": "",
                                "skills": []
                            }).execute()
                            print(f"✅ Created minimal profile for user_id: {user_id_clean}")
                        except Exception as e:
                            print(f"❌ Error creating profile: {str(e)}")
                            return ChatResponse(
                                response="⚠️ I couldn't create your profile. Please upload your resume first to create your profile.",
                                sources=None
                            )
                    
                    # Fetch existing goals for this user to prevent duplicates
                    existing_goals_res = sb.table("goals").select("*").eq("user_id", user_id_clean).execute()
                    existing_goals = existing_goals_res.data or []
                    existing_goal_texts = {g.get("goal_text", "").lower().strip() for g in existing_goals}
                    
                    print(f"📋 Found {len(existing_goals)} existing goals for user_id: {user_id_clean}")
                    
                    # Create goals for each skill
                    created_goals = []
                    skipped_goals = []
                    reactivated_goals = []
                    errors = []
                    for skill in skills_to_create:
                        if not skill or len(skill.strip()) < 2:
                            continue
                        goal_text_clean = f"Learn {skill.strip()}"
                        goal_text_lower = goal_text_clean.lower().strip()
                        
                        # Check if goal already exists for this user
                        if goal_text_lower in existing_goal_texts:
                            # Find the existing goal
                            existing_goal = next((g for g in existing_goals if g.get("goal_text", "").lower().strip() == goal_text_lower), None)
                            if existing_goal:
                                if existing_goal.get("status") == "active":
                                    # Skip if already active
                                    skipped_goals.append(skill.strip())
                                    print(f"⏭️ Skipped duplicate active goal: {goal_text_clean}")
                                    continue
                                elif existing_goal.get("status") == "completed":
                                    # Reactivate if completed
                                    try:
                                        goal_id = existing_goal.get("goal_id")
                                        update_res = sb.table("goals").update({"status": "active"}).eq("goal_id", goal_id).eq("user_id", user_id_clean).execute()
                                        reactivated_goals.append(skill.strip())
                                        print(f"🔄 Reactivated goal: {goal_text_clean}")
                                    except Exception as e:
                                        print(f"⚠️ Error reactivating goal '{skill}': {str(e)}")
                                        errors.append(f"Error reactivating goal for '{skill}': {str(e)}")
                                    continue
                        
                        # Create new goal
                        try:
                            res = sb.table("goals").insert({
                                "user_id": user_id_clean,
                                "goal_text": goal_text_clean,
                                "status": "active"
                            }).execute()
                            created_goals.append(skill.strip())
                            print(f"✅ Created goal: {goal_text_clean} for user_id: {user_id_clean}")
                        except Exception as e:
                            import traceback
                            error_trace = traceback.format_exc()
                            error_msg = f"Error creating goal for '{skill}': {str(e)}"
                            print(f"⚠️ {error_msg}")
                            print(f"   Traceback: {error_trace}")
                            errors.append(error_msg)
                    
                    # Build response message
                    if created_goals or reactivated_goals:
                        response_parts = []
                        if created_goals:
                            goals_list = "\n".join([f"• Learn {goal}" for goal in created_goals])
                            num_created = len(created_goals)
                            response_parts.append(f"""✅ **Goals Created Successfully!**

🎯 **Your New Goals ({num_created}):**
{goals_list}""")
                        
                        if reactivated_goals:
                            reactivated_list = "\n".join([f"• Learn {goal}" for goal in reactivated_goals])
                            response_parts.append(f"""🔄 **Reactivated Goals ({len(reactivated_goals)}):**
{reactivated_list}""")
                        
                        if skipped_goals:
                            skipped_list = "\n".join([f"• Learn {goal}" for goal in skipped_goals])
                            response_parts.append(f"""⏭️ **Skipped (Already Active) ({len(skipped_goals)}):**
{skipped_list}""")
                        
                        response_text = "\n\n".join(response_parts) + "\n\n💪 I'll help you track these goals. Ask me \"What are my goals?\" to see all your active goals."
                        
                        if errors:
                            response_text += f"\n\n⚠️ Note: {len(errors)} goal(s) failed to create. Check server logs for details."
                    else:
                        if skipped_goals and not errors:
                            skipped_list = "\n".join([f"• Learn {goal}" for goal in skipped_goals])
                            response_text = f"""⏭️ **All Goals Already Exist**

These goals are already active:
{skipped_list}

💡 Ask me *"What are my goals?"* to see all your active goals."""
                        elif errors:
                            response_text = f"⚠️ Failed to create goals. Errors:\n" + "\n".join([f"• {e}" for e in errors[:3]])
                        else:
                            response_text = "⚠️ I couldn't create the goals. Please try again."
                    
                    return ChatResponse(response=response_text, sources=None)
                
                # Single goal creation (original logic) - when goal_text is explicitly provided
                # First, try to extract skill name from goal_text if it's explicit (e.g., "learn Python", "Python", "to learn Spring Boot")
                extracted_skill = None
                if goal_text and goal_text != "from_context":
                    # Remove common prefixes like "learn", "master", "study", etc.
                    goal_text_clean_for_extraction = goal_text.strip()
                    
                    # Also check the original message if goal_text extraction failed
                    if not goal_text_clean_for_extraction or len(goal_text_clean_for_extraction) < 2:
                        # Try extracting directly from the user's message
                        message_lower = req.message.lower()
                        skill_match = regex_module.search(r'(?:set\s+a\s+goal\s+to\s+)?(?:learn|master|study|improve|get\s+better\s+at|understand)\s+(.+?)(?:\.|$|,|\s+and)', message_lower)
                        if skill_match:
                            goal_text_clean_for_extraction = skill_match.group(1).strip()
                    
                    # Pattern to extract skill name after "learn", "master", "study", etc.
                    skill_match = regex_module.search(r'\b(?:learn|master|study|improve|get better at|understand)\s+(.+?)(?:\.|$)', goal_text_clean_for_extraction.lower())
                    if skill_match:
                        extracted_skill = skill_match.group(1).strip()
                    else:
                        # If no "learn" prefix, check if it's just a skill name (e.g., "Python", "Spring Boot")
                        # Filter out common goal-setting phrases
                        if not any(phrase in goal_text_clean_for_extraction.lower() for phrase in [
                            'missing', 'gap', 'need to develop', 'required to develop', 'from context',
                            'from this', 'from that', 'from these', 'from them', 'add', 'set'
                        ]):
                            # Likely a direct skill name
                            extracted_skill = goal_text_clean_for_extraction
                
                # If we extracted a skill, use it directly
                if extracted_skill and len(extracted_skill.strip()) >= 2:
                    # Skip all the context extraction logic and go straight to goal creation
                    goal_text_clean = f"Learn {extracted_skill.strip()}"
                elif not goal_text or len(goal_text.strip()) < 2:
                    return ChatResponse(
                        response="⚠️ Please specify what goal you want to set. For example: 'Set a goal to learn Python'",
                        sources=None
                    )
                else:
                    goal_text_clean = goal_text.strip()
                
                # CRITICAL: Validate user_id before creating goal
                if not req.user_id or not req.user_id.strip():
                    return ChatResponse(
                        response="⚠️ I need your user_id to set goals. Please provide your user_id in the request.",
                        sources=None
                    )
                
                user_id_clean = req.user_id.strip()
                goal_text_lower = goal_text_clean.lower()
                
                # CRITICAL: Ensure profile exists before creating goal (foreign key constraint)
                profile_check = sb.table("profiles").select("user_id").eq("user_id", user_id_clean).execute()
                if not profile_check.data or len(profile_check.data) == 0:
                    # Profile doesn't exist, create a minimal profile
                    print(f"⚠️ Profile not found for user_id: {user_id_clean}, creating minimal profile...")
                    try:
                        sb.table("profiles").upsert({
                            "user_id": user_id_clean,
                            "name": "",
                            "email": "",
                            "experience_summary": "",
                            "skills": []
                        }).execute()
                        print(f"✅ Created minimal profile for user_id: {user_id_clean}")
                    except Exception as e:
                        print(f"❌ Error creating profile: {str(e)}")
                        return ChatResponse(
                            response="⚠️ I couldn't create your profile. Please upload your resume first to create your profile.",
                            sources=None
                        )
                
                # Check if goal already exists for this user
                existing_goals_res = sb.table("goals").select("*").eq("user_id", user_id_clean).execute()
                existing_goals = existing_goals_res.data or []
                existing_goal = next((g for g in existing_goals if g.get("goal_text", "").lower().strip() == goal_text_lower), None)
                
                if existing_goal:
                    if existing_goal.get("status") == "active":
                        response_text = f"""⏭️ **Goal Already Exists**

🎯 **Your Goal:**
"{goal_text_clean}"

This goal is already active. Ask me *"What are my goals?"* to see all your active goals."""
                    elif existing_goal.get("status") == "completed":
                        # Reactivate the goal
                        goal_id = existing_goal.get("goal_id")
                        update_res = sb.table("goals").update({"status": "active"}).eq("goal_id", goal_id).eq("user_id", user_id_clean).execute()
                        response_text = f"""🔄 **Goal Reactivated!**

🎯 **Your Goal:**
"{goal_text_clean}"

This goal was previously completed and is now active again. Ask me *"What are my goals?"* to see all your active goals."""
                    else:
                        response_text = f"""⏭️ **Goal Already Exists**

🎯 **Your Goal:**
"{goal_text_clean}"

This goal already exists. Ask me *"What are my goals?"* to see all your goals."""
                else:
                    # Create new goal
                    res = sb.table("goals").insert({
                        "user_id": user_id_clean,
                        "goal_text": goal_text_clean,
                        "status": "active"
                    }).execute()
                    
                    print(f"✅ Created goal: {goal_text_clean} for user_id: {user_id_clean}")
                    
                    response_text = f"""✅ **Goal Set Successfully!**

🎯 **Your New Goal:**
"{goal_text_clean}"

💪 I'll help you track this goal. Ask me *"What are my goals?"* to see all your active goals."""
                
                return ChatResponse(response=response_text, sources=None)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ Error in goal_set endpoint: {str(e)}")
                print(f"   Full traceback:\n{error_trace}")
                print(f"   Request message: {req.message}")
                print(f"   Goal text: {goal_text if 'goal_text' in locals() else 'N/A'}")
                print(f"   User ID: {req.user_id}")
                return ChatResponse(
                    response=f"⚠️ Error setting goals: {str(e)}\n\n💡 Please try again or check server logs for details.",
                    sources=None
                )
        
        elif intent == "goal_list":
            # List goals - CRITICAL: Filter by user_id to ensure users only see their own goals
            if not req.user_id or not req.user_id.strip():
                print(f"⚠️ WARNING: Goal list requested without valid user_id. Request: {req.user_id}")
                return ChatResponse(
                    response="⚠️ I need your user_id to list goals. Please provide your user_id in the request.",
                    sources=None
                )
            
            # Explicitly filter by user_id to prevent cross-user data leakage
            user_id_clean = req.user_id.strip()
            print(f"🔍 Fetching goals for user_id: {user_id_clean}")
            
            res = sb.table("goals").select("*").eq("user_id", user_id_clean).order("created_at", desc=True).execute()
            goals = res.data or []
            
            print(f"📋 Found {len(goals)} goals for user_id: {user_id_clean}")
            
            if not goals:
                response_text = "📋 You don't have any goals yet.\n\n💡 **Set a goal by saying:**\n\"Help me set a goal to learn Python\"\nor\n\"Set a goal to master Machine Learning\""
            else:
                # Filter to show active goals first, then completed
                active_goals = [g for g in goals if g.get("status") != "completed"]
                completed_goals = [g for g in goals if g.get("status") == "completed"]
                
                # Deduplicate goals by goal_text (case-insensitive)
                seen_goals = set()
                unique_active_goals = []
                for goal in active_goals:
                    goal_text_lower = goal.get('goal_text', '').lower().strip()
                    if goal_text_lower not in seen_goals:
                        seen_goals.add(goal_text_lower)
                        unique_active_goals.append(goal)
                
                seen_completed = set()
                unique_completed_goals = []
                for goal in completed_goals:
                    goal_text_lower = goal.get('goal_text', '').lower().strip()
                    if goal_text_lower not in seen_completed:
                        seen_completed.add(goal_text_lower)
                        unique_completed_goals.append(goal)
                
                total_unique = len(unique_active_goals) + len(unique_completed_goals)
                response_text = f"📋 **Your Goals ({total_unique} total):**\n\n"
                
                # Show active goals
                if unique_active_goals:
                    response_text += "**🔄 Active Goals:**\n"
                    for goal in unique_active_goals:
                        response_text += f"🔄 **{goal.get('goal_text', 'Unknown')}**\n"
                        response_text += f"   Status: {goal.get('status', 'active').title()}\n\n"
                
                # Show completed goals
                if unique_completed_goals:
                    response_text += "**✅ Completed Goals:**\n"
                    for goal in unique_completed_goals:
                        response_text += f"✅ **{goal.get('goal_text', 'Unknown')}**\n"
                        response_text += f"   Status: {goal.get('status', 'active').title()}\n\n"
            
            return ChatResponse(response=response_text, sources=None)
        
        elif intent == "goal_complete":
            # Mark goal as completed - CRITICAL: Filter by user_id to ensure users only update their own goals
            if not req.user_id or not req.user_id.strip():
                print(f"⚠️ WARNING: Goal complete requested without valid user_id. Request: {req.user_id}")
                return ChatResponse(
                    response="⚠️ I need your user_id to update goals. Please provide your user_id in the request.",
                    sources=None
                )
            
            user_id_clean = req.user_id.strip()
            print(f"🔍 Completing goal for user_id: {user_id_clean}")
            
            try:
                # Get all active goals - explicitly filter by user_id to prevent cross-user data access
                res = sb.table("goals").select("*").eq("user_id", user_id_clean).eq("status", "active").order("created_at", desc=True).execute()
                active_goals = res.data or []
                
                print(f"📋 Found {len(active_goals)} active goals for user_id: {user_id_clean}")
                
                if not active_goals:
                    return ChatResponse(
                        response="📋 You don't have any active goals to mark as completed.",
                        sources=None
                    )
                
                # Try to identify which goal to mark as completed
                # Check conversation history for recently mentioned goal
                goal_to_complete = None
                message_lower = req.message.lower().strip()
                
                # Extract goal keywords from message (remove common words like "completed", "done", "mark")
                message_words = [w for w in message_lower.split() if w not in ['completed', 'done', 'mark', 'as', 'complete', 'finish', 'finished', 'finish']]
                
                # First, try exact match or substring match (most precise)
                for goal in active_goals:
                    goal_text = goal.get("goal_text", "").lower().strip()
                    # Check for exact match or if goal text is contained in message
                    if goal_text in message_lower or message_lower in goal_text:
                        goal_to_complete = goal
                        break
                
                # If no exact match, try matching significant keywords
                if not goal_to_complete:
                    # Extract meaningful keywords from message (skip common words)
                    significant_message_words = [w for w in message_words if len(w) > 3 and w not in ['learn', 'goal', 'goals']]
                    
                    if significant_message_words:
                        best_match = None
                        best_score = 0
                        
                        for goal in active_goals:
                            goal_text = goal.get("goal_text", "").lower().strip()
                            goal_words = [w for w in goal_text.split() if len(w) > 3 and w not in ['learn']]
                            
                            # Score based on how many significant words match
                            score = 0
                            for word in significant_message_words:
                                if word in goal_text:
                                    score += 3  # Exact match in goal text
                                elif any(word in gw or gw in word for gw in goal_words):
                                    score += 2  # Match with goal word
                            
                            if score > best_score and score >= 3:  # Require at least 3 points (one exact match)
                                best_score = score
                                best_match = goal
                        
                        if best_match:
                            goal_to_complete = best_match
                
                # If no specific goal found, check conversation history for most recently mentioned goal
                if not goal_to_complete and req.conversation_history:
                    for msg in reversed(req.conversation_history[-10:]):
                        if isinstance(msg, dict):
                            msg_content = msg.get('content', '') or msg.get('message', '')
                        elif hasattr(msg, 'content'):
                            msg_content = getattr(msg, 'content', '')
                        else:
                            msg_content = str(msg)
                        
                        # Strip HTML
                        try:
                            if HAS_BS4:
                                soup = BeautifulSoup(msg_content, 'html.parser')
                                msg_content = soup.get_text(separator=' ', strip=True)
                            else:
                                msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                                msg_content = html.unescape(msg_content)
                        except:
                            msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                            msg_content = html.unescape(msg_content)
                        
                        msg_lower = msg_content.lower()
                        # Look for goal mentions
                        for goal in active_goals:
                            goal_text = goal.get("goal_text", "").lower()
                            goal_words = [w for w in goal_text.split() if len(w) > 3]
                            if goal_words and any(word in msg_lower for word in goal_words):
                                goal_to_complete = goal
                                break
                        
                        if goal_to_complete:
                            break
                
                # If still no goal found, use the most recent active goal
                if not goal_to_complete:
                    goal_to_complete = active_goals[0]
                
                # Update goal status to completed - CRITICAL: Ensure user_id filter is applied
                goal_id = goal_to_complete.get("goal_id")
                user_id_clean = req.user_id.strip()
                update_res = sb.table("goals").update({"status": "completed"}).eq("goal_id", goal_id).eq("user_id", user_id_clean).execute()
                print(f"✅ Marked goal '{goal_to_complete.get('goal_text', 'Unknown')}' as completed for user_id: {user_id_clean}")
                
                if update_res.data:
                    response_text = f"""✅ **Goal Marked as Completed!**

🎯 **Completed Goal:**
"{goal_to_complete.get('goal_text', 'Unknown')}"

🎉 Great job! You've achieved this goal. Keep up the excellent work!

💡 Ask me *"What are my goals?"* to see your remaining goals."""
                else:
                    response_text = "⚠️ Failed to update goal status. Please try again."
                
                return ChatResponse(response=response_text, sources=None)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ Error marking goal as completed: {str(e)}")
                print(f"   Full traceback:\n{error_trace}")
                return ChatResponse(
                    response=f"⚠️ Error updating goal: {str(e)}\n\n💡 Please try again or check server logs for details.",
                    sources=None
                )
        
        elif intent == "rag":
            # Use RAG for career knowledge
            rag_result = await query_career_knowledge(req.message, top_k=5)
            
            response_text = rag_result.get("answer", "I don't have information about that yet.")
            sources = rag_result.get("sources", [])
            
            # CRITICAL: Final HTML stripping pass (defense in depth)
            # Even though rag_service.py should have cleaned it, ensure no HTML remains
            import html as html_module
            
            original_response = response_text
            
            # Step 1: Remove sources-related HTML first (multiple passes)
            response_text = regex_module.sub(r'<br><br><small[^>]*>.*?[Ss]ources?.*?</small>', '', response_text, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            response_text = regex_module.sub(r'<small[^>]*>.*?[Ss]ources?.*?</small>', '', response_text, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            response_text = regex_module.sub(r'<[^>]+>.*?[Ss]ources?.*?</[^>]+>', '', response_text, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            response_text = regex_module.sub(r'📚\s*Sources?[:\s]*[^<\n]*', '', response_text, flags=regex_module.IGNORECASE)
            
            # Step 2: Convert <br> tags to newlines BEFORE removing other tags
            response_text = regex_module.sub(r'<br\s*/?>', '\n', response_text, flags=regex_module.IGNORECASE)
            
            # Step 3: Remove ALL remaining HTML tags (aggressive - catch everything)
            response_text = regex_module.sub(r'<[^>]+>', '', response_text)
            
            # Step 4: Decode HTML entities
            response_text = html_module.unescape(response_text)
            
            # Step 5: Clean up multiple newlines
            response_text = regex_module.sub(r'\n{3,}', '\n\n', response_text)
            
            # Step 6: Remove any remaining HTML entities
            response_text = regex_module.sub(r'&[a-zA-Z]+;', '', response_text)
            
            # Step 7: Final aggressive cleanup - remove any broken tags
            response_text = regex_module.sub(r'<[^>]*', '', response_text)
            
            response_text = response_text.strip()
            
            # Final check: if any HTML tags remain, log and remove them aggressively
            if '<' in response_text and '>' in response_text:
                print(f"❌ WARNING: HTML tags still present in RAG handler after cleaning!")
                print(f"   Original: {original_response[:100]}...")
                print(f"   Current: {response_text[:100]}...")
                # Last resort: remove everything between < and >
                response_text = regex_module.sub(r'<[^>]+>', '', response_text)
                response_text = regex_module.sub(r'<[^>]*', '', response_text)  # Catch broken tags
                response_text = response_text.strip()
            
            return ChatResponse(response=response_text, sources=sources)
        
        else:
            # Default: General chat with RAG
            # Check if this might be a skill gap question that wasn't detected
            message_lower = req.message.lower()
            if ('missing' in message_lower or 'skills' in message_lower) and ('resume' in message_lower or 'cv' in message_lower):
                # Try to route to skill gap analysis
                if req.user_id:
                    try:
                        res = sb.table("profiles").select("*").eq("user_id", req.user_id).execute()
                        if res.data:
                            # User has profile, try skill gap analysis
                            user_skills = res.data[0].get("skills", []) or []
                            # Search for job description in conversation
                            job_description = None
                            if req.conversation_history:
                                for msg in reversed(req.conversation_history):
                                    if isinstance(msg, dict):
                                        msg_role = msg.get('role', 'user')
                                        msg_content = msg.get('content', '') or msg.get('message', '')
                                    elif hasattr(msg, 'role'):
                                        msg_role = getattr(msg, 'role', 'user')
                                        msg_content = getattr(msg, 'content', '') or getattr(msg, 'message', '')
                                    else:
                                        msg_role = 'user'
                                        msg_content = str(msg)
                                    
                                    # Strip HTML
                                    try:
                                        if HAS_BS4:
                                            soup = BeautifulSoup(msg_content, 'html.parser')
                                            msg_content = soup.get_text(separator=' ', strip=True)
                                        else:
                                            msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                                            msg_content = html.unescape(msg_content)
                                    except:
                                        msg_content = regex_module.sub(r'<[^>]+>', ' ', msg_content)
                                        msg_content = html.unescape(msg_content)
                                    
                                    msg_text = msg_content.lower()
                                    jd_keywords = [
                                        'job description', 'job posting', 'skills required', 'required qualifications', 
                                        'we are looking', 'we are seeking', 'experience:', 'full-time', 'part-time', 
                                        'java developer', 'responsibilities', 'technical requirements', 'spring boot',
                                        'microservices', 'employment type', 'role category', 'greetings from',
                                        'job title:', 'venue:', 'date:', 'time:', 'experience range:', 'role:',
                                        'industry type:', 'department:', 'employment type:', 'role category:',
                                        'minimum qualification', 'education', 'key skills', 'preferred skills',
                                        'must have', 'should have', 'good to have', 'technical and professional requirements'
                                    ]
                                    if any(keyword in msg_text for keyword in jd_keywords) and len(msg_content) > 150:
                                        job_description = msg_content
                                        # Clean the job description text
                                        job_description = clean_job_description(job_description)
                                        break
                            
                            if job_description:
                                # Extract skills and perform gap analysis
                                skill_extract_prompt = ChatPromptTemplate.from_messages([
                                    ("system", """You are a technical recruiter extracting skills from a job description. 
Extract ALL technical skills, programming languages, frameworks, tools, and concepts mentioned. 
Return ONLY a JSON array of skills as strings."""),
                                    ("human", "Job Description:\n{job_description}\n\nExtract all skills and return as JSON array:")
                                ])
                                skill_extract_chain = skill_extract_prompt | llm
                                skills_result = await skill_extract_chain.ainvoke({"job_description": job_description})
                                skills_text = skills_result.content if hasattr(skills_result, 'content') else str(skills_result)
                                skills_text = regex_module.sub(r'```json\s*', '', skills_text)
                                skills_text = regex_module.sub(r'```\s*', '', skills_text)
                                skills_match = regex_module.search(r'\[.*?\]', skills_text, regex_module.DOTALL)
                                if skills_match:
                                    job_skills = json.loads(skills_match.group(0))
                                    
                                    # Perform gap analysis
                                    chain = get_skill_gap_chain()
                                    gap_result = await chain.ainvoke({
                                        "user_skills": json.dumps(user_skills),
                                        "job_skills": json.dumps(job_skills)
                                    })
                                    
                                    # Initialize variables
                                    matched = []
                                    gap = []
                                    
                                    if isinstance(gap_result, dict):
                                        matched = gap_result.get("matched", [])
                                        gap = gap_result.get("gap", [])
                                        if not gap and job_skills:
                                            user_skills_lower = [s.lower() for s in user_skills]
                                            gap = [js for js in job_skills if js.lower() not in user_skills_lower and not any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                                    else:
                                        # Fallback: manual computation
                                        user_skills_lower = [s.lower() for s in user_skills]
                                        matched = [js for js in job_skills if js.lower() in user_skills_lower or any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                                        gap = [js for js in job_skills if js.lower() not in user_skills_lower and not any(us.lower() in js.lower() or js.lower() in us.lower() for us in user_skills)]
                                    
                                    # Format response
                                    response_text = f"📊 **Skill Gap Analysis for the Job**\n\n"
                                    if matched:
                                        response_text += f"✅ **Skills You Have:**\n{', '.join(matched)}\n\n"
                                    if gap:
                                        response_text += f"❌ **Skills You Need to Develop:**\n{', '.join(gap)}\n\n"
                                        response_text += f"💡 **Recommendation:**\nFocus on developing: {', '.join(gap[:3])}"
                                    else:
                                        response_text += "✅ You have all the required skills!"
                                    
                                    return ChatResponse(response=response_text, sources=None)
                            else:
                                # No job description found, but user asked about resume
                                return ChatResponse(
                                    response="⚠️ I couldn't find a job description in our conversation. Please either:\n\n" +
                                            "• Paste a job description and ask again, OR\n" +
                                            "• Specify the role: \"What skills do I need for Data Scientist?\"",
                                    sources=None
                                )
                    except Exception as e:
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"⚠️ Error in fallback skill gap: {e}")
                        print(f"   Traceback: {error_trace}")
                        # Continue to default handler
            
            rag_result = await query_career_knowledge(req.message, top_k=3) if req.use_rag else {"answer": "", "sources": []}
            
            # Build conversation context
            context = ""
            if rag_result.get("sources"):
                context = "\n\nRelevant Career Information:\n"
                for source in rag_result["sources"]:
                    context += f"- {source.get('career_title', 'Unknown')}: {source.get('content_chunk', '')[:200]}...\n"
            
            # Build conversation history
            messages = []
            if req.conversation_history:
                for msg in req.conversation_history[-5:]:
                    # Handle both dict and Pydantic model formats
                    if isinstance(msg, dict):
                        msg_role = msg.get('role', 'user')
                        msg_content = msg.get('content', '')
                    elif hasattr(msg, 'role'):
                        msg_role = getattr(msg, 'role', 'user')
                        msg_content = getattr(msg, 'content', '')
                    else:
                        msg_role = 'user'
                        msg_content = str(msg)
                    messages.append((msg_role, msg_content))
            
            system_prompt = """You are 'Career Guidance', an expert AI Career Guidance Coach. 
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
- NEVER use HTML tags like <br>, <small>, <b>, <i>, <style>, or any inline CSS
- NEVER include sources, citations, or references in your answer
- Just provide the answer in clean Markdown format"""
            
            if context:
                system_prompt += f"\n\n{context}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                *messages,
                ("human", "{input}")
            ])
            
            chain = prompt | llm
            response = await chain.ainvoke({"input": req.message})
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # CRITICAL: Strip ALL HTML tags from response - return plain text only!
            # Same logic as RAG service - the frontend will handle formatting
            
            # Step 1: Remove sources-related HTML first
            answer = regex_module.sub(r'<br><br><small[^>]*>.*?[Ss]ources?.*?</small>', '', answer, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            answer = regex_module.sub(r'<small[^>]*>.*?[Ss]ources?.*?</small>', '', answer, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            answer = regex_module.sub(r'<[^>]+>.*?[Ss]ources?.*?</[^>]+>', '', answer, flags=regex_module.DOTALL | regex_module.IGNORECASE)
            answer = regex_module.sub(r'📚\s*Sources?[:\s]*[^<\n]*', '', answer, flags=regex_module.IGNORECASE)
            
            # Step 2: Convert <br> tags to newlines (preserve formatting)
            answer = regex_module.sub(r'<br\s*/?>', '\n', answer, flags=regex_module.IGNORECASE)
            # Step 3: Remove ALL remaining HTML tags
            answer = regex_module.sub(r'<[^>]+>', '', answer)
            # Step 4: Decode HTML entities
            answer = html.unescape(answer)
            # Step 5: Clean up multiple newlines
            answer = regex_module.sub(r'\n{3,}', '\n\n', answer)
            answer = answer.strip()
            
            return ChatResponse(
                response=answer,
                sources=rag_result.get("sources") if req.use_rag else None
            )
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        # Log the full error for debugging
        print(f"❌ Unhandled error in chat endpoint: {str(e)}")
        print(f"   Full traceback:\n{error_trace}")
        # Return more detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}\n\nCheck server logs for full traceback."
        )


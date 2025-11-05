import json
import re
import os
from typing import Dict, Any
from app.llm.gemini_client import get_gemini_llm, create_resume_parser_prompt

# PDF/DOCX text extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    try:
        import PyPDF2
        PYPDF2_AVAILABLE = True
    except ImportError:
        PYPDF2_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    DocxDocument = None


async def parse_resume_text(resume_text: str) -> Dict[str, Any]:
    """
    Parse resume text using LLM extraction.
    Returns structured data: name, email, experience, skills
    """
    # Use LLM to extract structured data from text
    llm = get_gemini_llm(temperature=0.1)  # Low temperature for structured extraction
    prompt = create_resume_parser_prompt()
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"resume_text": resume_text})
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response (might have markdown code blocks)
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from code block: {e}")
                parsed_data = {}
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    parsed_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON object: {e}")
                    parsed_data = {}
            else:
                # Try to parse directly
                try:
                    parsed_data = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse content as JSON: {e}, content: {content[:200]}")
                    parsed_data = {}
        
        # Additional skill extraction from text if LLM missed it
        if not parsed_data.get("skills") or len(parsed_data.get("skills", [])) == 0:
            # Try to extract skills from text using simple keyword matching
            skill_keywords = ["Python", "JavaScript", "Java", "React", "Node.js", "SQL", "Git", "Docker", 
                            "AWS", "Machine Learning", "Data Science", "TypeScript", "Angular", "Vue",
                            "MongoDB", "PostgreSQL", "Django", "Flask", "Spring", "Kubernetes"]
            found_skills = []
            text_lower = resume_text.lower()
            for skill in skill_keywords:
                if skill.lower() in text_lower:
                    found_skills.append(skill)
            if found_skills:
                parsed_data["skills"] = found_skills
                
    except Exception as e:
        # Fallback: basic extraction
        print(f"LLM parsing failed, using fallback: {e}")
        parsed_data = extract_basic_info(resume_text)
    
    # Ensure required fields
    if "name" not in parsed_data:
        parsed_data["name"] = ""
    if "email" not in parsed_data:
        parsed_data["email"] = extract_email(resume_text) or "unknown@example.com"
    if "experience" not in parsed_data:
        parsed_data["experience"] = ""
    if "skills" not in parsed_data:
        parsed_data["skills"] = []
    
    # Normalize skills to list of strings
    if isinstance(parsed_data["skills"], str):
        parsed_data["skills"] = [s.strip() for s in parsed_data["skills"].split(",")]
    
    return parsed_data


def extract_email(text: str) -> str | None:
    """Extract email from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    
    # Try pdfplumber first (better for tables/layouts)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"pdfplumber failed, trying PyPDF2: {e}")
    
    # Fallback to PyPDF2
    if PYPDF2_AVAILABLE:
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    raise Exception("No PDF extraction library available. Please install pdfplumber or PyPDF2.")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    if not DOCX_AVAILABLE:
        raise Exception("python-docx not available. Please install it: pip install python-docx")
    
    try:
        doc = DocxDocument(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")


async def parse_resume_file(file_path: str) -> Dict[str, Any]:
    """
    Parse resume file (PDF/DOCX) by extracting text and using LLM parsing.
    Returns structured data: name, email, experience, skills
    """
    try:
        # Extract text based on file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            resume_text = extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            resume_text = extract_text_from_docx(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_ext}")
        
        if not resume_text or len(resume_text.strip()) < 10:
            raise Exception("Could not extract text from file. File may be corrupted or empty.")
        
        # Use LLM to parse the extracted text
        return await parse_resume_text(resume_text)
        
    except Exception as e:
        raise Exception(f"Failed to parse resume file: {str(e)}")


def extract_basic_info(text: str) -> Dict[str, Any]:
    """Fallback: basic extraction if LLM fails."""
    email = extract_email(text) or "unknown@example.com"
    
    # Try to find name (first line or after "Name:")
    lines = text.split('\n')
    name = ""
    for line in lines[:5]:  # Check first few lines
        line = line.strip()
        if line and not '@' in line and len(line) < 50:
            name = line
            break
    
    return {
        "name": name,
        "email": email,
        "experience": text[:500] if len(text) > 500 else text,  # First 500 chars
        "skills": []  # Empty, will need manual input or better parsing
    }


"""
Intent detection service to route user messages to appropriate features.
"""
import re
from typing import Dict, Optional, Any


def detect_intent(message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect user intent from message and return intent type + extracted data.
    
    Returns:
        {
            "intent": "career_recommendation" | "skill_gap" | "job_fit" | "goal_set" | "goal_list" | "resume_parse" | "rag" | "chat",
            "extracted_data": {...}
        }
    """
    message_lower = message.lower().strip()
    
    # PRIORITY 0: Goal Setting Intent (check FIRST if "goal" or "goals" mentioned to avoid confusion)
    # Check for goal-related phrases early to catch "add to goals" before other intents
    # But exclude if it says "resume" - that's a different intent
    if 'goal' in message_lower and ('add' in message_lower or 'set' in message_lower or 'create' in message_lower) and 'resume' not in message_lower:
        goal_set_patterns_early = [
            r'\b(?:add|put)\s+(?:the\s+)?(?:skills?|missing|required)\s+(?:required\s+)?(?:to\s+develop|needed)?\s+(?:to|as|into)\s+(?:my\s+)?goals?',
            r'\b(?:add|put)\s+(?:the\s+)?(?:need|missing|required)\s+to\s+develop\s+skills?\s+(?:to|in|into)\s+(?:my\s+)?goals?',
            r'\b(?:add|put)\s+.*?\s+(?:to|as|into)\s+(?:my\s+)?goals?',
            r'\b(?:set|create|add|make)\s+(?:a|me a|my|up)?\s+goals?\s+(?:to|of|for|them)?',
        ]
        for pattern in goal_set_patterns_early:
            if re.search(pattern, message_lower):
                return {
                    "intent": "goal_set",
                    "extracted_data": {
                        "user_id": user_id,
                        "goal_text": "from_context"
                    }
                }
    
    # PRIORITY 1: Job Fit Analysis Intent (check BEFORE resume to avoid confusion)
    # Patterns: "job fit", "how well do I fit", "analyze this job", "match this job"
    job_fit_patterns = [
        r'\b(?:how\s+well\s+)?(?:do I|would I|will I)\s+fit\s+(?:this|for)\s+(?:job|role|position)',
        r'\b(?:job|role|position)\s+(?:fit|match|analysis)',
        r'\b(?:analyze|check|assess)\s+(?:this|my fit for|my match for)\s+(?:job|role|position)',
        r'\b(?:fit|match)\s+score\s+(?:for|of)',
    ]
    # Strong job description indicators (check these first)
    strong_jd_keywords = [
        'job description', 'job posting', 'we are looking for', 'we are seeking',
        'apply now', 'about the role', 'about this position', 'position summary',
        'required qualifications', 'required skills', 'must have', 'nice to have',
        'key responsibilities', 'primary responsibilities', 'what you\'ll do',
        'what you will do', 'role overview', 'company overview', 'location:',
        'salary range', 'benefits package', 'employment type', 'full-time', 'part-time',
        'years of experience required', 'experience level', 'senior', 'junior', 'mid-level'
    ]
    is_job_description = any(keyword in message_lower for keyword in strong_jd_keywords)
    
    # Check for job fit patterns OR text with job description keywords
    # If it has strong JD keywords, treat as job description even if short
    if any(re.search(pattern, message_lower) for pattern in job_fit_patterns) or \
       (len(message) > 150 and is_job_description) or \
       (is_job_description and len(message) > 100):
        return {
            "intent": "job_fit",
            "extracted_data": {
                "user_id": user_id,
                "job_description": message
            }
        }
    
    # 1. Resume/CV Parsing Intent
    # Patterns: "parse my resume", "analyze my cv", "here's my resume", etc.
    resume_patterns = [
        r'\b(?:parse|analyze|upload|read|process)\s+(?:my|the)\s+(?:resume|cv|curriculum vitae)\b',
        r'\b(?:here|this)\s+is\s+my\s+(?:resume|cv)\b',
        r'resume\s+(?:below|attached|here)',
        r'my\s+(?:resume|cv)\s+(?:is|below|attached)',
    ]
    if any(re.search(pattern, message_lower) for pattern in resume_patterns):
        return {
            "intent": "resume_parse",
            "extracted_data": {"resume_text": message}
        }
    
    # Check if message looks like resume text (long text with resume-specific keywords)
    # Exclude job description keywords to avoid confusion
    resume_keywords = ['objective', 'summary', 'work history', 'professional summary',
                      'career objective', 'professional experience', 'work experience',
                      'education background', 'academic background', 'projects', 'achievements']
    # Only treat as resume if it has resume keywords AND NOT job description keywords
    if len(message) > 200 and any(keyword in message_lower for keyword in resume_keywords) and not is_job_description:
        return {
            "intent": "resume_parse",
            "extracted_data": {"resume_text": message}
        }
    
    # 2. Career Path Recommendation Intent
    # Patterns: "what careers", "recommend careers", "suggest careers", "what should I do"
    career_patterns = [
        r'\b(?:what|which|suggest|recommend|tell me about)\s+(?:careers?|career paths?|jobs?)\s+(?:are|would be|should I)\s+(?:good|best|suitable|for me)',
        r'\b(?:what|which)\s+(?:should I|can I)\s+(?:do|become|pursue)',
        r'\b(?:career|job)\s+(?:recommendation|suggestion|advice)',
        r'\b(?:based on|according to)\s+my\s+(?:profile|skills|experience)',
        r'\b(?:recommend|suggest|tell me about)\s+(?:careers?|career paths?|jobs?)\s+(?:based on|according to)\s+my\s+(?:profile|skills|experience)',
        r'\b(?:recommend|suggest)\s+(?:careers?|career paths?|jobs?)\s+(?:for me|to me)',
    ]
    if any(re.search(pattern, message_lower) for pattern in career_patterns):
        return {
            "intent": "career_recommendation",
            "extracted_data": {"user_id": user_id}
        }
    
    # 3. Skill Gap Analysis Intent
    # Patterns: "skill gap", "what skills do I need", "analyze my skills for X", "what's missing"
    skill_gap_patterns = [
        r'\b(?:what|which)\s+skills?\s+(?:do I|would I|should I)\s+need\s+(?:for|to become|to be)',
        r'\b(?:analyze|check|compare)\s+my\s+skills?\s+(?:for|against)',
        r'\b(?:skill|skills?)\s+gap\s+(?:for|in)',
        r'\b(?:what|which)\s+(?:am I missing|lacking|need)\s+(?:for|to)',
        r'\b(?:compare|analyze)\s+(?:my\s+)?skills?\s+(?:with|for)',
        r'\b(?:what|which)\s+(?:is|are)\s+(?:it|missing|lacking)\s+(?:in|from)\s+(?:my\s+|the\s+)?(?:resume|cv)',
        r'\b(?:what|which)\s+(?:is|are)\s+missing\s+(?:in|from)\s+(?:my\s+|the\s+)?(?:resume|cv)',
        r'\b(?:what|which)\s+(?:skills?|is|are)\s+missing\s+(?:in|from)\s+(?:my\s+|the\s+)?(?:resume|cv)',
        r'\b(?:what|which)\s+(?:are|is)\s+missing\s+in\s+(?:the\s+)?(?:resume|cv)',
        r'\b(?:what|which)\s+(?:are|is)\s+missing\s+(?:in|from)\s+(?:the|my)\s+(?:resume|cv)',
        r'\b(?:what|which)\s+(?:do I|am I)\s+missing\s+(?:for|to apply for|in)',
        r'\b(?:to apply for|for this role|for this job|for the above)\s+(?:what|which)\s+(?:is|are)\s+(?:missing|needed)',
        r'\b(?:what|which)\s+(?:is|are)\s+(?:missing|needed|required)\s+(?:for|to apply for|in my resume)',
        r'\b(?:missing|needed)\s+(?:from|in)\s+(?:my\s+|the\s+)?(?:resume|cv)',
        r'\b(?:what\s+)?skills?\s+(?:are\s+)?missing\s+(?:from|in)',
        r'\b(?:what\s+skills?\s+are\s+missing)',
        r'\b(?:what|which)\s+(?:are|is)\s+missing\s+(?:in|from)\s+(?:the\s+)?(?:resume|cv)',
    ]
    skill_gap_match = None
    is_skill_gap_question = False
    
    for pattern in skill_gap_patterns:
        match = re.search(pattern, message_lower)
        if match:
            is_skill_gap_question = True
            # Extract target career/job from message
            # Look for "for Data Scientist", "to become Software Engineer", "for this role", etc.
            target_match = re.search(r'(?:for|to become|to be|this role|this job|the above|the job)\s+([a-zA-Z\s]+?)(?:\?|\.|$)', message_lower[match.end():])
            if target_match:
                skill_gap_match = target_match.group(1).strip()
            # Also check for "for this role" or "for the above" (referring to previous job description)
            if not skill_gap_match:
                if 'this role' in message_lower or 'this job' in message_lower or 'the above' in message_lower or 'the job' in message_lower:
                    skill_gap_match = "previous_job_description"  # Special marker to use conversation context
            # If no specific job mentioned and question is about resume, default to previous job description
            if not skill_gap_match and ('resume' in message_lower or 'cv' in message_lower or 'missing' in message_lower):
                skill_gap_match = "previous_job_description"
            print(f"🔍 Skill gap intent detected. Target: {skill_gap_match or 'previous_job_description'}")
            break
    
    if is_skill_gap_question:
        return {
            "intent": "skill_gap",
            "extracted_data": {
                "user_id": user_id,
                "target_career": skill_gap_match or "previous_job_description"
            }
        }
    
    # 5. Goal Setting Intent
    # Patterns: "set a goal", "help me learn", "create goal", "set up goals", "set goals for", "add skills to goals"
    goal_set_patterns = [
        r'\b(?:set|create|add|make)\s+(?:a|me a|my|up)?\s+goals?\s+(?:to|of|for|them)?',
        r'\b(?:set|create|add|make)\s+(?:up\s+)?goals?\s+for',
        r'\b(?:add|put)\s+(?:the\s+)?(?:skills?|missing|required)\s+(?:required\s+)?(?:to\s+develop|needed)?\s+(?:to|as|into)\s+(?:my\s+)?goals?',
        r'\b(?:add|put)\s+(?:the\s+)?(?:need|missing|required)\s+to\s+develop\s+skills?\s+(?:to|in|into)\s+(?:my\s+)?goals?',
        r'\b(?:add|put)\s+.*?\s+(?:to|as|into)\s+(?:my\s+)?goals?',
        r'\b(?:add)\s+(?:\d+)?\s*(?:need|missing|required)?\s*to\s+develop\s+skills?\s+(?:in|to|as|into)\s+(?:my\s+)?goals?',
        r'\b(?:add)\s+(?:\d+)?\s*(?:skills?|need|missing|required)\s+(?:to|in)\s+(?:my\s+)?goals?',
        r'\b(?:help me|I want to|I need to)\s+(?:learn|master|improve|develop)',
        r'\b(?:goal|target)\s+(?:to|of|for)',
        r'\b(?:set|create)\s+goals?\s+(?:for|to learn)',
        r'\b(?:set|create)\s+goals?\s+(?:for|from)\s+(?:the\s+)?(?:missing|gap)',
    ]
    goal_match = None
    is_goal_set_question = False
    
    for pattern in goal_set_patterns:
        match = re.search(pattern, message_lower)
        if match:
            is_goal_set_question = True
            # Check for context references FIRST - expanded list
            if any(phrase in message_lower for phrase in [
                'for them', 'for it', 'for these', 'for the missing', 
                'from them', 'from the skill gap', 'from skill gap analysis',
                'from the gap', 'from this', 'from that', 'from these',
                'missing skills', 'gap analysis', 'skill gap',
                'skills required to develop', 'required to develop', 'skills to develop',
                'need to develop', 'to develop', 'need to develop skills',
                'the skills', 'these skills', 'those skills'
            ]):
                goal_match = "from_context"  # Special marker to use conversation context
            # Also check if message contains "add [something] to goals"
            elif 'add' in message_lower and 'goal' in message_lower and ('skill' in message_lower or 'develop' in message_lower):
                goal_match = "from_context"
            # Check for "add X need to develop skills in goals"
            elif 'add' in message_lower and ('need' in message_lower or 'missing' in message_lower) and 'develop' in message_lower and 'skill' in message_lower:
                goal_match = "from_context"
            else:
                # Extract goal text (everything after "to learn", "to master", "to study", etc. or just skill name)
                # Try to find "learn X", "master X", "study X", etc.
                skill_extraction_patterns = [
                    r'\b(?:to|want to|need to|wanna|gonna)\s+(?:learn|master|study|improve|get better at|understand)\s+(.+?)(?:\.|$|,|\s+and)',
                    r'\b(?:learn|master|study|improve|get better at|understand)\s+(.+?)(?:\.|$|,|\s+and)',
                    r'(?:to|for)\s+(.+?)(?:\.|$|,|\s+and)',  # Fallback: everything after "to" or "for"
                ]
                for pattern_extract in skill_extraction_patterns:
                    goal_text_match = re.search(pattern_extract, message_lower[match.start():])
                    if goal_text_match:
                        goal_match = goal_text_match.group(1).strip()
                        # Remove trailing "them", "it", "these" if present
                        if goal_match.endswith((' them', ' it', ' these', ' those')):
                            goal_match = goal_match.rsplit(' ', 1)[0].strip()
                        break
            break
    
    if is_goal_set_question:
        return {
            "intent": "goal_set",
            "extracted_data": {
                "user_id": user_id,
                "goal_text": goal_match or "from_context"
            }
        }
    
    # 6. Goal List Intent
    # Patterns: "my goals", "list goals", "show goals", "what are my goals"
    goal_list_patterns = [
        r'\b(?:show|list|tell me|what are)\s+(?:my|the)?\s+goals?',
        r'\b(?:my|all)\s+goals?',
        r'\b(?:track|view|see)\s+(?:my\s+)?goals?',
    ]
    if any(re.search(pattern, message_lower) for pattern in goal_list_patterns):
        return {
            "intent": "goal_list",
            "extracted_data": {"user_id": user_id}
        }
    
    # 7. Goal Completion Intent
    # Patterns: "mark as complete", "completed", "done", "finished", "achieve"
    goal_complete_patterns = [
        r'\b(?:mark|set|make)\s+(?:as|it)\s+(?:complete|completed|done|finished)',
        r'\b(?:completed|complete|done|finished|achieved)\b',
        r'\b(?:mark|marking)\s+(?:goal|it)\s+(?:as|as a)\s+(?:complete|completed|done)',
        r'\b(?:I\s+)?(?:have\s+)?(?:completed|finished|done|achieved)\s+(?:this|it|the goal)',
    ]
    
    # Check if message is just "completed" or "done" - likely referring to a goal
    if message_lower.strip() in ['completed', 'done', 'finished', 'complete']:
        return {
            "intent": "goal_complete",
            "extracted_data": {
                "user_id": user_id
            }
        }
    
    # Check for completion patterns
    for pattern in goal_complete_patterns:
        match = re.search(pattern, message_lower)
        if match:
            return {
                "intent": "goal_complete",
                "extracted_data": {
                    "user_id": user_id
                }
            }
    
    # 8. RAG Intent (general career questions)
    # Default to RAG for career-related questions
    career_question_keywords = [
        'job outlook', 'salary', 'day to day', 'what is', 'tell me about',
        'career in', 'become', 'how to', 'outlook for', 'future of'
    ]
    
    if any(keyword in message_lower for keyword in career_question_keywords) or \
       message_lower.endswith('?') or \
       message_lower.startswith(('what', 'how', 'why', 'when', 'where', 'tell me', 'explain')):
        return {
            "intent": "rag",
            "extracted_data": {"query": message}
        }
    
    # 8. Default: General chat
    return {
        "intent": "chat",
        "extracted_data": {}
    }


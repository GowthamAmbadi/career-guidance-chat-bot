"""
Text processing utilities for HTML stripping and job description cleaning.
"""
import re
import html


def strip_html_tags(text: str) -> str:
    """
    Strip ALL HTML tags from text using multiple passes for thorough cleaning.
    This is the same logic used in both RAG service and chat router.
    
    Args:
        text: Text that may contain HTML tags
        
    Returns:
        Clean text with all HTML tags removed
    """
    if not text:
        return ""
    
    # Step 1: Remove sources-related HTML first (multiple passes)
    text = re.sub(r'<br><br><small[^>]*>.*?[Ss]ources?.*?</small>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<small[^>]*>.*?[Ss]ources?.*?</small>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>.*?[Ss]ources?.*?</[^>]+>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'📚\s*Sources?[:\s]*[^<\n]*', '', text, flags=re.IGNORECASE)
    
    # Step 2: Convert <br> tags to newlines (preserve formatting)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Step 3: Remove ALL remaining HTML tags (aggressive - catch everything)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Step 4: Decode HTML entities
    text = html.unescape(text)
    
    # Step 5: Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Step 6: Remove any remaining HTML entities that might have been missed
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    
    return text.strip()


def clean_job_description(jd_text: str) -> str:
    """
    Clean and normalize job description text.
    - Fixes skills that are run together (e.g., "JavaHibernateSpring Boot" -> "Java, Hibernate, Spring Boot")
    - Adds proper spacing and formatting
    - Removes excessive whitespace
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        Cleaned and normalized job description text
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


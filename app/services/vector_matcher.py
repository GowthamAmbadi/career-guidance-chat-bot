"""
Vector matching service for profile-to-job and profile-to-career similarity calculations.
"""
from typing import List
import numpy as np
from app.llm.embeddings import embed_texts
from app.utils.profile_utils import build_profile_text


def calculate_profile_similarity(
    user_embedding: List[float], 
    job_embedding: List[float]
) -> float:
    """
    Calculate cosine similarity between user profile and job description embeddings.
    
    Args:
        user_embedding: User profile embedding vector
        job_embedding: Job description embedding vector
    
    Returns:
        Similarity score between 0 and 1 (1 = perfect match, 0 = no match)
    """
    user_arr = np.array(user_embedding)
    job_arr = np.array(job_embedding)
    
    # Calculate cosine similarity
    dot_product = np.dot(user_arr, job_arr)
    norm_user = np.linalg.norm(user_arr)
    norm_job = np.linalg.norm(job_arr)
    
    if norm_user == 0 or norm_job == 0:
        return 0.0
    
    similarity = dot_product / (norm_user * norm_job)
    return float(similarity)


def generate_job_embedding(job_description: str) -> List[float]:
    """
    Generate embedding for job description.
    
    Args:
        job_description: Job description text
    
    Returns:
        Embedding vector (1536 dimensions)
    """
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty")
    
    embedding = embed_texts([job_description])[0]
    return embedding


def generate_profile_embedding(
    name: str, 
    experience: str, 
    skills: List[str]
) -> List[float]:
    """
    Generate embedding for user profile.
    
    Args:
        name: User's name
        experience: Experience summary text
        skills: List of skill strings
    
    Returns:
        Embedding vector (1536 dimensions)
    """
    profile_text = build_profile_text(name, experience, skills)
    
    if not profile_text.strip():
        raise ValueError("Profile text cannot be empty")
    
    embedding = embed_texts([profile_text])[0]
    return embedding


def generate_skill_embeddings(skills: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of skills.
    Each skill gets its own embedding vector for semantic matching.
    
    Args:
        skills: List of skill strings (e.g., ["Python", "React", "SQL"])
    
    Returns:
        List of embedding vectors, one per skill (each 1536 dimensions)
    """
    if not skills:
        return []
    
    # Filter out empty skills
    valid_skills = [skill.strip() for skill in skills if skill and skill.strip()]
    
    if not valid_skills:
        return []
    
    # Generate embeddings for all skills in one batch (more efficient)
    embeddings = embed_texts(valid_skills)
    return embeddings


def calculate_skill_similarity(
    skill1_embedding: List[float],
    skill2_embedding: List[float]
) -> float:
    """
    Calculate cosine similarity between two skill embeddings.
    
    Args:
        skill1_embedding: First skill embedding vector
        skill2_embedding: Second skill embedding vector
    
    Returns:
        Similarity score between 0 and 1 (1 = identical, 0 = no match)
    """
    skill1_arr = np.array(skill1_embedding)
    skill2_arr = np.array(skill2_embedding)
    
    # Calculate cosine similarity
    dot_product = np.dot(skill1_arr, skill2_arr)
    norm1 = np.linalg.norm(skill1_arr)
    norm2 = np.linalg.norm(skill2_arr)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return float(similarity)


def find_matching_skills(
    user_skill_embeddings: List[List[float]],
    job_skill_embeddings: List[List[float]],
    similarity_threshold: float = 0.7
) -> tuple[List[str], List[str], List[tuple[str, str, float]]]:
    """
    Find matching skills between user and job using vector similarity.
    
    Args:
        user_skill_embeddings: List of user skill embeddings
        job_skill_embeddings: List of job skill embeddings
        similarity_threshold: Minimum similarity to consider a match (default 0.7)
    
    Returns:
        Tuple of:
        - matched_skills: List of matched skill names (from user's perspective)
        - missing_skills: List of unmatched job skills
        - matches: List of (user_skill, job_skill, similarity) tuples
    """
    if not user_skill_embeddings or not job_skill_embeddings:
        return [], [], []
    
    matched_skills = []
    missing_skills = []
    matches = []
    matched_job_indices = set()
    
    # For each user skill, find the best matching job skill
    for i, user_emb in enumerate(user_skill_embeddings):
        best_match_idx = -1
        best_similarity = 0.0
        
        for j, job_emb in enumerate(job_skill_embeddings):
            similarity = calculate_skill_similarity(user_emb, job_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = j
        
        # If similarity is above threshold, it's a match
        if best_similarity >= similarity_threshold and best_match_idx >= 0:
            matched_skills.append(f"skill_{i}")  # Placeholder, will be replaced with actual skill names
            matched_job_indices.add(best_match_idx)
            matches.append((f"user_skill_{i}", f"job_skill_{best_match_idx}", best_similarity))
    
    # Job skills that weren't matched are missing
    for j in range(len(job_skill_embeddings)):
        if j not in matched_job_indices:
            missing_skills.append(f"job_skill_{j}")  # Placeholder
    
    return matched_skills, missing_skills, matches


def match_skills_semantic(
    user_skills: List[str],
    user_skill_embeddings: List[List[float]],
    job_skills: List[str],
    job_skill_embeddings: List[List[float]],
    similarity_threshold: float = 0.7
) -> dict:
    """
    Match user skills to job skills using semantic similarity.
    
    Args:
        user_skills: List of user skill names
        user_skill_embeddings: List of user skill embeddings (aligned with user_skills)
        job_skills: List of job skill names
        job_skill_embeddings: List of job skill embeddings (aligned with job_skills)
        similarity_threshold: Minimum similarity to consider a match (default 0.7)
    
    Returns:
        Dictionary with:
        - matched: List of (user_skill, job_skill, similarity) tuples
        - missing: List of unmatched job skills
        - matched_user_skills: List of user skills that matched
    """
    if not user_skill_embeddings or not job_skill_embeddings:
        return {
            "matched": [],
            "missing": job_skills if job_skills else [],
            "matched_user_skills": []
        }
    
    matched = []
    matched_user_indices = set()
    matched_job_indices = set()
    
    # For each user skill, find the best matching job skill
    for i, user_emb in enumerate(user_skill_embeddings):
        if i >= len(user_skills):
            continue
            
        best_match_idx = -1
        best_similarity = 0.0
        
        for j, job_emb in enumerate(job_skill_embeddings):
            if j >= len(job_skills):
                continue
                
            similarity = calculate_skill_similarity(user_emb, job_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = j
        
        # If similarity is above threshold, it's a match
        if best_similarity >= similarity_threshold and best_match_idx >= 0:
            matched.append((user_skills[i], job_skills[best_match_idx], best_similarity))
            matched_user_indices.add(i)
            matched_job_indices.add(best_match_idx)
    
    # Job skills that weren't matched are missing
    missing = [job_skills[j] for j in range(len(job_skills)) if j not in matched_job_indices]
    matched_user_skills = [user_skills[i] for i in matched_user_indices]
    
    return {
        "matched": matched,
        "missing": missing,
        "matched_user_skills": matched_user_skills
    }


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


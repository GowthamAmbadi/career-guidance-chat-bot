"""
Utility functions for building profile text for embeddings.
"""
from typing import List
import json


def build_profile_text(name: str, experience: str, skills: List[str]) -> str:
    """
    Build comprehensive profile text for embedding.
    Combines name, experience, and skills into a single text.
    
    Args:
        name: User's name
        experience: Experience summary text
        skills: List of skill strings
    
    Returns:
        Formatted profile text string
    """
    profile_parts = []
    
    if name:
        profile_parts.append(f"Name: {name}")
    
    if experience:
        profile_parts.append(f"Experience: {experience}")
    
    if skills:
        skills_text = ", ".join(skills)
        profile_parts.append(f"Skills: {skills_text}")
    
    return "\n".join(profile_parts)


def format_skill_embeddings_for_postgres(embeddings: List[List[float]]) -> List[List[float]]:
    """
    Format skill embeddings for PostgreSQL vector array type.
    
    Returns the raw list of lists. The caller should use RPC to update
    via the update_skills_embeddings function if direct upsert fails.
    
    Args:
        embeddings: List of embedding vectors (each is a list of floats)
    
    Returns:
        List of lists (raw format)
    """
    if not embeddings:
        return None
    
    # Return raw list of lists
    return embeddings


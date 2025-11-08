"""
Utility functions for building profile text for embeddings.
"""
from typing import List


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


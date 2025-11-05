from fastapi import APIRouter, HTTPException
from app.clients.supabase_client import get_supabase_client
from app.llm.chains import get_career_recommendation_chain
import json


router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/careers")
async def recommend_careers(user_id: str):
    """
    Recommend career paths based on user's profile (skills and experience).
    """
    sb = get_supabase_client()
    
    # Fetch user profile
    res = sb.table("profiles").select("*").eq("user_id", user_id).execute()
    
    if not res.data or len(res.data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found for user_id: {user_id}. Please parse your resume first."
        )
    
    profile = res.data[0]
    skills = profile.get("skills", []) or []
    experience = profile.get("experience_summary", "") or ""
    
    if not skills and not experience:
        raise HTTPException(
            status_code=400,
            detail="Profile has no skills or experience. Please parse your resume first."
        )
    
    # Get career recommendation chain
    chain = get_career_recommendation_chain()
    
    try:
        result = await chain.ainvoke({
            "skills": json.dumps(skills) if isinstance(skills, list) else str(skills),
            "experience": experience
        })
        
        # Handle different response formats
        if isinstance(result, dict) and "careers" in result:
            careers = result["careers"]
        elif isinstance(result, list):
            careers = result
        else:
            careers = [result] if result else []
        
        return {"careers": careers}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating career recommendations: {str(e)}"
        )



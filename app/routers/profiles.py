from fastapi import APIRouter, HTTPException
from app.clients.supabase_client import get_supabase_client
from app.models.schemas import Profile, ResumeParsed
from typing import Optional


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/upsert", response_model=Profile)
def upsert_profile(user_id: str, parsed: ResumeParsed):
    sb = get_supabase_client()
    res = (
        sb.table("profiles")
        .upsert(
            {
                "user_id": user_id,
                "name": parsed.name,
                "email": parsed.email,
                "experience_summary": parsed.experience,
                "skills": parsed.skills,
            }
        )
        .execute()
    )
    data = res.data[0]
    return Profile(
        user_id=data["user_id"],
        name=data.get("name"),
        email=data.get("email"),
        experience_summary=data.get("experience_summary"),
        skills=data.get("skills"),
    )


@router.get("/debug/{user_id}")
def debug_profile(user_id: str):
    """Debug endpoint to check if profile exists and what data is stored."""
    sb = get_supabase_client()
    
    # Check if profile exists
    res = sb.table("profiles").select("*").eq("user_id", user_id).execute()
    
    # Get all profiles (limit 5)
    all_res = sb.table("profiles").select("user_id, name").limit(5).execute()
    
    return {
        "searched_user_id": user_id,
        "found": len(res.data) > 0 if res.data else False,
        "profile": res.data[0] if res.data else None,
        "all_profiles_in_db": all_res.data if all_res.data else [],
        "total_count": len(all_res.data) if all_res.data else 0
    }



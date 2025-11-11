from fastapi import APIRouter
from app.clients.supabase_client import get_supabase_client
from app.models.schemas import Profile, ResumeParsed
from app.services.vector_matcher import generate_profile_embedding


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/upsert", response_model=Profile)
def upsert_profile(user_id: str, parsed: ResumeParsed):
    sb = get_supabase_client()
    
    # Check if profile exists to determine if we need to regenerate embedding
    existing_profile = sb.table("profiles").select("*").eq("user_id", user_id).execute()
    
    # Check if profile data changed (optimization: only regenerate if changed)
    needs_embedding_regeneration = True
    if existing_profile.data:
        existing = existing_profile.data[0]
        if (existing.get("name") == parsed.name and 
            existing.get("experience_summary") == parsed.experience and
            existing.get("skills") == parsed.skills):
            # Data hasn't changed, keep existing embedding if it exists
            needs_embedding_regeneration = False
    
    # Generate profile embedding if needed
    profile_embedding = None
    if needs_embedding_regeneration:
        try:
            profile_embedding = generate_profile_embedding(
                name=parsed.name or "",
                experience=parsed.experience or "",
                skills=parsed.skills or []
            )
            print(f"✅ Generated profile embedding for user_id: {user_id}")
        except Exception as e:
            print(f"⚠️ Error generating profile embedding: {e}")
            # Continue without embedding - profile will be saved without it
            # If existing profile has embedding, we'll keep it (don't set to None)
            if existing_profile.data and existing_profile.data[0].get("profile_embedding"):
                profile_embedding = existing_profile.data[0].get("profile_embedding")
    else:
        # Keep existing embedding if data hasn't changed
        if existing_profile.data and existing_profile.data[0].get("profile_embedding"):
            profile_embedding = existing_profile.data[0].get("profile_embedding")
    
    # Prepare profile data
    profile_data = {
        "user_id": user_id,
        "name": parsed.name,
        "email": parsed.email,
        "experience_summary": parsed.experience,
        "skills": parsed.skills,
    }
    
    # Only add embedding if we have one (don't overwrite with None if existing has one)
    if profile_embedding is not None:
        profile_data["profile_embedding"] = profile_embedding
    
    res = (
        sb.table("profiles")
        .upsert(profile_data)
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





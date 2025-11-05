from fastapi import APIRouter
from app.clients.supabase_client import get_supabase_client
from app.models.schemas import Profile, ResumeParsed


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





from fastapi import APIRouter, Depends
from typing import List
from app.models.schemas import GoalCreate, Goal
from app.clients.supabase_client import get_supabase_client


router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("/", response_model=Goal)
def create_goal(user_id: str, payload: GoalCreate):
    sb = get_supabase_client()
    res = (
        sb.table("goals")
        .insert({"user_id": user_id, "goal_text": payload.goal_text})
        .execute()
    )
    data = res.data[0]
    return Goal(
        goal_id=data["goal_id"],
        user_id=data["user_id"],
        goal_text=data["goal_text"],
        status=data["status"],
    )


@router.get("/", response_model=List[Goal])
def list_goals(user_id: str):
    sb = get_supabase_client()
    res = sb.table("goals").select("*").eq("user_id", user_id).execute()
    return [
        Goal(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            goal_text=row["goal_text"],
            status=row["status"],
        )
        for row in res.data
    ]

from pydantic import BaseModel, EmailStr
from typing import List, Optional


class ResumeParsed(BaseModel):
    name: str
    email: EmailStr
    experience: str
    skills: List[str]


class Profile(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    experience_summary: Optional[str] = None
    skills: Optional[List[str]] = None


class GoalCreate(BaseModel):
    goal_text: str


class Goal(BaseModel):
    goal_id: str
    user_id: str
    goal_text: str
    status: str


class SkillGapRequest(BaseModel):
    user_skills: List[str]
    job_skills: List[str]


class SkillGapResult(BaseModel):
    matched: List[str]
    gap: List[str]


class JobFitRequest(BaseModel):
    profile: Profile
    job_description: str


class JobFitResult(BaseModel):
    fit_score: int
    rationale: str

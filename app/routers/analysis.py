from fastapi import APIRouter, HTTPException
from app.models.schemas import SkillGapRequest, SkillGapResult, JobFitRequest, JobFitResult
from app.llm.chains import get_skill_gap_chain, get_job_fit_chain
import json


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/skill-gap", response_model=SkillGapResult)
async def skill_gap(req: SkillGapRequest):
    """
    Perform semantic skill gap analysis between user skills and job requirements.
    Uses LLM for semantic matching (not just exact keyword matching).
    """
    chain = get_skill_gap_chain()
    
    try:
        result = await chain.ainvoke({
            "user_skills": json.dumps(req.user_skills),
            "job_skills": json.dumps(req.job_skills)
        })
        
        # Handle response format
        if isinstance(result, dict):
            matched = result.get("matched", [])
            gap = result.get("gap", [])
        else:
            # Fallback to basic matching if LLM fails
            user_set = set(s.lower() for s in req.user_skills)
            job_set = set(s.lower() for s in req.job_skills)
            matched = sorted(list(user_set & job_set))
            gap = sorted(list(job_set - user_set))
        
        return SkillGapResult(matched=matched or [], gap=gap or [])
    except Exception as e:
        # Fallback to basic string matching on error
        user_set = set(s.lower() for s in req.user_skills)
        job_set = set(s.lower() for s in req.job_skills)
        matched = sorted(list(user_set & job_set))
        gap = sorted(list(job_set - user_set))
        return SkillGapResult(matched=matched, gap=gap)


@router.post("/job-fit", response_model=JobFitResult)
async def job_fit(req: JobFitRequest):
    """
    Analyze job fit score (0-100) with rationale.
    Compares user profile against job description using LLM.
    """
    chain = get_job_fit_chain()
    
    try:
        profile_json = json.dumps({
            "name": req.profile.name or "",
            "email": req.profile.email or "",
            "experience": req.profile.experience_summary or "",
            "skills": req.profile.skills or []
        })
        
        result = await chain.ainvoke({
            "profile": profile_json,
            "job_description": req.job_description
        })
        
        # Handle response format
        if isinstance(result, dict):
            fit_score = result.get("fit_score", 0)
            rationale = result.get("rationale", "Analysis completed.")
        else:
            fit_score = 0
            rationale = "Error parsing LLM response."
        
        # Ensure fit_score is between 0-100
        fit_score = max(0, min(100, int(fit_score)))
        
        return JobFitResult(fit_score=fit_score, rationale=rationale)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing job fit: {str(e)}"
        )



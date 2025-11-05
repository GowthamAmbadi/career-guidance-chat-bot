from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["root"])


@router.get("/")
def index():
    return {"service": "Career Guidance API", "status": "running", "docs": "/docs"}



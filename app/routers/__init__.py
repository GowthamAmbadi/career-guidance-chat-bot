from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .root import router as root_router
from .profiles import router as profiles_router
from .goals import router as goals_router
from .resume import router as resume_router
from .analysis import router as analysis_router
from .rag import router as rag_router
from .reco import router as reco_router
from .chat import router as chat_router


def register_routers(app: FastAPI) -> None:
    app.include_router(root_router)
    app.include_router(profiles_router)
    app.include_router(goals_router)
    app.include_router(resume_router)
    app.include_router(analysis_router)
    app.include_router(rag_router)
    app.include_router(reco_router)
    app.include_router(chat_router)



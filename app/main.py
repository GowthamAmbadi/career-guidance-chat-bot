from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import register_routers
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Career Guidance API", version="0.1.0")

    # Configure CORS origins
    # Default: Skill Capital frontend + localhost for development
    default_origins = [
        "https://dev.my.skillcapital.ai",
        "https://my.skillcapital.ai",  # Production URL if different
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # Parse CORS_ORIGINS from environment (comma-separated string)
    if settings.cors_origins:
        if settings.cors_origins == "*":
            cors_origins = ["*"]
        else:
            # Split comma-separated origins and add defaults
            env_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
            cors_origins = list(set(default_origins + env_origins))  # Remove duplicates
    else:
        cors_origins = default_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root endpoint - API information
    @app.get("/", include_in_schema=False)
    def read_root():
        return {
            "service": "Career Guidance API",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
            "health": "/health"
        }
    
    register_routers(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()



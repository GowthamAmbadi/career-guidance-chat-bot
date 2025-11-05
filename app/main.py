from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import register_routers
import os


def create_app() -> FastAPI:
    app = FastAPI(title="Career Guidance API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve static files (frontend) - MUST be before routers to avoid conflicts
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # Serve chat UI at root
        @app.get("/", include_in_schema=False)
        def read_root():
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"service": "Career Guidance API", "chat_ui": "Visit /docs for API documentation"}
    
    register_routers(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()



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
    # Try multiple paths for different deployment environments (local vs Vercel serverless)
    # In Vercel, files are in /var/task/ or similar, so we need to check multiple locations
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_static_dirs = [
        os.path.join(base_dir, "static"),  # Relative to app/ directory
        os.path.join(os.getcwd(), "static"),  # Current working directory
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),  # Alternative relative path
        "static",  # Simple relative path
        os.path.abspath("static"),  # Absolute from cwd
        "/var/task/static",  # Vercel serverless path
        "/var/task/api/static",  # Alternative Vercel path
    ]
    
    static_dir = None
    for dir_path in possible_static_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            static_dir = dir_path
            print(f"✅ Found static directory at: {static_dir}")
            break
    
    if static_dir:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # Serve chat UI at root
        @app.get("/", include_in_schema=False)
        def read_root():
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                print(f"⚠️ index.html not found at: {index_path}")
                print(f"   Current working directory: {os.getcwd()}")
                print(f"   Base directory: {base_dir}")
                return {"service": "Career Guidance API", "chat_ui": "Visit /docs for API documentation", "note": f"index.html not found at {index_path}"}
    else:
        # Fallback if static directory not found
        print(f"⚠️ Static directory not found. Checked paths: {possible_static_dirs}")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Base directory: {base_dir}")
        @app.get("/", include_in_schema=False)
        def read_root():
            return {"service": "Career Guidance API", "chat_ui": "Visit /docs for API documentation", "note": "Static files not found"}
    
    register_routers(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()



"""
Vercel serverless function entry point for FastAPI app.
This file is required by Vercel to locate the serverless function.
"""
from app.main import app
from mangum import Mangum

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app, lifespan="off")

# Export for Vercel
__all__ = ["handler", "app"]


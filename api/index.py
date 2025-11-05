"""
Vercel serverless function entry point for FastAPI app.
This file is required by Vercel to locate the serverless function.
"""
from app.main import app

# Export the app for Vercel
__all__ = ["app"]


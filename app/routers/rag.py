from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_service import query_career_knowledge


router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQuery(BaseModel):
    query: str


@router.post("/query")
async def rag_query(req: RAGQuery):
    """
    RAG query endpoint: Retrieves relevant career knowledge and generates grounded answer.
    
    Flow:
    1. Convert query to embedding
    2. Search career_data vector table in Supabase
    3. Retrieve top relevant documents
    4. Generate answer using LLM with retrieved context
    """
    if not req.query or len(req.query.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Query must be at least 3 characters long"
        )
    
    try:
        result = await query_career_knowledge(req.query, top_k=5)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing RAG query: {str(e)}"
        )



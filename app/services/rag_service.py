"""
RAG (Retrieval-Augmented Generation) service for career knowledge base.
"""
from typing import List, Dict, Any
from app.llm.embeddings import embed_texts
from app.clients.supabase_client import get_supabase_client
from app.llm.gemini_client import get_gemini_llm, create_career_coach_prompt
from langchain.prompts import ChatPromptTemplate


def search_career_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search career_data table using vector similarity (pgvector).
    Returns top_k most relevant documents.
    """
    sb = get_supabase_client()
    
    # Generate embedding for query
    query_embedding = embed_texts([query])[0]
    
    # Use Supabase RPC for vector search (if available)
    try:
        # First, try using the RPC function if it exists
        try:
            result = sb.rpc('match_career_data', {
                'query_embedding': str(query_embedding),  # Supabase might need string representation
                'match_threshold': 0.3,
                'match_count': top_k
            }).execute()
            
            if result.data:
                documents = [
                    {
                        "doc_id": row.get("doc_id"),
                        "career_title": row.get("career_title"),
                        "content_chunk": row.get("content_chunk"),
                        "similarity": row.get("similarity", 0.0)
                    }
                    for row in result.data
                ]
                return documents
        except Exception as rpc_error:
            # RPC function might not exist or have issues, fall back to Python-based search
            print(f"RPC search failed, using Python fallback: {rpc_error}")
        
        # Fallback: fetch all and do similarity in Python
        result = sb.table("career_data").select("doc_id, career_title, content_chunk, embedding").limit(100).execute()
        
        if not result.data:
            return []
        
        # Calculate similarity scores (cosine similarity with normalized embeddings)
        import numpy as np
        documents = []
        for row in result.data:
            embedding_raw = row.get("embedding")
            if embedding_raw:
                # Handle different embedding formats
                if isinstance(embedding_raw, str):
                    # Supabase returns embedding as string representation of list
                    try:
                        import ast
                        doc_embedding = ast.literal_eval(embedding_raw)
                        # Ensure it's a list
                        if not isinstance(doc_embedding, list):
                            doc_embedding = None
                    except Exception as e:
                        print(f"Error parsing embedding string: {e}")
                        doc_embedding = None
                elif isinstance(embedding_raw, list):
                    doc_embedding = embedding_raw
                else:
                    doc_embedding = None
                
                if doc_embedding and len(doc_embedding) == len(query_embedding):
                    # Convert to numpy array for dot product
                    doc_embedding = np.array(doc_embedding)
                    query_embedding_arr = np.array(query_embedding)
                    similarity = np.dot(query_embedding_arr, doc_embedding)
                    if similarity > 0.3:  # Threshold for relevance
                        documents.append({
                            "doc_id": row.get("doc_id"),
                            "career_title": row.get("career_title"),
                            "content_chunk": row.get("content_chunk"),
                            "similarity": float(similarity)
                        })
        
        # Sort by similarity and return top_k
        documents.sort(key=lambda x: x["similarity"], reverse=True)
        return documents[:top_k]
        
    except Exception as e:
        # Fallback: return empty list
        import traceback
        print(f"Error searching career knowledge: {e}")
        print(traceback.format_exc())
        return []


async def query_career_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    RAG flow: Retrieve relevant documents and generate answer.
    Returns answer and sources.
    """
    # 1. Retrieve relevant documents
    # Try multiple query variations to improve search (e.g., "Software Engineering" vs "Software Engineer")
    query_variations = [
        query,  # Original query
        query.replace("Engineering", "Engineer"),  # "Software Engineering" -> "Software Engineer"
        query.replace("Engineer", "Engineering"),  # "Software Engineer" -> "Software Engineering"
        query.replace("career", "").strip(),  # Remove generic words
    ]
    
    # Search with all variations and combine results
    all_docs = []
    seen_titles = set()
    for q in query_variations:
        if q and len(q.strip()) > 0:
            docs_found = search_career_knowledge(q, top_k)
            for doc in docs_found:
                title = doc.get("career_title", "")
                if title and title not in seen_titles:
                    all_docs.append(doc)
                    seen_titles.add(title)
    
    # Sort by similarity and take top_k
    all_docs.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
    docs = all_docs[:top_k] if all_docs else []
    
    if not docs:
        return {
            "answer": "I don't have enough information in my knowledge base to answer this question. Please provide more context or check back later.",
            "sources": []
        }
    
    # 2. Build context from retrieved documents
    context_parts = []
    for doc in docs:
        title = doc.get("career_title", "Unknown")
        content = doc.get("content_chunk", "")
        context_parts.append(f"Career: {title}\n{content}\n")
    
    context = "\n---\n".join(context_parts)
    
    # 3. Generate answer using LLM with context
    llm = get_gemini_llm(temperature=0.3)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are 'Career Guidance', an expert AI Career Guidance Coach for the Indian job market. 
Your tone is professional, encouraging, supportive, and data-driven. 
You are a partner in the user's career journey. 

CRITICAL CONTEXT REQUIREMENTS:
- ALL information provided MUST be specific to INDIA and the Indian job market
- ALL salary information MUST be in Indian Rupees (INR) format: ₹X LPA - ₹Y LPA (e.g., ₹8 LPA - ₹15 LPA)
- Use REALISTIC Indian IT market salary ranges (NOT just USD conversions). Typical ranges:
  * Software Engineer: ₹6-20 LPA (entry to senior)
  * Data Scientist: ₹8-25 LPA
  * Machine Learning Engineer: ₹10-30 LPA
  * DevOps Engineer: ₹8-22 LPA
  * Product Manager: ₹12-35 LPA
  * Backend Developer: ₹6-18 LPA
  * Frontend Developer: ₹5-16 LPA
  * Full Stack Developer: ₹7-20 LPA
- Use whole numbers only (no decimals like ₹124.5 LPA - use ₹12-25 LPA instead)
- Job outlook, market trends, and career information should reflect the Indian job market
- Skills, qualifications, and requirements should be relevant to Indian companies
- If the context doesn't contain India-specific information, adapt it to the Indian context

Context from knowledge base:
{context}

INSTRUCTIONS:
1. If the context contains information about the career the user asked about (or closely related careers), use that information and adapt it to the Indian context.
2. If the context mentions related careers (e.g., "Software Engineer" when asked about "Software Engineering"), use that information - they are essentially the same.
3. If the context contains partial information, use it and provide a helpful answer based on what's available.
4. Only say "I don't have enough information" if the context is completely unrelated to the user's question.
5. ALWAYS adapt any salary information to REALISTIC Indian market ranges in INR format (₹X LPA - ₹Y LPA) with whole numbers only.
6. ALWAYS make all information India-specific.

CRITICAL FORMATTING RULES:
- Use MARKDOWN format ONLY (no HTML tags whatsoever)
- Use **bold** for emphasis, *italics* for subtle emphasis
- Use blank lines for paragraph breaks (NOT <br>)
- Use ### for headings if needed
- Use - or • for lists
- NEVER use HTML tags like <br>, <small>, <b>, <i>, <style>, or any inline CSS
- NEVER include sources, citations, or references in your answer
- Just provide the answer in clean Markdown format
- Salary ranges MUST be in INR format: ₹X LPA - ₹Y LPA (e.g., ₹8 LPA - ₹15 LPA)"""),
        ("human", "Question: {query}")
    ])
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "context": context,
            "query": query
        })
        
        answer = response.content if hasattr(response, 'content') else str(response)
    
        
        # CRITICAL: Strip ALL HTML tags from the answer - LLM should not generate HTML!
        # The frontend will handle formatting, so we return plain text only
        import re
        import html
        
        # Log original answer for debugging
        original_answer = answer
        original_has_html = '<' in answer and '>' in answer
        
        if original_has_html:
            print(f"⚠️ RAG Service: Found HTML in answer, cleaning...")
            print(f"   Original: {answer[:150]}...")
            print(f"   Original length: {len(answer)}")
        
        # AGGRESSIVE HTML STRIPPING - Multiple passes to ensure nothing escapes
        
        # Pass 1: Remove sources-related HTML (exact patterns)
        answer = re.sub(r'<br><br><small[^>]*>.*?[Ss]ources?.*?</small>', '', answer, flags=re.DOTALL | re.IGNORECASE)
        answer = re.sub(r'<br><br>\s*<small[^>]*>.*?[Ss]ources?.*?</small>', '', answer, flags=re.DOTALL | re.IGNORECASE)
        answer = re.sub(r'<small[^>]*>.*?[Ss]ources?.*?</small>', '', answer, flags=re.DOTALL | re.IGNORECASE)
        answer = re.sub(r'<[^>]+>.*?[Ss]ources?.*?</[^>]+>', '', answer, flags=re.DOTALL | re.IGNORECASE)
        
        # Pass 2: Remove standalone "📚 Sources:" text patterns
        answer = re.sub(r'📚\s*Sources?[:\s]*[^<\n]*', '', answer, flags=re.IGNORECASE)
        
        # Pass 3: Convert <br> tags to newlines BEFORE removing other tags
        answer = re.sub(r'<br\s*/?>', '\n', answer, flags=re.IGNORECASE)
        
        # Pass 4: Remove ALL remaining HTML tags (aggressive - catch everything)
        # This should catch any <tag> including <style>, <div>, <small>, etc.
        answer = re.sub(r'<[^>]+>', '', answer)
        
        # Pass 5: Remove any broken tags (tags that don't close properly)
        answer = re.sub(r'<[^>]*', '', answer)
        
        # Pass 6: Decode HTML entities (e.g., &amp; -> &)
        answer = html.unescape(answer)
        
        # Pass 7: Remove any remaining HTML entities
        answer = re.sub(r'&[a-zA-Z]+;', '', answer)
        
        # Pass 8: Clean up multiple newlines
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # Pass 9: Final aggressive cleanup - remove ANY remaining HTML-like patterns
        # This is a catch-all for anything that might have escaped
        while '<' in answer and '>' in answer:
            answer = re.sub(r'<[^>]+>', '', answer)
            answer = re.sub(r'<[^>]*', '', answer)
        
        # Clean up whitespace
        answer = answer.strip()
        
        # Log results
        if original_has_html:
            if '<' not in answer and '>' not in answer:
                print(f"✅ RAG Service: Successfully removed all HTML tags")
                print(f"   Cleaned length: {len(answer)}")
                print(f"   Cleaned: {answer[:100]}...")
            else:
                print(f"❌ RAG Service: WARNING - HTML tags still present after cleaning!")
                print(f"   Remaining: {answer}")
                # Last resort: split by < and take only text parts
                parts = answer.split('<')
                answer = parts[0] if parts else ''
                for part in parts[1:]:
                    if '>' in part:
                        text_after = part.split('>', 1)[1] if '>' in part else ''
                        if text_after:
                            answer += text_after
                answer = answer.strip()
                print(f"   After last resort cleanup: {answer[:100]}...")
        
        # Extract sources
        sources = [
            {
                "doc_id": doc.get("doc_id"),
                "career_title": doc.get("career_title"),
                "similarity": doc.get("similarity", 0.0)
            }
            for doc in docs
        ]
        
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": []
        }


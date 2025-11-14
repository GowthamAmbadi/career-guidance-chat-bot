import os
import base64
import tempfile
import time
import random
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas import ResumeParsed
from app.services.resume_parser import parse_resume_text, parse_resume_file
from app.clients.supabase_client import get_supabase_client
from app.services.vector_matcher import generate_profile_embedding, generate_skill_embeddings
from app.utils.profile_utils import format_skill_embeddings_for_postgres


router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeParsed)
async def parse_resume(
    resume_text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    user_id: Optional[str] = Form(default=None),
):
    """
    Parse resume from text or uploaded file.
    Supports: .txt, .pdf, .docx files
    Returns structured data: name, email, experience, skills.
    """
    print(f"\n{'='*60}")
    print(f"📄 RESUME PARSE REQUEST")
    print(f"{'='*60}")
    print(f"   user_id received: {user_id}")
    print(f"   file: {file.filename if file else None}")
    print(f"   resume_text length: {len(resume_text) if resume_text else 0}")
    print(f"{'='*60}\n")
    
    text_content = None
    
    if file and file.filename:
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Read uploaded file
        contents = await file.read()
        
        # Handle PDF and DOCX files
        if file_ext in ['.pdf', '.docx']:
            try:
                # Save to temporary file for pyresparser
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    temp_file.write(contents)
                    temp_path = temp_file.name
                
                try:
                    # Parse PDF/DOCX file
                    parsed = await parse_resume_file(temp_path)
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    
                    # CRITICAL: Generate user_id from email to ensure consistency
                    # This overrides any user_id sent from frontend to prevent mismatches
                    parsed_email = parsed.get("email", "")
                    if parsed_email and parsed_email != "unknown@example.com":
                        # Generate user_id from email (same logic as frontend)
                        email_encoded = base64.b64encode(parsed_email.encode()).decode()
                        email_based_user_id = 'user_' + ''.join(c for c in email_encoded if c.isalnum())[:20]
                        old_user_id = user_id
                        user_id = email_based_user_id
                        print(f"🔄 Generated user_id from email: {user_id} for email: {parsed_email}")
                        if old_user_id and old_user_id != user_id:
                            print(f"   ⚠️ Overriding frontend user_id: {old_user_id} -> {user_id}")
                    elif not user_id:
                        # Fallback: generate temporary user_id if no email and no user_id provided
                        user_id = f'user_{int(time.time())}_{random.randint(1000, 9999)}'
                        print(f"⚠️ No email found, using temporary user_id: {user_id}")
                    
                    # Save to profile if user_id is available
                    if user_id:
                        try:
                            print(f"🔍 Attempting to save profile for user_id: {user_id}")
                            sb = get_supabase_client()
                            
                            # Generate profile embedding
                            profile_embedding = None
                            try:
                                profile_embedding = generate_profile_embedding(
                                    name=parsed.get("name", ""),
                                    experience=parsed.get("experience", ""),
                                    skills=parsed.get("skills", [])
                                )
                                print(f"✅ Generated profile embedding ({len(profile_embedding)} dimensions)")
                            except Exception as e:
                                print(f"⚠️ Error generating profile embedding: {e}")
                                # Continue without embedding - profile will be saved without it
                            
                            # Generate skill embeddings
                            skills_embeddings = None
                            skills_list = parsed.get("skills", [])
                            if skills_list:
                                try:
                                    skills_embeddings = generate_skill_embeddings(skills_list)
                                    # Format embeddings for PostgreSQL vector array
                                    skills_embeddings = format_skill_embeddings_for_postgres(skills_embeddings)
                                    print(f"✅ Generated {len(skills_embeddings) if skills_embeddings else 0} skill embeddings")
                                except Exception as e:
                                    print(f"⚠️ Error generating skill embeddings: {e}")
                                    # Continue without skill embeddings - profile will be saved without them
                            
                            profile_data = {
                                "user_id": user_id,
                                "name": parsed.get("name", ""),
                                "email": parsed.get("email", "unknown@example.com"),
                                "experience_summary": parsed.get("experience", ""),
                                "skills": parsed.get("skills", []),
                                "profile_embedding": profile_embedding,
                            }
                            print(f"   Profile data: {profile_data}")
                            result = sb.table("profiles").upsert(profile_data).execute()
                            print(f"✅ Profile saved successfully for user_id: {user_id}")
                            
                            # Update skills_embeddings via RPC if we have them (vector arrays need special handling)
                            if skills_embeddings:
                                try:
                                    # Pass Python list directly - Supabase converts to JSONB automatically
                                    sb.rpc('update_skills_embeddings', {
                                        'p_user_id': user_id,
                                        'p_skills_embeddings': skills_embeddings  # Pass list directly, not json.dumps()
                                    }).execute()
                                    print(f"✅ Updated skills_embeddings via RPC for user_id: {user_id}")
                                except Exception as e:
                                    print(f"⚠️ Error updating skills_embeddings via RPC: {e}")
                                    # Continue - profile is saved, just without skill embeddings
                            print(f"   Result: {result.data if result.data else 'No data returned'}")
                            # Verify it was saved
                            verify = sb.table("profiles").select("*").eq("user_id", user_id).execute()
                            print(f"   Verification query returned {len(verify.data) if verify.data else 0} row(s)")
                        except Exception as e:
                            # Log full error for debugging
                            import traceback
                            error_trace = traceback.format_exc()
                            print(f"❌ Error saving profile to database: {str(e)}")
                            print(f"   Full traceback: {error_trace}")
                            # Don't fail the request, but log the error
                    else:
                        print(f"⚠️ No user_id provided - profile will not be saved")
                    
                    return ResumeParsed(
                        name=parsed.get("name", ""),
                        email=parsed.get("email", "unknown@example.com"),
                        experience=parsed.get("experience", ""),
                        skills=parsed.get("skills", [])
                    )
                except Exception as e:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                    # Log the full error for debugging
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"Error parsing {file_ext} file: {error_trace}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error parsing {file_ext} file: {str(e)}. Please ensure the file is not corrupted."
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing {file_ext} file: {str(e)}"
                )
        
        # Handle text files (.txt)
        elif file_ext == '.txt':
            try:
                # Try UTF-8 first
                text_content = contents.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                try:
                    text_content = contents.decode('latin-1')
                except UnicodeDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not decode text file. Please ensure it's UTF-8 encoded."
                    )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: .txt, .pdf, .docx"
            )
    elif resume_text:
        text_content = resume_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'resume_text' or 'file' must be provided"
        )
    
    if not text_content or len(text_content.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Resume text is too short or empty (minimum 10 characters)"
        )
    
    # Parse resume text
    try:
        parsed = await parse_resume_text(text_content)
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error parsing resume text: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing resume: {str(e)}"
        )
    
    # CRITICAL: Generate user_id from email to ensure consistency
    # This overrides any user_id sent from frontend to prevent mismatches
    parsed_email = parsed.get("email", "")
    if parsed_email and parsed_email != "unknown@example.com":
        # Generate user_id from email (same logic as frontend)
        email_encoded = base64.b64encode(parsed_email.encode()).decode()
        email_based_user_id = 'user_' + ''.join(c for c in email_encoded if c.isalnum())[:20]
        old_user_id = user_id
        user_id = email_based_user_id
        print(f"🔄 Generated user_id from email: {user_id} for email: {parsed_email}")
        if old_user_id and old_user_id != user_id:
            print(f"   ⚠️ Overriding frontend user_id: {old_user_id} -> {user_id}")
    elif not user_id:
        # Fallback: generate temporary user_id if no email and no user_id provided
        user_id = f'user_{int(time.time())}_{random.randint(1000, 9999)}'
        print(f"⚠️ No email found, using temporary user_id: {user_id}")
    
    # Save to profile if user_id is available
    if user_id:
        try:
            print(f"🔍 Attempting to save profile for user_id: {user_id}")
            sb = get_supabase_client()
            
            # Generate profile embedding
            profile_embedding = None
            try:
                profile_embedding = generate_profile_embedding(
                    name=parsed.get("name", ""),
                    experience=parsed.get("experience", ""),
                    skills=parsed.get("skills", [])
                )
                print(f"✅ Generated profile embedding ({len(profile_embedding)} dimensions)")
            except Exception as e:
                print(f"⚠️ Error generating profile embedding: {e}")
                # Continue without embedding - profile will be saved without it
            
            # Generate skill embeddings
            skills_embeddings = None
            skills_list = parsed.get("skills", [])
            if skills_list:
                try:
                                    skills_embeddings = generate_skill_embeddings(skills_list)
                                    # Format embeddings for PostgreSQL vector array
                                    skills_embeddings = format_skill_embeddings_for_postgres(skills_embeddings)
                                    print(f"✅ Generated {len(skills_embeddings) if skills_embeddings else 0} skill embeddings")
                except Exception as e:
                    print(f"⚠️ Error generating skill embeddings: {e}")
                    # Continue without skill embeddings - profile will be saved without them
            
            profile_data = {
                "user_id": user_id,
                "name": parsed.get("name", ""),
                "email": parsed.get("email", "unknown@example.com"),
                "experience_summary": parsed.get("experience", ""),
                "skills": parsed.get("skills", []),
                "profile_embedding": profile_embedding,
            }
            print(f"   Profile data: {profile_data}")
            result = sb.table("profiles").upsert(profile_data).execute()
            print(f"✅ Profile saved successfully for user_id: {user_id}")
            
            # Update skills_embeddings via RPC if we have them (vector arrays need special handling)
            if skills_embeddings:
                try:
                    # Pass Python list directly - Supabase converts to JSONB automatically
                    sb.rpc('update_skills_embeddings', {
                        'p_user_id': user_id,
                        'p_skills_embeddings': skills_embeddings  # Pass list directly, not json.dumps()
                    }).execute()
                    print(f"✅ Updated skills_embeddings via RPC for user_id: {user_id}")
                except Exception as e:
                    print(f"⚠️ Error updating skills_embeddings via RPC: {e}")
                    # Continue - profile is saved, just without skill embeddings
            print(f"   Result: {result.data if result.data else 'No data returned'}")
            # Verify it was saved
            verify = sb.table("profiles").select("*").eq("user_id", user_id).execute()
            print(f"   Verification query returned {len(verify.data) if verify.data else 0} row(s)")
        except Exception as e:
            # Log full error for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error saving profile to database: {str(e)}")
            print(f"   Full traceback: {error_trace}")
            # Don't fail the request, but log the error
    else:
        print(f"⚠️ No user_id provided - profile will not be saved")
    
    return ResumeParsed(
        name=parsed.get("name", ""),
        email=parsed.get("email", "unknown@example.com"),
        experience=parsed.get("experience", ""),
        skills=parsed.get("skills", [])
    )



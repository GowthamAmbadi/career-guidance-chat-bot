"""
Script to backfill profile embeddings for existing profiles.
Run this after running the database migration 004_add_profile_embeddings.sql
"""
import os
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.clients.supabase_client import get_supabase_client
from app.services.vector_matcher import generate_profile_embedding


def backfill_embeddings():
    """Generate embeddings for all existing profiles without embeddings."""
    sb = get_supabase_client()
    
    print("=" * 60)
    print("Backfilling Profile Embeddings")
    print("=" * 60)
    
    # Get all profiles without embeddings
    print("\n📊 Fetching profiles without embeddings...")
    profiles = sb.table("profiles").select("*").is_("profile_embedding", "null").execute()
    
    if not profiles.data:
        print("✅ No profiles found without embeddings. All profiles are up to date!")
        return
    
    print(f"Found {len(profiles.data)} profiles without embeddings")
    print("\n🔄 Generating embeddings...\n")
    
    success_count = 0
    error_count = 0
    
    for i, profile in enumerate(profiles.data, 1):
        user_id = profile.get("user_id", "Unknown")
        name = profile.get("name", "Unknown")
        
        print(f"[{i}/{len(profiles.data)}] Processing: {name} ({user_id})")
        
        try:
            # Generate embedding
            embedding = generate_profile_embedding(
                name=profile.get("name", ""),
                experience=profile.get("experience_summary", ""),
                skills=profile.get("skills", []) or []
            )
            
            # Update profile
            sb.table("profiles").update({
                "profile_embedding": embedding
            }).eq("user_id", user_id).execute()
            
            print(f"  ✅ Updated embedding for {name}")
            success_count += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  ❌ Error processing {name}: {e}")
            error_count += 1
            # Continue to next profile
            continue
    
    print("\n" + "=" * 60)
    print("✅ Backfill Complete!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total: {len(profiles.data)}")
    print("=" * 60)


if __name__ == "__main__":
    load_dotenv()
    backfill_embeddings()


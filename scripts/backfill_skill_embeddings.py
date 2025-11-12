"""
Backfill script to generate skill embeddings for existing profiles.
Run this after running the database migration 005_add_skills_embeddings.sql
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.supabase_client import get_supabase_client
from app.services.vector_matcher import generate_skill_embeddings


def backfill_skill_embeddings():
    """Generate and backfill skill embeddings for all profiles that don't have them."""
    sb = get_supabase_client()
    
    # Get all profiles that have skills but no skill embeddings
    profiles = sb.table("profiles").select("*").execute()
    
    if not profiles.data:
        print("No profiles found in database.")
        return
    
    print(f"Found {len(profiles.data)} profiles to process...")
    
    updated_count = 0
    error_count = 0
    
    for profile in profiles.data:
        user_id = profile.get("user_id")
        skills = profile.get("skills", []) or []
        existing_embeddings = profile.get("skills_embeddings")
        
        # Skip if no skills or already has embeddings
        if not skills:
            print(f"⏭️  Skipping {user_id}: No skills")
            continue
        
        if existing_embeddings:
            print(f"⏭️  Skipping {user_id}: Already has skill embeddings")
            continue
        
        try:
            # Generate skill embeddings
            print(f"🔄 Processing {user_id}: {len(skills)} skills...")
            skill_embeddings = generate_skill_embeddings(skills)
            
            if not skill_embeddings:
                print(f"⚠️  No embeddings generated for {user_id}")
                error_count += 1
                continue
            
            # Update profile with skill embeddings
            result = sb.table("profiles").update({
                "skills_embeddings": skill_embeddings
            }).eq("user_id", user_id).execute()
            
            if result.data:
                print(f"✅ Updated {user_id}: {len(skill_embeddings)} skill embeddings")
                updated_count += 1
            else:
                print(f"⚠️  Failed to update {user_id}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {user_id}: {e}")
            import traceback
            print(traceback.format_exc())
            error_count += 1
    
    print(f"\n✅ Backfill complete!")
    print(f"   Updated: {updated_count}")
    print(f"   Errors: {error_count}")
    print(f"   Skipped: {len(profiles.data) - updated_count - error_count}")


if __name__ == "__main__":
    print("🚀 Starting skill embeddings backfill...")
    print("=" * 50)
    backfill_skill_embeddings()
    print("=" * 50)
    print("✅ Done!")


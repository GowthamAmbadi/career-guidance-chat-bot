"""
Script to clear old embeddings from career_data table.
Run this before re-seeding with new OpenAI embeddings.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.clients.supabase_client import get_supabase_client

def clear_career_data():
    """Delete all rows from career_data table."""
    sb = get_supabase_client()
    
    print("Clearing old career_data embeddings...")
    
    try:
        # Delete all rows
        result = sb.table("career_data").delete().neq("doc_id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Cleared career_data table")
        print(f"   Deleted rows (if any existed)")
    except Exception as e:
        print(f"❌ Error clearing career_data: {e}")
        raise

if __name__ == "__main__":
    load_dotenv()
    clear_career_data()
    print("\n✅ Done! Ready to re-seed with new OpenAI embeddings.")


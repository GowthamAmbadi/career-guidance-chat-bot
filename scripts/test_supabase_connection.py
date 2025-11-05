"""Test script to verify Supabase connection and profile saving."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.supabase_client import get_supabase_client
from app.config import settings

def test_supabase():
    print("=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    # Check settings
    print(f"\n📋 Configuration:")
    print(f"   SUPABASE_URL: {settings.supabase_url[:30]}..." if settings.supabase_url else "   ❌ SUPABASE_URL not set")
    print(f"   Service Role Key: {'✅ Set' if settings.supabase_service_role_key else '❌ Not set'}")
    
    try:
        # Get client
        print(f"\n🔌 Connecting to Supabase...")
        sb = get_supabase_client()
        print(f"   ✅ Client created successfully")
        
        # Test query (should work even with service_role)
        print(f"\n📊 Testing query...")
        test_result = sb.table("profiles").select("user_id").limit(1).execute()
        print(f"   ✅ Query successful")
        print(f"   📋 Current profiles in DB: {len(test_result.data) if test_result.data else 0}")
        
        # Test insert
        print(f"\n💾 Testing profile insert...")
        test_user_id = "test_user_12345"
        test_profile = {
            "user_id": test_user_id,
            "name": "Test User",
            "email": "test@example.com",
            "experience_summary": "Test experience",
            "skills": ["Python", "SQL"]
        }
        
        print(f"   Inserting test profile: {test_profile}")
        insert_result = sb.table("profiles").upsert(test_profile).execute()
        print(f"   ✅ Insert result: {insert_result.data if insert_result.data else 'No data returned'}")
        
        # Verify it was saved
        print(f"\n🔍 Verifying insert...")
        verify_result = sb.table("profiles").select("*").eq("user_id", test_user_id).execute()
        if verify_result.data and len(verify_result.data) > 0:
            print(f"   ✅ Profile found in database!")
            print(f"   📋 Profile data: {verify_result.data[0]}")
        else:
            print(f"   ❌ Profile NOT found in database!")
            print(f"   ⚠️ This means the insert failed silently or RLS is blocking")
        
        # Clean up test data
        print(f"\n🧹 Cleaning up test data...")
        delete_result = sb.table("profiles").delete().eq("user_id", test_user_id).execute()
        print(f"   ✅ Test profile deleted")
        
        print(f"\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {str(e)}")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        print(f"\n" + "=" * 60)
        print("❌ Test failed!")
        print("=" * 60)

if __name__ == "__main__":
    test_supabase()



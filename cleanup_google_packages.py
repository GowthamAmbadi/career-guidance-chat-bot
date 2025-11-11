import os
import shutil
from pathlib import Path

def cleanup_google_packages():
    """Remove leftover Google API package directories."""
    site_packages = Path(".venv/Lib/site-packages")
    
    # Directories to remove
    dirs_to_remove = [
        "googleapiclient", "google", "google_auth", "google_auth_httplib2",
        "googleapis_common_protos", "google_generativeai", "google_ai_generativelanguage",
        "google_api_core", "google_api_python_client", "uritemplate"
    ]
    
    # .dist-info folders to remove
    dist_info_to_remove = [
        "google_api_python_client-2.186.0.dist-info",
        "google_auth-2.42.1.dist-info",
        "google_auth_httplib2-0.2.1.dist-info",
        "googleapis_common_protos-1.71.0.dist-info",
        "google_generativeai-0.8.5.dist-info",
        "google_ai_generativelanguage-0.6.15.dist-info",
        "google_api_core-2.28.1.dist-info",
        "uritemplate-4.2.0.dist-info"
    ]
    
    removed = []
    for dir_name in dirs_to_remove + dist_info_to_remove:
        dir_path = site_packages / dir_name
        if dir_path.exists():
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    removed.append(dir_name)
                    print(f"✅ Removed: {dir_name}")
            except Exception as e:
                print(f"⚠️ Could not remove {dir_name}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {len(removed)} directories.")
    return len(removed)

if __name__ == "__main__":
    cleanup_google_packages()


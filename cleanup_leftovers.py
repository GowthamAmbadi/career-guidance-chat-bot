import os
import shutil
from pathlib import Path

def cleanup_leftover_dirs():
    """Remove leftover package directories that pip didn't fully clean up."""
    site_packages = Path(".venv/Lib/site-packages")
    
    # Directories to remove
    dirs_to_remove = [
        "scipy", "pandas", "sympy", "sklearn", "sqlalchemy", 
        "networkx", "nltk", "spacy", "spacy_legacy", "spacy_loggers",
        "pandas.libs", "scipy.libs"
    ]
    
    # .dist-info folders to remove
    dist_info_to_remove = [
        "scipy-1.16.3.dist-info", "pandas-2.3.3.dist-info", 
        "sympy-1.14.0.dist-info", "scikit_learn-1.5.2.dist-info",
        "SQLAlchemy-2.0.35.dist-info", "networkx-3.5.dist-info",
        "nltk-3.9.1.dist-info", "spacy-3.7.5.dist-info",
        "spacy_legacy-3.0.12.dist-info", "spacy_loggers-1.0.5.dist-info",
        "pillow-12.0.0.dist-info"
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
    cleanup_leftover_dirs()


import os
from pathlib import Path

def get_dir_size(path):
    """Get total size of directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    except PermissionError:
        pass
    return total

def main():
    # Get total project size
    project_root = Path(".")
    total_size = sum(f.stat().st_size for f in project_root.rglob("*") if f.is_file())
    
    # Get .venv size
    venv_path = Path(".venv")
    venv_size = 0
    if venv_path.exists():
        venv_size = sum(f.stat().st_size for f in venv_path.rglob("*") if f.is_file())
    
    project_only_size = total_size - venv_size
    
    print(f"Total project size: {total_size / (1024 * 1024):.2f} MB")
    print(f".venv size: {venv_size / (1024 * 1024):.2f} MB")
    print(f"Project (excluding .venv): {project_only_size / (1024 * 1024):.2f} MB")
    print()
    
    # Get package sizes
    site_packages = Path(".venv/Lib/site-packages")
    if not site_packages.exists():
        print("Error: .venv/Lib/site-packages not found")
        return
    
    packages = []
    print("Scanning packages...")
    for item in site_packages.iterdir():
        if item.is_dir():
            size_mb = get_dir_size(item) / (1024 * 1024)
            packages.append((item.name, size_mb))
    
    # Sort by size descending
    packages.sort(key=lambda x: x[1], reverse=True)
    
    # Print in the exact format requested
    print(f"{'Package':<25} {'Size(MB)':>10}")
    print("-" * 37)
    
    for name, size in packages:
        print(f"{name:<25} {size:>10.2f}")

if __name__ == "__main__":
    main()


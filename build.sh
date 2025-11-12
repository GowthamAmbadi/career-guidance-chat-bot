#!/bin/bash
set -e

# Set cache directories to /tmp to reduce memory usage
export XDG_CACHE_HOME=/tmp
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export PIP_NO_BUILD_ISOLATION=1
export PIP_NO_COMPILE=1

echo "=========================================="
echo "Installing dependencies from requirements.txt"
echo "=========================================="

# Install all dependencies from requirements.txt
if [ -f requirements.txt ]; then
    echo "Installing from requirements.txt..."
    uv pip install --system --no-cache -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Clean up unnecessary files to reduce bundle size
echo "=========================================="
echo "Cleaning up unnecessary files to reduce bundle size..."
echo "=========================================="

# Remove Python cache files
echo "Removing Python cache files..."
find /usr/local/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pyo" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pyd" -delete 2>/dev/null || true

# Remove documentation files (keep METADATA and LICENSE files)
echo "Removing documentation files..."
find /usr/local/lib/python3.12/site-packages -name "*.md" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.txt" ! -name "METADATA" ! -name "LICENSE*" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.rst" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.html" -delete 2>/dev/null || true

# Remove test files and directories
echo "Removing test files..."
find /usr/local/lib/python3.12/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*_test.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "test_*.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*_tests.py" -delete 2>/dev/null || true

# Remove example files
echo "Removing example files..."
find /usr/local/lib/python3.12/site-packages -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -type d -name "example" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*example*.py" -delete 2>/dev/null || true

# Remove Jupyter notebook files
echo "Removing Jupyter notebook files..."
find /usr/local/lib/python3.12/site-packages -name "*.ipynb" -delete 2>/dev/null || true

# Remove numpy unnecessary files
echo "Removing numpy unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/numpy" ]; then
    find /usr/local/lib/python3.12/site-packages/numpy -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*test*.py" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.rst" -delete 2>/dev/null || true
fi

# Remove langchain unnecessary files
echo "Removing langchain unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/langchain" ]; then
    find /usr/local/lib/python3.12/site-packages/langchain -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*example*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*.rst" -delete 2>/dev/null || true
fi

# Remove any .git directories
echo "Removing .git directories..."
find /usr/local/lib/python3.12/site-packages -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true

# Remove unnecessary locale files (keep only en_US if needed)
echo "Removing unnecessary locale files..."
find /usr/local/lib/python3.12/site-packages -type d -name "locale" -exec find {} -mindepth 2 -maxdepth 2 ! -name "en_US" -type d -exec rm -rf {} + \; 2>/dev/null || true

# Remove ALL empty directories
echo "Removing empty directories..."
find /usr/local/lib/python3.12/site-packages -type d -empty -delete 2>/dev/null || true

echo "=========================================="
echo "Cleanup complete. Bundle size minimized."
echo "=========================================="

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="

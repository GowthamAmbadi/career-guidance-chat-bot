#!/bin/bash
set -e

# Set all cache directories to /tmp to reduce memory usage
export TRANSFORMERS_CACHE=/tmp/transformers_cache
export HF_HOME=/tmp/hf_home
export SENTENCE_TRANSFORMERS_HOME=/tmp/st_cache
export TORCH_HOME=/tmp/torch_cache
export XDG_CACHE_HOME=/tmp
export HF_DATASETS_CACHE=/tmp/hf_datasets_cache
export HF_METRICS_CACHE=/tmp/hf_metrics_cache
export HF_MODULES_CACHE=/tmp/hf_modules_cache
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export PIP_NO_BUILD_ISOLATION=1
export PIP_NO_COMPILE=1

echo "=========================================="
echo "Installing dependencies with uv (optimized)"
echo "=========================================="

# Install all dependencies from requirements.txt first (lightweight packages)
if [ -f requirements.txt ]; then
    echo "Installing from requirements.txt..."
    uv pip install --system --no-cache -r requirements.txt
fi

echo ""
echo "=========================================="
echo "Installing ML dependencies (memory intensive)"
echo "=========================================="
# Install numpy and scikit-learn first (dependencies for sentence-transformers)
uv pip install --system --no-cache \
    --only-binary :all: \
    numpy==1.26.4 \
    scikit-learn==1.5.2 || \
uv pip install --system --no-cache \
    numpy==1.26.4 \
    scikit-learn==1.5.2

# Install CPU-only PyTorch (much smaller ~200MB vs ~1.5GB for full PyTorch)
# Only install torch core, skip torchvision and torchaudio to save space
echo "Installing CPU-only PyTorch (minimal installation for size optimization)..."
uv pip install --system --no-cache \
    torch==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu || \
uv pip install --system --no-cache \
    torch==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers last (most memory intensive) - only binary wheels
echo "Installing sentence-transformers (binary only)..."
uv pip install --system --no-cache \
    --only-binary :all: \
    sentence-transformers==3.0.1 || \
uv pip install --system --no-cache \
    sentence-transformers==3.0.1

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

# Aggressive PyTorch cleanup
echo "Removing unnecessary PyTorch files..."
if [ -d "/usr/local/lib/python3.12/site-packages/torch" ]; then
    # Remove CUDA files (shouldn't exist in CPU build, but just in case)
    find /usr/local/lib/python3.12/site-packages/torch -name "cu*" -type f -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*.cudnn*" -delete 2>/dev/null || true
    # Remove torchvision and torchaudio if accidentally installed
    rm -rf /usr/local/lib/python3.12/site-packages/torchvision 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/torchaudio 2>/dev/null || true
    # Remove test files
    find /usr/local/lib/python3.12/site-packages/torch -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*test*.py" -delete 2>/dev/null || true
    # Remove example files
    find /usr/local/lib/python3.12/site-packages/torch -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
fi

# Remove transformers unnecessary files
echo "Removing transformers unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/transformers" ]; then
    # Remove test files only (keep model code and tokenizers)
    find /usr/local/lib/python3.12/site-packages/transformers -name "*test*.py" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    # Remove example files
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
fi

# Remove sentence-transformers unnecessary files
echo "Removing sentence-transformers unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/sentence_transformers" ]; then
    # Remove example models and data
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*example*" -delete 2>/dev/null || true
fi

# Remove scikit-learn unnecessary files
echo "Removing scikit-learn unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/sklearn" ]; then
    # Remove datasets (if any)
    find /usr/local/lib/python3.12/site-packages/sklearn -type d -name "datasets" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -type d -name "data" -exec rm -rf {} + 2>/dev/null || true
fi

# Remove langchain unnecessary files
echo "Removing langchain unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/langchain" ]; then
    find /usr/local/lib/python3.12/site-packages/langchain -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*example*" -delete 2>/dev/null || true
fi

# Remove any .git directories
echo "Removing .git directories..."
find /usr/local/lib/python3.12/site-packages -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true

# Remove any large data files
echo "Removing large data files..."
find /usr/local/lib/python3.12/site-packages -name "*.pkl" -size +1M -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.h5" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.hdf5" -delete 2>/dev/null || true

# Remove unnecessary locale files (keep only en_US if needed)
echo "Removing unnecessary locale files..."
find /usr/local/lib/python3.12/site-packages -type d -name "locale" -exec find {} -mindepth 2 -maxdepth 2 ! -name "en_US" -type d -exec rm -rf {} + \; 2>/dev/null || true

# Final cleanup: remove empty directories
echo "Removing empty directories..."
find /usr/local/lib/python3.12/site-packages -type d -empty -delete 2>/dev/null || true

echo "=========================================="
echo "Cleanup complete. Bundle size optimized."
echo "=========================================="

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="


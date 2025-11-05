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
echo "Installing CPU-only PyTorch (optimized for size)..."
uv pip install --system --no-cache \
    torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu \
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
echo "Cleaning up unnecessary files to reduce bundle size..."
# Remove Python cache files
find /usr/local/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pyo" -delete 2>/dev/null || true

# Remove documentation files (keep METADATA files)
find /usr/local/lib/python3.12/site-packages -name "*.md" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.txt" ! -name "METADATA" -delete 2>/dev/null || true

# Remove test files
find /usr/local/lib/python3.12/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*_test.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "test_*.py" -delete 2>/dev/null || true

# Remove unnecessary PyTorch CUDA files (if any)
find /usr/local/lib/python3.12/site-packages/torch -name "cu*" -type f -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages/torch -name "*.cudnn*" -delete 2>/dev/null || true

echo "Cleanup complete. Bundle size optimized."

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="


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

# Install sentence-transformers last (most memory intensive) - only binary wheels
echo "Installing sentence-transformers (binary only)..."
uv pip install --system --no-cache \
    --only-binary :all: \
    sentence-transformers==3.0.1 || \
uv pip install --system --no-cache \
    sentence-transformers==3.0.1

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="


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

# Install CPU-only PyTorch (use older, smaller version for size optimization)
# Version 2.0.1 is smaller than 2.1.0
echo "Installing CPU-only PyTorch (minimal version 2.0.1 for size optimization)..."
uv pip install --system --no-cache \
    torch==2.0.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu || \
uv pip install --system --no-cache \
    torch==2.0.1+cpu \
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

# Aggressive PyTorch cleanup - remove as much as possible
echo "Removing unnecessary PyTorch files (aggressive cleanup)..."
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
    # Remove unnecessary torch modules to save space
    # Keep essential modules: nn, optim, functional, tensor operations, autograd, multiprocessing
    # Remove only clearly unnecessary: distributed, jit, quantization, onnx, profiler, cuda
    for module in distributed jit quantization onnx profiler cuda; do
        find /usr/local/lib/python3.12/site-packages/torch -type d -name "$module" -exec rm -rf {} + 2>/dev/null || true
    done
    # Remove large binary files that aren't essential
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "*.a" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcudart*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcublas*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcurand*" -delete 2>/dev/null || true
fi

# Remove transformers unnecessary files (aggressive cleanup)
echo "Removing transformers unnecessary files (aggressive cleanup)..."
if [ -d "/usr/local/lib/python3.12/site-packages/transformers" ]; then
    # Remove test files
    find /usr/local/lib/python3.12/site-packages/transformers -name "*test*.py" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    # Remove example files
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    # Remove benchmarking and optimization tools
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "benchmark" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -name "*benchmark*" -delete 2>/dev/null || true
    # Remove ONNX and other export tools
    find /usr/local/lib/python3.12/site-packages/transformers -type d -name "onnx" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -name "*onnx*" -delete 2>/dev/null || true
    # Remove model cards and documentation
    find /usr/local/lib/python3.12/site-packages/transformers -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -name "*.rst" -delete 2>/dev/null || true
fi

# Remove sentence-transformers unnecessary files
echo "Removing sentence-transformers unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/sentence_transformers" ]; then
    # Remove example models and data
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*example*" -delete 2>/dev/null || true
fi

# Remove scikit-learn unnecessary files (aggressive cleanup)
echo "Removing scikit-learn unnecessary files (aggressive cleanup)..."
if [ -d "/usr/local/lib/python3.12/site-packages/sklearn" ]; then
    # Remove datasets (if any)
    find /usr/local/lib/python3.12/site-packages/sklearn -type d -name "datasets" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -type d -name "data" -exec rm -rf {} + 2>/dev/null || true
    # Remove example data files
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.csv" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.arff" -delete 2>/dev/null || true
    # Remove documentation
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.rst" -delete 2>/dev/null || true
fi

# Remove numpy unnecessary files
echo "Removing numpy unnecessary files..."
if [ -d "/usr/local/lib/python3.12/site-packages/numpy" ]; then
    # Remove test files
    find /usr/local/lib/python3.12/site-packages/numpy -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*test*.py" -delete 2>/dev/null || true
    # Remove f2py (Fortran compiler interface, not needed)
    find /usr/local/lib/python3.12/site-packages/numpy -type d -name "f2py" -exec rm -rf {} + 2>/dev/null || true
    # Remove documentation
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.rst" -delete 2>/dev/null || true
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

# Remove any large data files (more aggressive)
echo "Removing large data files (aggressive cleanup)..."
# Remove large pickle files (keep small ones that might be needed for library functionality)
find /usr/local/lib/python3.12/site-packages -name "*.pkl" -size +500k -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.h5" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.hdf5" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.npz" -size +100k -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.npy" -size +100k -delete 2>/dev/null || true
# Remove model weights that might be bundled (models download on demand)
find /usr/local/lib/python3.12/site-packages -name "*.bin" -size +1M -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.safetensors" -size +1M -delete 2>/dev/null || true

# Remove unnecessary locale files (keep only en_US if needed)
echo "Removing unnecessary locale files..."
find /usr/local/lib/python3.12/site-packages -type d -name "locale" -exec find {} -mindepth 2 -maxdepth 2 ! -name "en_US" -type d -exec rm -rf {} + \; 2>/dev/null || true

# EXTREME CLEANUP: Remove ALL non-essential files from ALL packages
echo "=========================================="
echo "EXTREME CLEANUP: Removing ALL non-essential files..."
echo "=========================================="

# Remove ALL documentation, examples, tests from EVERY package
echo "Removing ALL documentation, examples, tests..."
find /usr/local/lib/python3.12/site-packages -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" ! -name "METADATA" ! -name "LICENSE*" -o -name "*.html" -o -name "*.json" ! -name "*.dist-info/METADATA" \) -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -type d \( -name "tests" -o -name "test" -o -name "examples" -o -name "example" -o -name "docs" -o -name "doc" -o -name "benchmarks" -o -name "benchmark" \) -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*test*.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*example*.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*benchmark*.py" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.ipynb" -delete 2>/dev/null || true

# Remove ALL data files, models, and large binaries
echo "Removing ALL data files and large binaries..."
find /usr/local/lib/python3.12/site-packages -name "*.pkl" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.h5" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.hdf5" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.npz" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.npy" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.bin" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.safetensors" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.onnx" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.tflite" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.pb" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.csv" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.tsv" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.json" ! -path "*/dist-info/*" -delete 2>/dev/null || true

# Remove ALL static libraries and unnecessary binaries
echo "Removing ALL static libraries and unnecessary binaries..."
find /usr/local/lib/python3.12/site-packages -name "*.a" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.lib" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.so.*" ! -name "*.so" -delete 2>/dev/null || true

# Aggressive PyTorch stripping - remove everything except core functionality
echo "EXTREME PyTorch cleanup - keeping only absolute essentials..."
if [ -d "/usr/local/lib/python3.12/site-packages/torch" ]; then
    # Remove ONLY clearly unnecessary directories (keep core C extensions)
    for dir in distributed jit quantization onnx profiler cuda amp hub; do
        rm -rf /usr/local/lib/python3.12/site-packages/torch/$dir 2>/dev/null || true
    done
    # Remove ALL test and example files
    find /usr/local/lib/python3.12/site-packages/torch -type d \( -name "test" -o -name "tests" -o -name "examples" -o -name "example" \) -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*test*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*example*" -delete 2>/dev/null || true
    # Remove ALL documentation
    find /usr/local/lib/python3.12/site-packages/torch -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*.rst" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch -name "*.txt" ! -name "METADATA" -delete 2>/dev/null || true
    # Remove ALL static libraries
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "*.a" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcuda*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcudnn*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcurand*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcublas*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcusparse*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libcusolver*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libnvrtc*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/torch/lib -name "libnvToolsExt*" -delete 2>/dev/null || true
fi

# Aggressive transformers stripping
echo "EXTREME transformers cleanup..."
if [ -d "/usr/local/lib/python3.12/site-packages/transformers" ]; then
    # Remove ALL unnecessary subdirectories
    for dir in benchmarks examples tests test utils; do
        rm -rf /usr/local/lib/python3.12/site-packages/transformers/$dir 2>/dev/null || true
    done
    # Remove ALL model-specific directories we don't use (keep only tokenizers and basic models)
    # This is risky but necessary - we'll keep only what sentence-transformers needs
    find /usr/local/lib/python3.12/site-packages/transformers/models -type d -mindepth 1 -maxdepth 1 ! -name "auto" ! -name "bert" ! -name "roberta" ! -name "distilbert" ! -name "sentence_transformers" -exec rm -rf {} + 2>/dev/null || true
    # Remove ALL documentation
    find /usr/local/lib/python3.12/site-packages/transformers -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -name "*.rst" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/transformers -name "*.txt" ! -name "METADATA" -delete 2>/dev/null || true
fi

# Aggressive sentence-transformers stripping
echo "EXTREME sentence-transformers cleanup..."
if [ -d "/usr/local/lib/python3.12/site-packages/sentence_transformers" ]; then
    # Remove ALL examples and tests
    rm -rf /usr/local/lib/python3.12/site-packages/sentence_transformers/examples 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/sentence_transformers/tests 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*test*" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*example*" -delete 2>/dev/null || true
    # Remove ALL documentation
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sentence_transformers -name "*.rst" -delete 2>/dev/null || true
fi

# Aggressive scikit-learn stripping
echo "EXTREME scikit-learn cleanup..."
if [ -d "/usr/local/lib/python3.12/site-packages/sklearn" ]; then
    # Remove ALL datasets and examples
    rm -rf /usr/local/lib/python3.12/site-packages/sklearn/datasets 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/sklearn/examples 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/sklearn/tests 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.rst" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.csv" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/sklearn -name "*.arff" -delete 2>/dev/null || true
fi

# Aggressive numpy stripping
echo "EXTREME numpy cleanup..."
if [ -d "/usr/local/lib/python3.12/site-packages/numpy" ]; then
    rm -rf /usr/local/lib/python3.12/site-packages/numpy/tests 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/numpy/f2py 2>/dev/null || true
    rm -rf /usr/local/lib/python3.12/site-packages/numpy/doc 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/numpy -name "*.rst" -delete 2>/dev/null || true
fi

# Aggressive langchain stripping
echo "EXTREME langchain cleanup..."
if [ -d "/usr/local/lib/python3.12/site-packages/langchain" ]; then
    find /usr/local/lib/python3.12/site-packages/langchain -type d \( -name "examples" -o -name "tests" -o -name "test" \) -exec rm -rf {} + 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*.md" -delete 2>/dev/null || true
    find /usr/local/lib/python3.12/site-packages/langchain -name "*.rst" -delete 2>/dev/null || true
fi

# Remove ALL locale files except en_US
echo "Removing ALL non-English locales..."
find /usr/local/lib/python3.12/site-packages -type d -name "locale" -exec find {} -mindepth 2 -maxdepth 2 ! -name "en_US" -type d -exec rm -rf {} + \; 2>/dev/null || true

# Remove ALL .git directories
echo "Removing ALL .git directories..."
find /usr/local/lib/python3.12/site-packages -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -type d -name ".github" -exec rm -rf {} + 2>/dev/null || true

# Remove ALL empty directories
echo "Removing ALL empty directories..."
find /usr/local/lib/python3.12/site-packages -type d -empty -delete 2>/dev/null || true

# Final pass: Remove any remaining large files
echo "Final pass: Removing any remaining large files..."
find /usr/local/lib/python3.12/site-packages -type f -size +500k ! -name "*.so" -delete 2>/dev/null || true

echo "=========================================="
echo "EXTREME cleanup complete. Bundle size minimized."
echo "=========================================="

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="


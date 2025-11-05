#!/bin/bash
# Script to optimize bundle size by removing unnecessary files after build

echo "Optimizing bundle size..."

# Remove unnecessary PyTorch files (CPU-only needed)
find /usr/local/lib/python3.12/site-packages/torch -name "*.so" ! -path "*/lib/*" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages/torch -name "cu*" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages/torch -name "*.cudnn*" -delete 2>/dev/null || true

# Remove test files
find /usr/local/lib/python3.12/site-packages -name "*test*" -type f -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*__pycache__*" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove documentation
find /usr/local/lib/python3.12/site-packages -name "*.md" -delete 2>/dev/null || true
find /usr/local/lib/python3.12/site-packages -name "*.txt" ! -name "METADATA" -delete 2>/dev/null || true

# Remove unnecessary transformers models (only keep what's needed)
# Models will be downloaded at runtime
find /usr/local/lib/python3.12/site-packages/transformers/models -mindepth 2 -maxdepth 2 -type d ! -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Bundle optimization complete"


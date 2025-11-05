#!/bin/bash
set -e

echo "=========================================="
echo "Stage 1: Upgrading pip"
echo "=========================================="
pip install --upgrade pip --no-cache-dir

echo ""
echo "=========================================="
echo "Stage 2: Installing core dependencies (lightweight)"
echo "=========================================="
pip install --no-cache-dir --no-warn-script-location \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.6 \
    python-dotenv==1.0.1 \
    pydantic==2.9.2 \
    pydantic-settings==2.5.2 \
    httpx==0.27.2 \
    python-multipart==0.0.20 \
    email-validator==2.3.0

echo ""
echo "=========================================="
echo "Stage 3: Installing database dependencies"
echo "=========================================="
pip install --no-cache-dir --no-warn-script-location \
    supabase==2.6.0 \
    psycopg[binary]==3.2.1 \
    pgvector==0.3.3 \
    SQLAlchemy==2.0.35

echo ""
echo "=========================================="
echo "Stage 4: Installing LangChain dependencies"
echo "=========================================="
pip install --no-cache-dir --no-warn-script-location \
    langchain==0.3.7 \
    langchain-community==0.3.7 \
    langchain-google-genai==2.0.1

echo ""
echo "=========================================="
echo "Stage 5: Installing resume parsing dependencies"
echo "=========================================="
pip install --no-cache-dir --no-warn-script-location \
    pdfplumber==0.11.0 \
    PyPDF2==3.0.1 \
    python-docx==1.1.2

echo ""
echo "=========================================="
echo "Stage 6: Installing ML dependencies (memory intensive)"
echo "=========================================="
# Set cache directories to /tmp to reduce memory usage
export TRANSFORMERS_CACHE=/tmp/transformers_cache
export HF_HOME=/tmp/hf_home
export SENTENCE_TRANSFORMERS_HOME=/tmp/st_cache
export TORCH_HOME=/tmp/torch_cache
export XDG_CACHE_HOME=/tmp

# Install numpy and scikit-learn first (dependencies for sentence-transformers)
pip install --no-cache-dir --no-warn-script-location \
    numpy==1.26.4 \
    scikit-learn==1.5.2

# Install sentence-transformers last (most memory intensive)
pip install --no-cache-dir --no-warn-script-location \
    sentence-transformers==3.0.1

echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="


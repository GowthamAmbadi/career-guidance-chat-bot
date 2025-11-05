"""
Script to seed career_data table with embeddings.
Run this after setting up your Supabase tables.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.config import settings
from app.llm.embeddings import embed_texts
from app.clients.supabase_client import get_supabase_client

# Sample career data
CAREER_DATA = [
    {
        "career_title": "Data Scientist",
        "content_chunk": """Data Scientists analyze complex data sets to identify trends and patterns. 
They use machine learning, statistics, and programming (Python, R) to build predictive models. 
Day-to-day work includes: data collection, cleaning, analysis, model building, and presenting insights. 
Required skills: Python, R, SQL, Machine Learning, Statistics, Data Visualization, TensorFlow, PyTorch. 
Salary range: $95,000 - $165,000. Job outlook: Excellent with 22% growth projected through 2030."""
    },
    {
        "career_title": "Software Engineer",
        "content_chunk": """Software Engineers design, develop, and maintain software applications. 
They work with programming languages like Python, Java, JavaScript, C++, and use frameworks like React, Django, Spring. 
Day-to-day work includes: writing code, debugging, testing, code reviews, system design, and collaboration. 
Required skills: Programming languages, Data Structures, Algorithms, Version Control (Git), Software Design Patterns. 
Salary range: $85,000 - $150,000. Job outlook: Excellent with high demand across all industries."""
    },
    {
        "career_title": "Product Manager",
        "content_chunk": """Product Managers oversee product development from conception to launch. 
They work with engineering, design, and marketing teams to define product vision and strategy. 
Day-to-day work includes: requirement gathering, roadmap planning, stakeholder management, user research, and analytics. 
Required skills: Product Strategy, User Research, Analytics, Agile/Scrum, Communication, Market Analysis. 
Salary range: $100,000 - $160,000. Job outlook: Strong with growing demand for technical PMs."""
    },
    {
        "career_title": "DevOps Engineer",
        "content_chunk": """DevOps Engineers bridge development and operations teams, automating and streamlining processes. 
They manage CI/CD pipelines, infrastructure as code, monitoring, and deployment automation. 
Day-to-day work includes: setting up deployment pipelines, managing cloud infrastructure, monitoring systems, and automation. 
Required skills: Docker, Kubernetes, AWS/GCP/Azure, CI/CD, Terraform, Linux, Scripting (Bash/Python). 
Salary range: $90,000 - $155,000. Job outlook: Excellent with increasing cloud adoption."""
    },
    {
        "career_title": "Machine Learning Engineer",
        "content_chunk": """Machine Learning Engineers build and deploy ML models into production systems. 
They work on model training, optimization, deployment, and maintaining ML pipelines. 
Day-to-day work includes: model development, feature engineering, model deployment, performance monitoring, and optimization. 
Required skills: Python, TensorFlow, PyTorch, ML Algorithms, Cloud Platforms, MLOps, Data Engineering. 
Salary range: $110,000 - $175,000. Job outlook: Excellent with rapid growth in AI/ML space."""
    }
]


def seed_career_data():
    """Generate embeddings and insert career data into Supabase."""
    sb = get_supabase_client()
    
    print("Generating embeddings for career data...")
    
    # Generate embeddings for all content chunks
    content_chunks = [item["content_chunk"] for item in CAREER_DATA]
    embeddings = embed_texts(content_chunks)
    
    print(f"Generated {len(embeddings)} embeddings")
    print("Inserting career data into Supabase...")
    
    # Insert data with embeddings
    for i, item in enumerate(CAREER_DATA):
        try:
            # Check if already exists
            existing = (
                sb.table("career_data")
                .select("doc_id")
                .eq("career_title", item["career_title"])
                .execute()
            )
            
            if existing.data:
                print(f"Skipping {item['career_title']} (already exists)")
                continue
            
            # Insert new record
            result = (
                sb.table("career_data")
                .insert({
                    "career_title": item["career_title"],
                    "content_chunk": item["content_chunk"],
                    "embedding": embeddings[i]
                })
                .execute()
            )
            
            print(f"✓ Inserted: {item['career_title']}")
        except Exception as e:
            print(f"✗ Error inserting {item['career_title']}: {e}")
    
    print("\nDone! Career data seeded successfully.")


if __name__ == "__main__":
    load_dotenv()
    seed_career_data()


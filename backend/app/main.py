from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router
from backend.app.config import get_settings
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

settings = get_settings()

# Create necessary directories
os.makedirs(settings.storage_path, exist_ok=True)
os.makedirs(settings.output_path, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)


app = FastAPI(
    title="AI Documentation Generator",
    description="Automated code documentation using LangGraph and OpenAI",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "AI Documentation Generator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
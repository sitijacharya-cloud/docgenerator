from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import logging
import asyncio
import json
import os
from collections import defaultdict
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

from backend.core.langgraph_pipeline import LangGraphPipeline
from backend.core.models import ProjectMetadata, ParsedCode
from backend.storage.project_store import ProjectStore
from backend.core.code_loader import CodeLoader


# User preferences storage (in production, use database)
user_preferences_store: Dict[str, Dict] = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Code Documentation Agent API",
    description="AI-powered code documentation generator with multi-language support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

project_store = ProjectStore()
langgraph_pipeline = LangGraphPipeline()
code_loader = CodeLoader()

progress_queues: Dict[str, Queue] = defaultdict(Queue)


class ProjectResponse(BaseModel):
    """Project metadata response."""
    id: str
    name: str
    file_name: str
    file_size: int
    language: Optional[str] = None
    status: str
    uploaded_at: datetime
    progress_message: Optional[str] = None
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None
    
    class Config:
        from_attributes = True


class ProcessingStatus(BaseModel):
    """Processing status response."""
    project_id: str
    status: str
    message: str
    progress_message: Optional[str] = None
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Code Documentation Agent API",
        "status": "operational",
        "version": "1.0.0",
        "supported_languages": code_loader.get_supported_languages()
    }


@app.on_event("startup")
async def startup_event():
    """Reset any stuck projects on startup."""
    try:
        all_projects = project_store.list_projects()
        stuck_count = 0
        for project in all_projects:
            if project.status in ['processing', 'parsing']:
                project.status = 'error'
                project.progress_message = 'Processing interrupted - backend restarted'
                project_store.save_project(project)
                stuck_count += 1
                logger.warning(f"Reset stuck project: {project.id}")
        
        if stuck_count > 0:
            logger.info(f"Reset {stuck_count} stuck project(s) on startup")
    except Exception as e:
        logger.error(f"Startup reset failed: {e}")


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "pipeline": "code_documentation",
        "timestamp": datetime.now().isoformat(),
        "supported_languages": code_loader.get_supported_languages()
    }

@app.post("/preferences")
async def set_preferences(
    project_name: str = Body(...),
    documentation_style: str = Body("Google Style"),
    include_examples: bool = Body(True),
    include_diagrams: bool = Body(True)
):
    """
    Set documentation preferences for a project.
    
    Styles: 'Google Style', 'NumPy Style', 'PEP 257', 'JSDoc', 'Javadoc', etc.
    """
    user_preferences_store[project_name] = {
        "style": documentation_style,
        "include_examples": include_examples,
        "include_diagrams": include_diagrams
    }
    
    # Also update pipeline preferences
    langgraph_pipeline.user_preferences[project_name] = user_preferences_store[project_name]
    
    return {
        "message": "Preferences saved",
        "preferences": user_preferences_store[project_name]
    }


@app.get("/preferences/{project_name}")
async def get_preferences(project_name: str):
    """Get documentation preferences for a project."""
    prefs = user_preferences_store.get(project_name, {
        "style": "Google Style",
        "include_examples": True,
        "include_diagrams": True
    })
    return prefs

@app.post("/projects/{project_id}/review")
async def submit_human_review(
    project_id: str,
    approved: bool = Body(...),
    feedback: str = Body(""),
    approved_sections: List[str] = Body(default=[])
):
    """
    Submit human review feedback (HITL).
    
    This allows reviewers to approve or request changes to documentation.
    """
    project = project_store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Store review feedback
    review_data = {
        "approved": approved,
        "feedback": feedback,
        "approved_sections": approved_sections,
        "timestamp": datetime.now().isoformat()
    }
    
    # In production, this would trigger workflow continuation
    # For now, just store the feedback
    project.status = "reviewed" if approved else "needs_revision"
    project.progress_message = f"Review: {feedback}" if feedback else "Reviewed"
    project_store.save_project(project)
    
    return {
        "message": "Review submitted",
        "status": project.status,
        "review": review_data
    }

@app.post("/projects/upload", response_model=ProjectResponse)
async def upload_code(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload source code file(s) and create a documentation project.
    Checks if file already exists to enable change tracking.
    
    Supported: Python, JavaScript, TypeScript, Java, C#, Go, Rust, Ruby, PHP, and more
    """
    try:
        # Check if file is supported
        if not code_loader.is_supported_language(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(code_loader.get_supported_extensions())}"
            )
        
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Detect language
        language = code_loader.detect_language(file.filename)
        
        # Check if project with same filename already exists
        existing_project = None
        all_projects = project_store.list_projects()
        for proj in all_projects:
            if proj.file_name == file.filename:
                existing_project = proj
                break
        
        if existing_project:
            # UPDATE existing project
            project_id = existing_project.id
            project = existing_project
            
            # Store old code as previous version
            old_file_content = project_store.get_file(project_id)
            if old_file_content:
                project_store.save_file(f"{project_id}_previous", old_file_content, f"{file.filename}.previous")
            
            # Update project with new file
            project.file_size = file_size
            project.status = "uploaded"
            project.uploaded_at = datetime.now()
            project_store.save_project(project)
            project_store.save_file(project_id, file_content, file.filename)
            
            logger.info(f"Project UPDATED: {project_id} - {file.filename} ({language})")
        else:
            # CREATE new project
            project_id = str(uuid.uuid4())
            project_name = file.filename.rsplit('.', 1)[0]
            
            project = ProjectMetadata(
                id=project_id,
                name=project_name,
                file_name=file.filename,
                file_size=file_size,
                language=language,
                status="uploaded",
                uploaded_at=datetime.now()
            )
            
            project_store.save_project(project)
            project_store.save_file(project_id, file_content, file.filename)
            
            logger.info(f"Project CREATED: {project_id} - {file.filename} ({language})")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            file_name=project.file_name,
            file_size=project.file_size,
            language=project.language,
            status=project.status,
            uploaded_at=project.uploaded_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
@app.post("/projects/upload-folder", response_model=List[ProjectResponse])
async def upload_folder(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload multiple code files from a folder"""
    try:
        uploaded_projects = []
        
        for file in files:
            if not code_loader.is_supported_language(file.filename):
                continue  # Skip unsupported files
            
            file_content = await file.read()
            file_size = len(file_content)
            
            if file_size == 0:
                continue
            
            language = code_loader.detect_language(file.filename)
            project_id = str(uuid.uuid4())
            project_name = file.filename.rsplit('.', 1)[0]
            
            project = ProjectMetadata(
                id=project_id,
                name=project_name,
                file_name=file.filename,
                file_size=file_size,
                language=language,
                status="uploaded",
                uploaded_at=datetime.now()
            )
            
            project_store.save_project(project)
            project_store.save_file(project_id, file_content, file.filename)
            
            uploaded_projects.append(ProjectResponse(
                id=project.id,
                name=project.name,
                file_name=project.file_name,
                file_size=project.file_size,
                language=project.language,
                status=project.status,
                uploaded_at=project.uploaded_at
            ))
        
        return uploaded_projects
        
    except Exception as e:
        logger.error(f"Folder upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.post("/projects/{project_id}/process", response_model=ProcessingStatus)
async def process_project(project_id: str, background_tasks: BackgroundTasks):
    """
    Process uploaded code and generate documentation.
    
    Triggers AI pipeline to analyze code and create comprehensive documentation.
    """
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status == "completed":
            return ProcessingStatus(
                project_id=project_id,
                status="completed",
                message="Project already processed"
            )
        
        # Start processing in background
        background_tasks.add_task(process_project_task, project_id)
        
        # Update status
        project.status = "processing"
        project_store.save_project(project)
        
        return ProcessingStatus(
            project_id=project_id,
            status="processing",
            message="Documentation generation started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/progress-stream")
async def stream_progress(project_id: str):
    """Stream real-time progress updates using Server-Sent Events."""
    async def event_generator():
        try:
            project = project_store.get_project(project_id)
            if not project:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Project not found"})
                }
                return
            
            queue = progress_queues[project_id]
            
            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": project.status,
                    "progress_message": project.progress_message or "Starting...",
                    "current_chunk": project.current_chunk or 0,
                    "total_chunks": project.total_chunks or 0,
                    "timestamp": datetime.now().isoformat()
                })
            }
            
            max_duration = 300
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_duration:
                try:
                    try:
                        event = queue.get_nowait()
                        
                        yield {
                            "event": event.get("event", "progress"),
                            "data": json.dumps(event.get("data", {}))
                        }
                        
                        if event.get("data", {}).get("status") in ["completed", "error"]:
                            break
                    
                    except:
                        await asyncio.sleep(1.5)
                        
                        project = project_store.get_project(project_id)
                        if project and project.status in ["completed", "error"]:
                            yield {
                                "event": "progress",
                                "data": json.dumps({
                                    "status": project.status,
                                    "progress_message": project.progress_message or "Done",
                                    "current_chunk": project.current_chunk or 0,
                                    "total_chunks": project.total_chunks or 0,
                                    "timestamp": datetime.now().isoformat()
                                })
                            }
                            break
                        
                        yield {
                            "event": "heartbeat",
                            "data": json.dumps({"timestamp": datetime.now().isoformat()})
                        }
                        
                except Exception as e:
                    logger.error(f"SSE error: {e}")
                    break
                        
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            if project_id in progress_queues:
                del progress_queues[project_id]
    
    return EventSourceResponse(event_generator())


async def process_project_task(project_id: str):
    """Background task to process code documentation."""
    try:
        project = project_store.get_project(project_id)
        logger.info(f"Starting documentation generation for: {project_id}")
        
        project.status = "parsing"
        project.progress_message = "Analyzing code structure..."
        project_store.save_project(project)
        
        file_content = project_store.get_file(project_id)
        
        from io import BytesIO
        file_obj = BytesIO(file_content)
        file_obj.name = project.file_name
        
        def update_progress(current: int, total: int, message: str):
            """Update and broadcast progress."""
            project.current_chunk = current
            project.total_chunks = total
            project.progress_message = message
            project_store.save_project(project)
            logger.info(f"Progress [{current}/{total}]: {message}")
            
            if project_id in progress_queues:
                event = {
                    "event": "progress",
                    "data": {
                        "status": project.status,
                        "progress_message": message,
                        "current_chunk": current,
                        "total_chunks": total,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                progress_queues[project_id].put(event)
        
        # Get previous code if this is an update
        previous_code = None
        if project.documentation:
            # This is an update - get previous code
            previous_file = project_store.get_file(f"{project_id}_previous")
            if previous_file:
                previous_code = previous_file.decode('utf-8')
        
        # Store current code as previous for next update
        project_store.save_file(f"{project_id}_previous", file_content, f"{project.file_name}.previous")
        
        # Run pipeline in thread pool with previous code
        loop = asyncio.get_event_loop()
        logger.info(f"Using LangGraph multi-agent pipeline for {project_id}")
        
        # Pass previous_code to pipeline
        def run_pipeline():
            from io import BytesIO
            file_obj = BytesIO(file_content)
            file_obj.name = project.file_name
            return langgraph_pipeline.run_from_uploaded_file_with_changes(
                file_obj,
                project.name,
                update_progress,
                previous_code
            )
        
        parsed_code, documentation = await loop.run_in_executor(None, run_pipeline)
        
        project.parsed_code = parsed_code
        project.documentation = documentation
        project.status = "completed"
        project.progress_message = "✅ Documentation generation completed!"
        project_store.save_project(project)
        
        if project_id in progress_queues:
            event = {
                "event": "progress",
                "data": {
                    "status": "completed",
                    "progress_message": "✅ Documentation generation completed!",
                    "current_chunk": project.total_chunks or 0,
                    "total_chunks": project.total_chunks or 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
            progress_queues[project_id].put(event)
        
        logger.info(f"Documentation completed for: {project_id}")
        
    except Exception as e:
        logger.error(f"Processing failed for {project_id}: {e}", exc_info=True)
        project = project_store.get_project(project_id)
        if project:
            project.status = "error"
            project.progress_message = f"❌ Error: {str(e)}"
            project_store.save_project(project)
            
            if project_id in progress_queues:
                event = {
                    "event": "progress",
                    "data": {
                        "status": "error",
                        "progress_message": f"❌ Error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                progress_queues[project_id].put(event)


@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """Get list of all projects."""
    try:
        projects = project_store.list_projects()
        return [
            ProjectResponse(
                id=p.id,
                name=p.name,
                file_name=p.file_name,
                file_size=p.file_size,
                language=p.language,
                status=p.status,
                uploaded_at=p.uploaded_at,
                progress_message=getattr(p, 'progress_message', None),
                current_chunk=getattr(p, 'current_chunk', None),
                total_chunks=getattr(p, 'total_chunks', None)
            )
            for p in projects
        ]
    except Exception as e:
        logger.error(f"List projects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details."""
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            file_name=project.file_name,
            file_size=project.file_size,
            language=project.language,
            status=project.status,
            uploaded_at=project.uploaded_at,
            progress_message=getattr(project, 'progress_message', None),
            current_chunk=getattr(project, 'current_chunk', None),
            total_chunks=getattr(project, 'total_chunks', None)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/analysis")
async def get_code_analysis(project_id: str):
    """Get code analysis for a project."""
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.parsed_code:
            raise HTTPException(status_code=400, detail="Code not yet analyzed")
        
        return project.parsed_code.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/documentation")
async def get_documentation(project_id: str):
    """Get generated documentation for a project."""
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.documentation:
            raise HTTPException(status_code=400, detail="Documentation not yet generated")
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "language": project.language,
            "content": project.documentation,
            "word_count": len(project.documentation.split()),
            "generated_at": project.uploaded_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get documentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/pdf")
async def generate_pdf(project_id: str):
    """Generate PDF from documentation."""
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.documentation:
            raise HTTPException(status_code=400, detail="Documentation not yet generated")
        
        from backend.core.pdf_generator import PDFGenerator
        
        def _generate_pdf():
            pdf_generator = PDFGenerator()
            return pdf_generator.generate_pdf_bytes(project.documentation, project.name)
        
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(None, _generate_pdf)
        
        import re
        clean_name = re.sub(r'\.(py|js|java|cpp|go|rs|rb)$', '', project.name, flags=re.IGNORECASE)
        safe_filename = clean_name.replace('"', '').replace('/', '-').replace('\\', '-')
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}_Documentation.pdf"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


@app.post("/pdf/generate")
async def generate_pdf_from_content(content: str = Body(...), filename: str = Body("documentation")):
    """Generate PDF from custom markdown content."""
    try:
        from backend.core.pdf_generator import PDFGenerator
        
        def _generate_pdf():
            pdf_generator = PDFGenerator()
            return pdf_generator.generate_pdf_bytes(content, filename)
        
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(None, _generate_pdf)
        
        safe_filename = filename.replace('"', '').replace('/', '-').replace('\\', '-')
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}.pdf"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/reset")
async def reset_project(project_id: str):
    """Reset a stuck project."""
    try:
        project = project_store.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project.status = 'uploaded'
        project.progress_message = 'Ready to process'
        project.current_chunk = None
        project.total_chunks = None
        project.parsed_code = None
        project.documentation = None
        project_store.save_project(project)
        
        if project_id in progress_queues:
            del progress_queues[project_id]
        
        logger.info(f"Reset project: {project_id}")
        return {"message": "Project reset successfully", "status": project.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    try:
        success = project_store.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logger.info(f"Project deleted: {project_id}")
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
from fastapi import APIRouter, BackgroundTasks, HTTPException
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))



from shared.models import DocRequest, JobStatus
from backend.app.services.job_service import (
    create_job,
    get_job_status as get_status,
    get_job_result,
    run_documentation_job
)


router = APIRouter(prefix="/api", tags=["documentation"])


@router.post("/generate-docs")
async def generate_documentation(
    request: DocRequest,
    background_tasks: BackgroundTasks
):
    """Start documentation generation job."""
    
    language = request.language if hasattr(request, 'language') else None
    generate_diagram = request.generate_diagram if hasattr(request, 'generate_diagram') else True
    generate_pdf = request.generate_pdf if hasattr(request, 'generate_pdf') else False
    
    job_id = create_job(
        request.code_path, 
        request.project_name, 
        language,
        generate_diagram,
        generate_pdf
    )
    
    # Run in background
    background_tasks.add_task(
        run_documentation_job,
        job_id,
        request.code_path,
        request.project_name,
        language,
        generate_diagram,
        generate_pdf
    )
    
    return {
        "job_id": job_id,
        "status": "created",
        "message": "Documentation generation started"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status."""
    status = get_status(job_id)
    return status


@router.get("/docs/{job_id}")
async def get_generated_docs(job_id: str):
    """Get generated documentation."""
    result = get_job_result(job_id)
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result
@router.get("/download/pdf/{job_id}")
async def download_pdf(job_id: str):
    """Download generated PDF."""
    from fastapi.responses import FileResponse
    
    job = get_job_status(job_id)
    
    if job.get('status') != 'completed':
        raise HTTPException(status_code=404, detail="Job not completed")
    
    pdf_path = job.get('pdf_path')
    
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        path=pdf_path,
        media_type='application/pdf',
        filename=os.path.basename(pdf_path)
    )
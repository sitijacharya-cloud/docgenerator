import uuid
from typing import Dict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.graph.workflow import create_documentation_workflow


# In-memory job storage (use Redis/DB in production)
jobs_storage: Dict[str, Dict] = {}

async def run_documentation_job(job_id: str, code_path: str, project_name: str, 
                                language: str = None, generate_diagram: bool = True, 
                                generate_pdf: bool = False):
    """Run documentation generation workflow."""
    try:
        # Auto-detect language if not provided
        if not language:
            from agents.parsers.parser_factory import ParserFactory
            language = ParserFactory.detect_language(code_path)
        
        # Update job status
        jobs_storage[job_id]['status'] = 'processing'
        jobs_storage[job_id]['progress'] = f'Starting workflow for {language}...'
        jobs_storage[job_id]['language'] = language
        
        # Create and run workflow
        workflow = create_documentation_workflow()
        
        initial_state = {
            'code_path': code_path,
            'project_name': project_name,
            'language': language,
            'generate_diagram': generate_diagram,     # NEW
            'generate_pdf': generate_pdf,             # NEW
            'parsed_files': [],
            'code_components': [],
            'generated_docstrings': {},
            'markdown_content': '',
            'relationship_analysis': None,            # NEW
            'mermaid_diagram': None,                  # NEW
            'pdf_path': None,                         # NEW
            'validation_results': {},
            'output_path': None,
            'status': 'started',
            'errors': []
        }
        
        # Run the workflow
        result = workflow.invoke(initial_state)
        
        # Update job with results
        if result['status'] in ['completed', 'pdf_generation_complete', 'pdf_failed']:
            jobs_storage[job_id]['status'] = 'completed'
            jobs_storage[job_id]['output_path'] = result.get('output_path')
            jobs_storage[job_id]['pdf_path'] = result.get('pdf_path')  # NEW
            jobs_storage[job_id]['result'] = {
                'markdown_content': result.get('markdown_content'),
                'validation_results': result.get('validation_results'),
                'component_count': len(result.get('code_components', [])),
                'has_diagram': result.get('mermaid_diagram') is not None,  # NEW
                'pdf_path': result.get('pdf_path')                         # NEW
            }
        else:
            jobs_storage[job_id]['status'] = 'failed'
            jobs_storage[job_id]['error'] = '; '.join(result.get('errors', ['Unknown error']))
        
    except Exception as e:
        jobs_storage[job_id]['status'] = 'failed'
        jobs_storage[job_id]['error'] = str(e)
        print(f"Job error: {e}")
        import traceback
        traceback.print_exc()


def create_job(code_path: str, project_name: str, language: str = None, 
               generate_diagram: bool = True, generate_pdf: bool = False) -> str:
    """Create a new documentation job."""
    job_id = str(uuid.uuid4())
    
    jobs_storage[job_id] = {
        'job_id': job_id,
        'code_path': code_path,
        'project_name': project_name,
        'language': language,
        'generate_diagram': generate_diagram,  # NEW
        'generate_pdf': generate_pdf,          # NEW
        'status': 'created',
        'progress': '',
        'output_path': None,
        'pdf_path': None,                      # NEW
        'error': None,
        'result': None
    }
    
    return job_id



def get_job_status(job_id: str) -> Dict:
    """Get job status."""
    return jobs_storage.get(job_id, {
        'job_id': job_id,
        'status': 'not_found',
        'error': 'Job not found'
    })


def get_job_result(job_id: str) -> Dict:
    """Get job result."""
    job = jobs_storage.get(job_id)
    
    if not job:
        return {'error': 'Job not found'}
    
    if job['status'] != 'completed':
        return {'error': f"Job status: {job['status']}"}
    
    return job.get('result', {})
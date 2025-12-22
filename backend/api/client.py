import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path
import time


class APIClient:
    """Client for Code Documentation Agent FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client."""
        self.base_url = base_url
        self.timeout = 300.0  # 5 minutes for processing
    
    
    
    def upload_code(self, file_path: Path = None, file_bytes: bytes = None, filename: str = None) -> Dict[str, Any]:
        """
        Upload source code file(s) to create a documentation project.
        
        Args:
            file_path: Path to code file (if uploading from disk)
            file_bytes: File bytes (if uploading from memory)
            filename: Filename to use
        
        Returns:
            Project metadata
        """
        try:
            if file_path:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f)}
                    response = httpx.post(
                        f"{self.base_url}/projects/upload",
                        files=files,
                        timeout=30.0
                    )
            elif file_bytes and filename:
                files = {'file': (filename, file_bytes)}
                response = httpx.post(
                    f"{self.base_url}/projects/upload",
                    files=files,
                    timeout=30.0
                )
            else:
                raise ValueError("Must provide either file_path or (file_bytes + filename)")
            
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise TimeoutError("Backend is busy processing. Try using progress stream instead.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Upload failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")
        
    def upload_folder(self, files_data: List[tuple]) -> List[Dict[str, Any]]:
        """Upload multiple files from a folder"""
        try:
            files = [
                ('files', (filename, content, 'application/octet-stream'))
                for filename, content in files_data
            ]
            response = httpx.post(
                f"{self.base_url}/projects/upload-folder",
                files=files,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Folder upload failed: {str(e)}")

    

    def process_project(self, project_id: str) -> Dict[str, Any]:
        """
        Start processing a code documentation project (non-blocking).
        
        Args:
            project_id: Project ID
        
        Returns:
            Processing status
        """
        try:
            response = httpx.post(
                f"{self.base_url}/projects/{project_id}/process",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"project_id": project_id, "status": "processing", "message": "Processing started"}
        except httpx.HTTPStatusError as e:
            raise Exception(f"Process failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Process error: {str(e)}")
    
    def get_project(self, project_id: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Get project details."""
        try:
            response = httpx.get(
                f"{self.base_url}/projects/{project_id}",
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"Get project failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Get project error: {str(e)}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """Get list of all projects."""
        try:
            response = httpx.get(
                f"{self.base_url}/projects",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return []
        except Exception as e:
            raise Exception(f"List projects error: {str(e)}")
    
    def get_code_analysis(self, project_id: str) -> Dict[str, Any]:
        """
        Get parsed code analysis for a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            Code analysis data
        """
        try:
            response = httpx.get(
                f"{self.base_url}/projects/{project_id}/analysis",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise Exception(f"Get analysis failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Get analysis error: {str(e)}")
    
    def get_documentation(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get generated code documentation.
        
        Args:
            project_id: Project ID
        
        Returns:
            Documentation data
        """
        try:
            response = httpx.get(
                f"{self.base_url}/projects/{project_id}/documentation",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise Exception(f"Get documentation failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Get documentation error: {str(e)}")
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        try:
            response = httpx.delete(
                f"{self.base_url}/projects/{project_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise Exception(f"Delete project failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Delete project error: {str(e)}")
    
    def generate_pdf(self, project_id: str) -> bytes:
        """Generate PDF for a project."""
        try:
            response = httpx.post(
                f"{self.base_url}/projects/{project_id}/pdf",
                timeout=60.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            pdf_bytes = response.content
            
            if not pdf_bytes or len(pdf_bytes) < 100:
                raise Exception(f"PDF too small or empty: {len(pdf_bytes)} bytes")
            
            if not pdf_bytes.startswith(b'%PDF'):
                preview = pdf_bytes[:50].decode('utf-8', errors='replace')
                raise Exception(f"Invalid PDF format. Received: {preview}")
            
            return pdf_bytes
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"PDF generation failed: {error_text}")
        except Exception as e:
            raise Exception(f"PDF generation error: {str(e)}")
    
    def generate_pdf_from_content(self, content: str, filename: str = "documentation") -> bytes:
        """Generate PDF from markdown content."""
        try:
            response = httpx.post(
                f"{self.base_url}/pdf/generate",
                json={"content": content, "filename": filename},
                timeout=60.0
            )
            response.raise_for_status()
            
            pdf_bytes = response.content
            
            if not pdf_bytes or len(pdf_bytes) < 100:
                raise Exception(f"PDF too small or empty: {len(pdf_bytes)} bytes")
            
            if not pdf_bytes.startswith(b'%PDF'):
                raise Exception("Invalid PDF format")
            
            return pdf_bytes
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"PDF generation failed: {error_text}")
        except Exception as e:
            raise Exception(f"PDF generation error: {str(e)}")
    
    def reset_project(self, project_id: str) -> Dict[str, Any]:
        """Reset a stuck project to allow reprocessing."""
        try:
            response = httpx.post(
                f"{self.base_url}/projects/{project_id}/reset",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Reset project error: {str(e)}")
    
    def wait_for_completion(self, project_id: str, check_interval: float = 2.0, max_wait: float = 300.0) -> str:
        """Wait for project processing to complete."""
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            project = self.get_project(project_id)
            if not project:
                raise Exception("Project not found")
            
            status = project['status']
            
            if status in ['completed', 'error']:
                return status
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"Processing did not complete within {max_wait} seconds")
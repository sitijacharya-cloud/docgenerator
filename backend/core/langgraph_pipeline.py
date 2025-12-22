from pathlib import Path
from typing import Union, Tuple, Callable, Optional, Dict, Any
import uuid
from backend.core.code_loader import CodeLoader
from backend.core.langgraph_supervisor import LangGraphSupervisorWorkflow, SupervisorState
from backend.core.models import ParsedCode
import os


class LangGraphPipeline:
    """
    Multi-agent pipeline using LangGraph for Code to Documentation.
    
    Features:
    - Multi-agent collaboration (Parser, Docstring Generator, Markdown Writer, Validator)
    - Automatic quality checks and validation loops
    - State persistence across workflow execution
    - Support for multiple programming languages
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LangGraph pipeline with agents"""
        self.loader = CodeLoader()
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.workflow = LangGraphSupervisorWorkflow(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
        )
        
        # Track active workflows
        self.active_workflows: Dict[str, str] = {}  # project_id -> thread_id
        # User preferences storage
        self.user_preferences = {}
    def run_from_file(
        self,
        file_path: Union[str, Path],
        project_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[ParsedCode, str]:
        """
        Run LangGraph pipeline from a file path.
        
        Args:
            file_path: Path to source code file
            project_name: Name of the project
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Tuple of (ParsedCode, documentation_markdown)
        """
        if progress_callback:
            progress_callback(0, 0, "Loading source code...")
        
        code_content, language = self.loader.load_code(file_path)
        
        return self._run_workflow(code_content, language, project_name, progress_callback)
    
    def run_from_uploaded_file(
        self,
        uploaded_file,
        project_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[ParsedCode, str]:
        """
        Run LangGraph pipeline from uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            project_name: Name of the project
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Tuple of (ParsedCode, documentation_markdown)
        """
        if progress_callback:
            progress_callback(0, 0, "Loading source code...")
        
        code_content, language = self.loader.load_from_uploaded_file(uploaded_file)
        
        return self._run_workflow(code_content, language, project_name, progress_callback)
    
    def run_from_uploaded_file_with_changes(
        self,
        uploaded_file,
        project_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        previous_code: Optional[str] = None
    ) -> Tuple[ParsedCode, str]:
        """
        Run pipeline with change tracking support.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            project_name: Name of the project
            progress_callback: Optional callback(current, total, message)
            previous_code: Previous version of code (for change tracking)
        
        Returns:
            Tuple of (ParsedCode, documentation_markdown)
        """
        if progress_callback:
            progress_callback(0, 0, "Loading source code...")
        
        code_content, language = self.loader.load_from_uploaded_file(uploaded_file)
        
        return self._run_workflow_with_changes(
            code_content, 
            language, 
            project_name, 
            progress_callback,
            previous_code
        )
    
    def _run_workflow_with_changes(
        self,
        code_content: str,
        language: str,
        project_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        previous_code: Optional[str] = None
    ) -> Tuple[ParsedCode, str]:
        """Execute workflow with change tracking"""
        
        thread_id = str(uuid.uuid4())
        
        if progress_callback:
            if previous_code:
                progress_callback(0, 100, "Initializing with change detection...")
            else:
                progress_callback(0, 100, "Initializing code documentation workflow...")
        
        # Get user preferences
        user_prefs = self.user_preferences.get(project_name, {})
        
        # Execute workflow with previous code
        final_state = self.workflow.process_code(
            code_content=code_content,
            language=language,
            project_name=project_name,
            thread_id=thread_id,
            progress_callback=progress_callback,
            user_preferences=user_prefs,
            previous_code=previous_code  # NEW: Pass previous code
        )
        
        if final_state.get("error"):
            raise RuntimeError(f"Workflow failed: {final_state['error']}")
        
        parsed_code = self._state_to_parsed_code(final_state)
        documentation = final_state.get("final_documentation", "")
        
        if progress_callback:
            progress_callback(100, 100, "Documentation workflow completed!")
        
        return parsed_code, documentation
    def _run_workflow(
        self,
        code_content: str,
        language: str,
        project_name: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[ParsedCode, str]:
        """Execute the LangGraph multi-agent workflow"""
        
        # Generate unique thread ID for this workflow
        thread_id = str(uuid.uuid4())
        
        if progress_callback:
            progress_callback(0, 100, "Initializing code documentation workflow...")
        
        user_prefs = self.user_preferences.get(project_name, {})
        
        final_state = self.workflow.process_code(
            code_content=code_content,
            language=language,
            project_name=project_name,
            thread_id=thread_id,
            progress_callback=progress_callback,
            user_preferences=user_prefs  # NEW: Pass preferences
        )
        
        # Check for errors
        if final_state.get("error"):
            raise RuntimeError(f"Workflow failed: {final_state['error']}")
        
        # Convert state to ParsedCode format for compatibility
        parsed_code = self._state_to_parsed_code(final_state)
        documentation = final_state.get("final_documentation", "")
        
        if progress_callback:
            progress_callback(100, 100, "Code documentation workflow completed!")
        
        return parsed_code, documentation
    
    def _state_to_parsed_code(self, state: Dict[str, Any]) -> ParsedCode:
        """Convert LangGraph state to ParsedCode model"""
        return ParsedCode(
            project_name=state.get("project_name", ""),
            language=state.get("language", ""),
            file_path="uploaded_file",
            functions=[],
            classes=[],
            modules=[],
            dependencies=[]
        )
    
    def get_workflow_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a workflow for a project"""
        thread_id = self.active_workflows.get(project_id)
        if not thread_id:
            return None
        return None
    
    def start_async_workflow(
        self,
        code_content: str,
        language: str,
        project_id: str,
        project_name: str
    ) -> str:
        """
        Start an async workflow.
        Returns thread_id for tracking.
        """
        thread_id = str(uuid.uuid4())
        self.active_workflows[project_id] = thread_id
        return thread_id
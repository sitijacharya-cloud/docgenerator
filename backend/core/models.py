from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FunctionInfo(BaseModel):
    """Information about a function."""
    name: str = Field(description="Function name")
    signature: str = Field(description="Full function signature")
    docstring: Optional[str] = Field(None, description="Function docstring")
    parameters: List[Dict[str, str]] = Field(default_factory=list, description="Parameter info")
    return_type: Optional[str] = Field(None, description="Return type")
    exceptions: List[str] = Field(default_factory=list, description="Exceptions raised")
    line_number: Optional[int] = Field(None, description="Starting line number")
    complexity: Optional[str] = Field(None, description="Complexity notes")


class ClassInfo(BaseModel):
    """Information about a class."""
    name: str = Field(description="Class name")
    docstring: Optional[str] = Field(None, description="Class docstring")
    bases: List[str] = Field(default_factory=list, description="Base classes")
    attributes: List[Dict[str, str]] = Field(default_factory=list, description="Class attributes")
    methods: List[FunctionInfo] = Field(default_factory=list, description="Class methods")
    line_number: Optional[int] = Field(None, description="Starting line number")


class ModuleInfo(BaseModel):
    """Information about a module."""
    name: str = Field(description="Module name")
    docstring: Optional[str] = Field(None, description="Module docstring")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    functions: List[FunctionInfo] = Field(default_factory=list, description="Module-level functions")
    classes: List[ClassInfo] = Field(default_factory=list, description="Module classes")


class DependencyInfo(BaseModel):
    """External dependency information."""
    name: str = Field(description="Dependency name")
    version: Optional[str] = Field(None, description="Version if specified")
    purpose: Optional[str] = Field(None, description="Why this dependency is used")


class ParsedCode(BaseModel):
    """Complete parsed code structure."""
    
    # Project metadata
    project_name: str = Field(description="Project name")
    language: str = Field(description="Programming language")
    file_path: str = Field(description="Original file path")
    
    # Code components
    functions: List[FunctionInfo] = Field(default_factory=list, description="All functions")
    classes: List[ClassInfo] = Field(default_factory=list, description="All classes")
    modules: List[ModuleInfo] = Field(default_factory=list, description="Module information")
    
    # Dependencies and imports
    dependencies: List[DependencyInfo] = Field(default_factory=list, description="External dependencies")
    
    # Metrics
    total_lines: Optional[int] = Field(None, description="Total lines of code")
    documented_items: Optional[int] = Field(None, description="Number of documented items")
    undocumented_items: Optional[int] = Field(None, description="Number of undocumented items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "MyProject",
                "language": "Python",
                "file_path": "main.py",
                "functions": [
                    {
                        "name": "calculate",
                        "signature": "calculate(x: int, y: int) -> int",
                        "docstring": "Calculate the sum of two numbers",
                        "parameters": [
                            {"name": "x", "type": "int", "description": "First number"},
                            {"name": "y", "type": "int", "description": "Second number"}
                        ],
                        "return_type": "int"
                    }
                ]
            }
        }


class DocumentationArtifact(BaseModel):
    """Generated documentation artifact."""
    project_name: str
    language: str
    generated_at: datetime = Field(default_factory=datetime.now)
    markdown_content: str = Field(description="Complete documentation in Markdown")
    parsed_code: ParsedCode = Field(description="Source parsed code")
    
    # Quality metrics
    documentation_coverage: Optional[float] = Field(None, description="Percentage of documented items")
    validation_passed: bool = Field(default=True, description="Whether validation passed")
    issues_found: List[str] = Field(default_factory=list, description="Documentation issues")
    
    def get_word_count(self) -> int:
        """Get word count of generated documentation."""
        return len(self.markdown_content.split())
    
    def get_section_count(self) -> int:
        """Get number of main sections."""
        lines = self.markdown_content.split('\n')
        return sum(1 for line in lines if line.startswith('#'))


class ProjectMetadata(BaseModel):
    """Project metadata for tracking."""
    id: str = Field(description="Unique project identifier")
    name: str = Field(description="Project name")
    uploaded_at: datetime = Field(default_factory=datetime.now)
    file_name: str = Field(description="Original file name")
    file_size: int = Field(description="File size in bytes")
    language: Optional[str] = Field(None, description="Detected programming language")
    status: str = Field(default="uploaded", description="Processing status")
    parsed_code: Optional[ParsedCode] = None
    documentation: Optional[str] = None
    progress_message: Optional[str] = None
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None
    
    def get_status_emoji(self) -> str:
        """Get emoji for current status."""
        status_map = {
            "uploaded": "📄",
            "parsing": "🔄",
            "parsed": "✅",
            "generating": "⚙️",
            "completed": "✨",
            "error": "❌",
        }
        return status_map.get(self.status, "❓")
class ChangeInfo(BaseModel):
    """Information about code changes"""
    type: str = Field(description="addition, deletion, or modification")
    name: str = Field(description="Name of changed item")
    item_type: str = Field(description="function or class")
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
class ChangeReport(BaseModel):
    """Complete change tracking report"""
    summary: str
    additions: List[ChangeInfo] = Field(default_factory=list)
    deletions: List[ChangeInfo] = Field(default_factory=list)
    modifications: List[ChangeInfo] = Field(default_factory=list)
    markdown: str = Field(default="")
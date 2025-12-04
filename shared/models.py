from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
class LanguageType(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"

class ComponentType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"


class Parameter(BaseModel):
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None


class CodeComponent(BaseModel):
    id: str
    type: ComponentType
    name: str
    file_path: str
    signature: str
    parameters: List[Parameter] = []
    return_type: Optional[str] = None
    decorators: List[str] = []
    existing_docstring: Optional[str] = None
    source_code: str
    line_number: int


class ParsedFile(BaseModel):
    file_path: str
    module_name: str
    source_code: str
    module_docstring: Optional[str] = None


class ValidationResult(BaseModel):
    component_id: str
    score: float
    issues: List[str] = []
    warnings: List[str] = []


class DocRequest(BaseModel):
    code_path: str
    project_name: str = "project"
    language: Optional[str] = None 
    generate_diagram: bool = True     
    generate_pdf: bool = False


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: str = ""
    output_path: Optional[str] = None
    error: Optional[str] = None
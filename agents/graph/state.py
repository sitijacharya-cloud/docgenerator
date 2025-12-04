from typing import TypedDict, List, Dict, Optional


class DocumentationState(TypedDict):
    # Input
    code_path: str
    project_name: str

    #lanugugae
    language: str
    generate_diagram: bool      # NEW
    generate_pdf: bool   
    # Processing
    parsed_files: List[Dict]
    code_components: List[Dict]
    generated_docstrings: Dict[str, str]
    markdown_content: str
    relationship_analysis: Optional[Dict]
    mermaid_diagram: Optional[str]
    pdf_path: Optional[str]
    # Validation
    validation_results: Dict
    
    # Output
    output_path: Optional[str]
    
    # Metadata
    status: str
    errors: List[str]
from langgraph.graph import StateGraph, END
from .state import DocumentationState
from .nodes import (
    parse_code_node,
    extract_components_node,
    generate_docstrings_node,
    validate_docstrings_node,
    analyze_relationships_node,     # NEW
    generate_diagram_node,          # NEW
    generate_markdown_node,
    generate_pdf_node,              # NEW
    save_output_node
)


def should_generate_diagram(state: DocumentationState) -> str:
    """Decide if diagram should be generated."""
    if state.get('generate_diagram', False):
        return "generate_diagram"
    return "generate_markdown"


def should_generate_pdf(state: DocumentationState) -> str:
    """Decide if PDF should be generated."""
    if state.get('generate_pdf', False):
        return "generate_pdf"
    return "save_output"


def create_documentation_workflow():
    """Create the LangGraph workflow for documentation generation."""
    
    workflow = StateGraph(DocumentationState)
    
    # Add nodes
    workflow.add_node("parse_code", parse_code_node)
    workflow.add_node("extract_components", extract_components_node)
    workflow.add_node("generate_docstrings", generate_docstrings_node)
    workflow.add_node("validate", validate_docstrings_node)
    workflow.add_node("analyze_relationships", analyze_relationships_node)  # NEW
    workflow.add_node("generate_diagram", generate_diagram_node)            # NEW
    workflow.add_node("generate_markdown", generate_markdown_node)
    workflow.add_node("generate_pdf", generate_pdf_node)                    # NEW
    workflow.add_node("save_output", save_output_node)
    
    # Define edges
    workflow.set_entry_point("parse_code")
    workflow.add_edge("parse_code", "extract_components")
    workflow.add_edge("extract_components", "generate_docstrings")
    workflow.add_edge("generate_docstrings", "validate")
    workflow.add_edge("validate", "analyze_relationships")
    
    # Conditional: generate diagram or skip
    workflow.add_conditional_edges(
        "analyze_relationships",
        should_generate_diagram,
        {
            "generate_diagram": "generate_diagram",
            "generate_markdown": "generate_markdown"
        }
    )
    
    workflow.add_edge("generate_diagram", "generate_markdown")
    
    # Conditional: generate PDF or skip
    workflow.add_conditional_edges(
        "generate_markdown",
        should_generate_pdf,
        {
            "generate_pdf": "generate_pdf",
            "save_output": "save_output"
        }
    )
    
    workflow.add_edge("generate_pdf", "save_output")
    workflow.add_edge("save_output", END)
    
    return workflow.compile()
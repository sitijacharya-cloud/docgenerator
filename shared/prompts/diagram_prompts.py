DIAGRAM_GENERATION_PROMPT = """You are an expert at creating Mermaid diagrams for code architecture.

Given the following code structure analysis, generate a Mermaid diagram that visualizes the architecture.

Language: {language}
Project: {project_name}

Classes: {classes_list}

Class Hierarchy:
{class_hierarchy}

Dependencies:
{dependencies}

Requirements:
1. Generate a Mermaid class diagram or flowchart
2. Show relationships between classes and methods
3. Keep it clean and readable
4. Use appropriate Mermaid syntax
5. Include only the most important relationships

Generate ONLY the Mermaid diagram code (starting with ```mermaid and ending with ```), no additional text.
"""


def build_diagram_prompt(project_name: str, analysis: dict, language: str) -> str:
    """Build prompt for diagram generation."""
    
    # Format classes list
    classes_list = ", ".join([c['name'] for c in analysis.get('classes', [])])
    
    # Format class hierarchy
    hierarchy_text = ""
    for class_name, info in analysis.get('class_hierarchy', {}).items():
        methods = ", ".join(info['methods'][:5])  # Limit to 5 methods
        hierarchy_text += f"- {class_name}: {methods}\n"
    
    # Format dependencies
    dependencies_text = ""
    for dep in analysis.get('dependencies', [])[:10]:  # Limit to 10
        to_list = ", ".join(dep['to'][:3])  # Limit targets
        dependencies_text += f"- {dep['from']} → {to_list}\n"
    
    return DIAGRAM_GENERATION_PROMPT.format(
        language=language,
        project_name=project_name,
        classes_list=classes_list or "None",
        class_hierarchy=hierarchy_text or "None",
        dependencies=dependencies_text or "None"
    )
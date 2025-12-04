MARKDOWN_GENERATION_PROMPT = """You are a technical documentation expert. Generate a well-structured Markdown documentation file.

Project Name: {project_name}
Total Components: {total_components}

Components Data:
{components_json}

Requirements:
1. Create a professional README-style documentation
2. Include a table of contents with links
3. Organize by modules, then classes, then functions
4. For each component, include:
   - Clear heading with signature
   - Full docstring
   - Source file location and line number
5. Add a quick API reference table at the end
6. Use proper Markdown formatting (headers, code blocks, tables, links)
7. Make it easy to navigate

Generate ONLY the markdown content without any preamble or explanation.
"""


def build_markdown_prompt(project_name: str, components: list, docstrings: dict) -> str:
    """Build the prompt for markdown generation."""
    
    components_data = []
    for comp in components:
        comp_data = {
            'id': comp['id'],
            'type': comp['type'],
            'name': comp['name'],
            'signature': comp['signature'],
            'file_path': comp['file_path'],
            'line_number': comp['line_number'],
            'docstring': docstrings.get(comp['id'], 'No documentation generated.')
        }
        components_data.append(comp_data)
    
    import json
    components_json = json.dumps(components_data, indent=2)
    
    return MARKDOWN_GENERATION_PROMPT.format(
        project_name=project_name,
        total_components=len(components),
        components_json=components_json
    )
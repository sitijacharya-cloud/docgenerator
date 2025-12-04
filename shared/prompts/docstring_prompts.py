DOCSTRING_GENERATION_PROMPT = """You are an expert technical writer specializing in {language} documentation.

Generate comprehensive documentation for the following {language} code component.

Component Type: {component_type}
Component Name: {component_name}
Signature: {signature}
Language: {language}

Source Code:
{source_code}

{context}

Requirements for {language} documentation:
1. Write a brief one-line summary
2. Add a detailed description (2-4 sentences)
3. Document all parameters with types and descriptions
4. Document return value with type and description
5. List any exceptions that might be raised/thrown
6. Include a practical usage example in {language}
7. Use appropriate documentation style for {language}

Generate ONLY the documentation content without any additional text, explanations, or markdown formatting.
"""

CONTEXT_TEMPLATE = """
Here are similar well-documented examples from this codebase:

{examples}

Follow the same style and level of detail.
"""


def build_docstring_prompt(component: dict, similar_examples: list = None, language: str = "python") -> str:
    """Build the prompt for docstring generation."""
    
    context = ""
    if similar_examples:
        examples_text = "\n\n".join([
            f"Example {i+1}:\n{ex['source']}\n\nDocumentation:\n{ex['docstring']}"
            for i, ex in enumerate(similar_examples[:2])
        ])
        context = CONTEXT_TEMPLATE.format(examples=examples_text)
    
    return DOCSTRING_GENERATION_PROMPT.format(
        language=language.title(),
        component_type=component['type'],
        component_name=component['name'],
        signature=component['signature'],
        source_code=component['source_code'],
        context=context
    )
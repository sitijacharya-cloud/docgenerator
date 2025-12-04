from typing import Dict, List
from openai import OpenAI
from shared.prompts.docstring_prompts import build_docstring_prompt
from agents.memory.context_builder import ContextBuilder


class DocstringGenerator:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", 
                 temperature: float = 0.3, max_tokens: int = 1000):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate_docstring(self, component: dict, context_builder: ContextBuilder, language: str = "python") -> str:
        """Generate a docstring for a code component."""
        try:
            # Get similar examples for context
            similar_examples = context_builder.build_context_for_component(component)
            
            # Import here to avoid circular dependency
            from shared.prompts.docstring_prompts import build_docstring_prompt
            
            # Build prompt with language
            prompt = build_docstring_prompt(component, similar_examples, language)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert {language.title()} documentation writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            docstring = response.choices[0].message.content.strip()
            
            # Clean up any markdown code blocks if present
            if docstring.startswith('```'):
                lines = docstring.split('\n')
                docstring = '\n'.join(lines[1:-1]) if len(lines) > 2 else docstring
            
            return docstring
            
        except Exception as e:
            print(f"Error generating docstring for {component.get('name')}: {e}")
            return f"Error generating documentation: {str(e)}"


    def generate_batch(self, components: List[dict], context_builder: ContextBuilder, language: str = "python") -> Dict[str, str]:
        """Generate docstrings for multiple components."""
        docstrings = {}
        
        for component in components:
            component_id = component['id']
            print(f"Generating {language} docstring for: {component_id}")
            
            docstring = self.generate_docstring(component, context_builder, language)
            docstrings[component_id] = docstring
        
        return docstrings
from typing import Dict, List
from openai import OpenAI
from shared.prompts.markdown_prompts import build_markdown_prompt


class MarkdownGenerator:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", 
                 temperature: float = 0.3, max_tokens: int = 3000):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate_markdown(self, project_name: str, components: List[dict], 
                         docstrings: Dict[str, str]) -> str:
        """Generate markdown documentation using OpenAI."""
        try:
            prompt = build_markdown_prompt(project_name, components, docstrings)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical documentation writer specializing in creating clear, well-structured markdown documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            markdown = response.choices[0].message.content.strip()
            
            return markdown
            
        except Exception as e:
            print(f"Error generating markdown: {e}")
            return self._generate_fallback_markdown(project_name, components, docstrings)
    
    def _generate_fallback_markdown(self, project_name: str, 
                                   components: List[dict], 
                                   docstrings: Dict[str, str]) -> str:
        """Generate basic markdown if OpenAI fails."""
        from datetime import datetime
        
        md = f"# {project_name} Documentation\n\n"
        md += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"Total Components: {len(components)}\n\n"
        md += "---\n\n"
        
        # Group by file
        files = {}
        for comp in components:
            file_path = comp['file_path']
            if file_path not in files:
                files[file_path] = []
            files[file_path].append(comp)
        
        for file_path, comps in files.items():
            md += f"## Module: `{file_path}`\n\n"
            
            for comp in comps:
                md += f"### {comp['type'].title()}: `{comp['name']}`\n\n"
                md += f"**Signature:** `{comp['signature']}`\n\n"
                
                docstring = docstrings.get(comp['id'], 'No documentation available.')
                md += f"{docstring}\n\n"
                
                md += f"**Source:** `{file_path}:{comp['line_number']}`\n\n"
                md += "---\n\n"
        
        return md
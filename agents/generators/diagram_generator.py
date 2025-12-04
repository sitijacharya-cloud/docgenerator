from typing import Dict
from openai import OpenAI


class DiagramGenerator:
    """Generate Mermaid diagrams for code architecture."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_diagram(self, project_name: str, analysis: dict, language: str) -> str:
        """Generate a Mermaid diagram from code analysis."""
        try:
            from shared.prompts.diagram_prompts import build_diagram_prompt
            
            prompt = build_diagram_prompt(project_name, analysis, language)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating clear, informative Mermaid diagrams for software architecture."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            diagram = response.choices[0].message.content.strip()
            
            # Extract mermaid code if wrapped in markdown
            if '```mermaid' in diagram:
                start = diagram.find('```mermaid') + 10
                end = diagram.find('```', start)
                diagram = diagram[start:end].strip()
            elif '```' in diagram:
                diagram = diagram.replace('```', '').strip()
            
            return diagram
            
        except Exception as e:
            print(f"Error generating diagram: {e}")
            return self._generate_fallback_diagram(analysis)
    
    def _generate_fallback_diagram(self, analysis: dict) -> str:
        """Generate a simple fallback diagram."""
        diagram = "graph TD\n"
        
        classes = analysis.get('classes', [])
        for i, cls in enumerate(classes[:5]):  # Limit to 5 classes
            diagram += f"    Class{i}[{cls['name']}]\n"
        
        return diagram
from typing import Dict, List
import re


class BasicValidator:
    def validate_docstring(self, component: dict, docstring: str) -> Dict:
        """Validate a generated docstring."""
        issues = []
        warnings = []
        score = 1.0
        
        # Check if docstring is too short
        if len(docstring) < 50:
            issues.append("Docstring is too short (less than 50 characters)")
            score -= 0.3
        
        # Check if docstring is too long
        if len(docstring) > 2000:
            warnings.append("Docstring is very long (over 2000 characters)")
        
        # Check for required sections based on component type
        component_type = component['type']
        
        if component_type in ['function', 'method']:
            # Check for Args section if there are parameters
            if component['parameters']:
                if not re.search(r'Args?:', docstring, re.IGNORECASE):
                    issues.append("Missing 'Args:' section for parameters")
                    score -= 0.2
                
                # Check if all parameters are mentioned
                for param in component['parameters']:
                    param_name = param['name']
                    if param_name != 'self' and param_name not in docstring:
                        issues.append(f"Parameter '{param_name}' not documented")
                        score -= 0.1
            
            # Check for Returns section
            if component.get('return_type') and component['return_type'] != 'None':
                if not re.search(r'Returns?:', docstring, re.IGNORECASE):
                    warnings.append("Missing 'Returns:' section")
                    score -= 0.1
        
        # Check for example
        if not re.search(r'Example[s]?:', docstring, re.IGNORECASE):
            warnings.append("Consider adding usage examples")
            score -= 0.05
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return {
            'component_id': component['id'],
            'score': score,
            'issues': issues,
            'warnings': warnings
        }
    
    def validate_batch(self, components: List[dict], 
                      docstrings: Dict[str, str]) -> Dict:
        """Validate multiple docstrings."""
        results = []
        total_score = 0.0
        
        for component in components:
            component_id = component['id']
            docstring = docstrings.get(component_id, '')
            
            result = self.validate_docstring(component, docstring)
            results.append(result)
            total_score += result['score']
        
        overall_score = total_score / len(components) if components else 0.0
        
        return {
            'overall_score': overall_score,
            'component_scores': {r['component_id']: r for r in results}
        }
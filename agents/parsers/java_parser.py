import javalang
from typing import List, Dict
from pathlib import Path
from agents.parsers.base_parser import BaseParser


class JavaParser(BaseParser):
    """Parser for Java files."""
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse a Java source file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = javalang.parse.parse(source_code)
            
            return {
                'file_path': file_path,
                'module_name': Path(file_path).stem,
                'ast_tree': tree,
                'source_code': source_code,
                'module_docstring': None
            }
        except Exception as e:
            raise Exception(f"Failed to parse {file_path}: {str(e)}")
    
    def extract_components(self, parsed_data: Dict) -> List[Dict]:
        """Extract classes and methods from Java AST."""
        components = []
        tree = parsed_data['ast_tree']
        file_path = parsed_data['file_path']
        source_lines = parsed_data['source_code'].split('\n')
        
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            class_component = self._extract_class(node, file_path, source_lines)
            components.append(class_component)
            
            # Extract methods
            for method in node.methods:
                method_component = self._extract_method(method, node.name, file_path, source_lines)
                components.append(method_component)
        
        return components
    
    def _extract_class(self, node, file_path: str, source_lines: List[str]) -> Dict:
        """Extract class information."""
        return {
            'id': f"{Path(file_path).stem}.{node.name}",
            'type': 'class',
            'name': node.name,
            'file_path': file_path,
            'signature': f"class {node.name}",
            'parameters': [],
            'return_type': None,
            'decorators': [],
            'existing_docstring': node.documentation if hasattr(node, 'documentation') else None,
            'source_code': f"class {node.name} {{ ... }}",
            'line_number': node.position.line if hasattr(node, 'position') and node.position else 0
        }
    
    def _extract_method(self, node, class_name: str, file_path: str, source_lines: List[str]) -> Dict:
        """Extract method information."""
        params = []
        if node.parameters:
            for param in node.parameters:
                params.append({
                    'name': param.name,
                    'type_hint': param.type.name if hasattr(param.type, 'name') else str(param.type),
                    'default': None
                })
        
        return_type = node.return_type.name if node.return_type and hasattr(node.return_type, 'name') else 'void'
        
        return {
            'id': f"{Path(file_path).stem}.{class_name}.{node.name}",
            'type': 'method',
            'name': node.name,
            'file_path': file_path,
            'signature': f"{return_type} {node.name}(...)",
            'parameters': params,
            'return_type': return_type,
            'decorators': [],
            'existing_docstring': node.documentation if hasattr(node, 'documentation') else None,
            'source_code': f"// Method: {node.name}",
            'line_number': node.position.line if hasattr(node, 'position') and node.position else 0
        }
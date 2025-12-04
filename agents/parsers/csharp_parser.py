import re
from typing import List, Dict
from pathlib import Path
from agents.parsers.base_parser import BaseParser


class CSharpParser(BaseParser):
    """Simple regex-based parser for C# files."""
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse a C# source file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return {
                'file_path': file_path,
                'module_name': Path(file_path).stem,
                'ast_tree': None,
                'source_code': source_code,
                'module_docstring': None
            }
        except Exception as e:
            raise Exception(f"Failed to parse {file_path}: {str(e)}")
    
    def extract_components(self, parsed_data: Dict) -> List[Dict]:
        """Extract classes and methods using regex."""
        components = []
        source_code = parsed_data['source_code']
        file_path = parsed_data['file_path']
        source_lines = source_code.split('\n')
        
        # Find classes
        class_pattern = r'(public|private|protected|internal)?\s*class\s+(\w+)'
        for match in re.finditer(class_pattern, source_code):
            class_name = match.group(2)
            line_num = source_code[:match.start()].count('\n') + 1
            
            components.append({
                'id': f"{Path(file_path).stem}.{class_name}",
                'type': 'class',
                'name': class_name,
                'file_path': file_path,
                'signature': f"class {class_name}",
                'parameters': [],
                'return_type': None,
                'decorators': [],
                'existing_docstring': None,
                'source_code': f"class {class_name} {{ }}",
                'line_number': line_num
            })
        
        # Find methods
        method_pattern = r'(public|private|protected|internal)?\s*(\w+)\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, source_code):
            return_type = match.group(2)
            method_name = match.group(3)
            line_num = source_code[:match.start()].count('\n') + 1
            
            if method_name not in ['if', 'for', 'while', 'switch']:  # Filter keywords
                components.append({
                    'id': f"{Path(file_path).stem}.{method_name}",
                    'type': 'method',
                    'name': method_name,
                    'file_path': file_path,
                    'signature': f"{return_type} {method_name}(...)",
                    'parameters': [],
                    'return_type': return_type,
                    'decorators': [],
                    'existing_docstring': None,
                    'source_code': f"// Method: {method_name}",
                    'line_number': line_num
                })
        
        return components
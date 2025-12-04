import ast
from typing import List, Dict, Optional
from pathlib import Path
from .base_parser import BaseParser


class PythonParser(BaseParser):
    def parse_file(self, file_path: str) -> Dict:
        """Parse a Python source file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            module_docstring = ast.get_docstring(tree)
            
            return {
                'file_path': file_path,
                'module_name': Path(file_path).stem,
                'ast_tree': tree,
                'source_code': source_code,
                'module_docstring': module_docstring
            }
        except Exception as e:
            raise Exception(f"Failed to parse {file_path}: {str(e)}")
    
    def extract_components(self, parsed_data: Dict) -> List[Dict]:
        """Extract functions, classes, and methods from AST."""
        components = []
        tree = parsed_data['ast_tree']
        file_path = parsed_data['file_path']
        source_lines = parsed_data['source_code'].split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's a method (inside a class)
                is_method = any(isinstance(parent, ast.ClassDef) 
                               for parent in ast.walk(tree) 
                               if node in ast.walk(parent))
                
                if not is_method:
                    component = self._extract_function(node, file_path, source_lines)
                    components.append(component)
            
            elif isinstance(node, ast.ClassDef):
                # Extract class
                class_component = self._extract_class(node, file_path, source_lines)
                components.append(class_component)
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_component = self._extract_method(
                            item, node.name, file_path, source_lines
                        )
                        components.append(method_component)
        
        return components
    
    def _extract_function(self, node: ast.FunctionDef, file_path: str, 
                         source_lines: List[str]) -> Dict:
        """Extract function information."""
        return {
            'id': f"{Path(file_path).stem}.{node.name}",
            'type': 'function',
            'name': node.name,
            'file_path': file_path,
            'signature': self._get_signature(node),
            'parameters': self._get_parameters(node),
            'return_type': self._get_return_type(node),
            'decorators': self._get_decorators(node),
            'existing_docstring': ast.get_docstring(node),
            'source_code': self._get_source_code(node, source_lines),
            'line_number': node.lineno
        }
    
    def _extract_class(self, node: ast.ClassDef, file_path: str, 
                      source_lines: List[str]) -> Dict:
        """Extract class information."""
        return {
            'id': f"{Path(file_path).stem}.{node.name}",
            'type': 'class',
            'name': node.name,
            'file_path': file_path,
            'signature': f"class {node.name}:",
            'parameters': [],
            'return_type': None,
            'decorators': self._get_decorators(node),
            'existing_docstring': ast.get_docstring(node),
            'source_code': self._get_source_code(node, source_lines),
            'line_number': node.lineno
        }
    
    def _extract_method(self, node: ast.FunctionDef, class_name: str, 
                       file_path: str, source_lines: List[str]) -> Dict:
        """Extract method information."""
        return {
            'id': f"{Path(file_path).stem}.{class_name}.{node.name}",
            'type': 'method',
            'name': node.name,
            'file_path': file_path,
            'signature': self._get_signature(node),
            'parameters': self._get_parameters(node),
            'return_type': self._get_return_type(node),
            'decorators': self._get_decorators(node),
            'existing_docstring': ast.get_docstring(node),
            'source_code': self._get_source_code(node, source_lines),
            'line_number': node.lineno
        }
    
    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Get function/method signature."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Handle defaults
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for i, default in enumerate(defaults):
            if default is not None:
                args[i] += f" = {ast.unparse(default)}"
        
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {ast.unparse(node.returns)}"
        
        return f"def {node.name}({', '.join(args)}){return_annotation}:"
    
    def _get_parameters(self, node: ast.FunctionDef) -> List[Dict]:
        """Extract parameter information."""
        params = []
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        
        for arg, default in zip(node.args.args, defaults):
            param = {
                'name': arg.arg,
                'type_hint': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': ast.unparse(default) if default else None
            }
            params.append(param)
        
        return params
    
    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation."""
        if node.returns:
            return ast.unparse(node.returns)
        return None
    
    def _get_decorators(self, node) -> List[str]:
        """Get decorator names."""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(f"@{decorator.id}")
            elif isinstance(decorator, ast.Call):
                decorators.append(f"@{ast.unparse(decorator)}")
            else:
                decorators.append(f"@{ast.unparse(decorator)}")
        return decorators
    
    def _get_source_code(self, node, source_lines: List[str]) -> str:
        """Extract source code for a node."""
        try:
            return ast.unparse(node)
        except:
            # Fallback to line-based extraction
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, 'end_lineno') else start + 1
            return '\n'.join(source_lines[start:end])
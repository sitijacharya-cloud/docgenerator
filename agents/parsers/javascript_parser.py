import esprima
from typing import List, Dict
from pathlib import Path
from agents.parsers.base_parser import BaseParser


class JavaScriptParser(BaseParser):
    """Parser for JavaScript/TypeScript files."""
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse a JavaScript source file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse with esprima
            try:
                tree = esprima.parseScript(source_code, {'loc': True, 'comment': True})
            except:
                tree = esprima.parseModule(source_code, {'loc': True, 'comment': True})
            
            return {
                'file_path': file_path,
                'module_name': Path(file_path).stem,
                'ast_tree': tree,
                'source_code': source_code,
                'module_docstring': self._extract_module_doc(tree)
            }
        except Exception as e:
            raise Exception(f"Failed to parse {file_path}: {str(e)}")
    
    def extract_components(self, parsed_data: Dict) -> List[Dict]:
        """Extract functions and classes from JavaScript AST."""
        components = []
        tree = parsed_data['ast_tree']
        file_path = parsed_data['file_path']
        source_lines = parsed_data['source_code'].split('\n')
        
        for node in self._walk_ast(tree):
            if node.type == 'FunctionDeclaration':
                component = self._extract_function(node, file_path, source_lines)
                components.append(component)
            
            elif node.type == 'ClassDeclaration':
                class_component = self._extract_class(node, file_path, source_lines)
                components.append(class_component)
                
                # Extract methods
                if hasattr(node, 'body') and hasattr(node.body, 'body'):
                    for item in node.body.body:
                        if item.type == 'MethodDefinition':
                            method = self._extract_method(item, node.id.name, file_path, source_lines)
                            components.append(method)
        
        return components
    
    def _walk_ast(self, node):
        """Walk JavaScript AST recursively."""
        yield node
        
        for key in dir(node):
            if key.startswith('_'):
                continue
            
            value = getattr(node, key)
            
            if hasattr(value, 'type'):
                yield from self._walk_ast(value)
            elif isinstance(value, list):
                for item in value:
                    if hasattr(item, 'type'):
                        yield from self._walk_ast(item)
    
    def _extract_function(self, node, file_path: str, source_lines: List[str]) -> Dict:
        """Extract function information."""
        params = []
        if hasattr(node, 'params'):
            for param in node.params:
                params.append({
                    'name': getattr(param, 'name', 'param'),
                    'type_hint': None,
                    'default': None
                })
        
        name = node.id.name if hasattr(node, 'id') and node.id else 'anonymous'
        
        return {
            'id': f"{Path(file_path).stem}.{name}",
            'type': 'function',
            'name': name,
            'file_path': file_path,
            'signature': f"function {name}(...)",
            'parameters': params,
            'return_type': None,
            'decorators': [],
            'existing_docstring': self._extract_jsdoc(node),
            'source_code': self._get_source(node, source_lines),
            'line_number': node.loc.start.line if hasattr(node, 'loc') else 0
        }
    
    def _extract_class(self, node, file_path: str, source_lines: List[str]) -> Dict:
        """Extract class information."""
        name = node.id.name if hasattr(node, 'id') and node.id else 'AnonymousClass'
        
        return {
            'id': f"{Path(file_path).stem}.{name}",
            'type': 'class',
            'name': name,
            'file_path': file_path,
            'signature': f"class {name}",
            'parameters': [],
            'return_type': None,
            'decorators': [],
            'existing_docstring': self._extract_jsdoc(node),
            'source_code': self._get_source(node, source_lines),
            'line_number': node.loc.start.line if hasattr(node, 'loc') else 0
        }
    
    def _extract_method(self, node, class_name: str, file_path: str, source_lines: List[str]) -> Dict:
        """Extract method information."""
        name = node.key.name if hasattr(node.key, 'name') else 'method'
        
        params = []
        if hasattr(node.value, 'params'):
            for param in node.value.params:
                params.append({
                    'name': getattr(param, 'name', 'param'),
                    'type_hint': None,
                    'default': None
                })
        
        return {
            'id': f"{Path(file_path).stem}.{class_name}.{name}",
            'type': 'method',
            'name': name,
            'file_path': file_path,
            'signature': f"{name}(...)",
            'parameters': params,
            'return_type': None,
            'decorators': [],
            'existing_docstring': self._extract_jsdoc(node),
            'source_code': self._get_source(node, source_lines),
            'line_number': node.loc.start.line if hasattr(node, 'loc') else 0
        }
    
    def _extract_jsdoc(self, node) -> str:
        """Extract JSDoc comment if present."""
        # Simplified - just return None for now
        return None
    
    def _extract_module_doc(self, tree) -> str:
        """Extract module-level documentation."""
        return None
    
    def _get_source(self, node, source_lines: List[str]) -> str:
        """Get source code for a node."""
        if hasattr(node, 'loc'):
            start = node.loc.start.line - 1
            end = node.loc.end.line
            return '\n'.join(source_lines[start:end])
        return "// Source code unavailable"
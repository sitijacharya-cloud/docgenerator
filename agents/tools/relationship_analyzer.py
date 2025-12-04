from typing import List, Dict, Set


class RelationshipAnalyzer:
    """Analyze relationships between code components."""
    
    def analyze_relationships(self, components: List[Dict]) -> Dict:
        """Analyze relationships between components."""
        
        classes = [c for c in components if c['type'] == 'class']
        functions = [c for c in components if c['type'] == 'function']
        methods = [c for c in components if c['type'] == 'method']
        
        # Build class hierarchy
        class_hierarchy = self._build_class_hierarchy(components)
        
        # Find dependencies
        dependencies = self._find_dependencies(components)
        
        return {
            'classes': classes,
            'functions': functions,
            'methods': methods,
            'class_hierarchy': class_hierarchy,
            'dependencies': dependencies,
            'total_components': len(components)
        }
    
    def _build_class_hierarchy(self, components: List[Dict]) -> Dict:
        """Build class hierarchy from components."""
        hierarchy = {}
        
        for comp in components:
            if comp['type'] == 'class':
                class_name = comp['name']
                hierarchy[class_name] = {
                    'methods': [],
                    'file': comp['file_path']
                }
        
        # Add methods to classes
        for comp in components:
            if comp['type'] == 'method':
                # Extract class name from component ID
                parts = comp['id'].split('.')
                if len(parts) >= 2:
                    class_name = parts[-2]
                    if class_name in hierarchy:
                        hierarchy[class_name]['methods'].append(comp['name'])
        
        return hierarchy
    
    def _find_dependencies(self, components: List[Dict]) -> List[Dict]:
        """Find dependencies between components (simplified)."""
        dependencies = []
        
        # Simple heuristic: look for class names in function/method source code
        class_names = {c['name'] for c in components if c['type'] == 'class'}
        
        for comp in components:
            if comp['type'] in ['function', 'method']:
                source = comp.get('source_code', '')
                found_deps = []
                
                for class_name in class_names:
                    if class_name in source and class_name != comp['name']:
                        found_deps.append(class_name)
                
                if found_deps:
                    dependencies.append({
                        'from': comp['name'],
                        'to': found_deps,
                        'type': 'uses'
                    })
        
        return dependencies
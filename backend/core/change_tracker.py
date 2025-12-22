import difflib
from typing import Dict, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class CodeChangeTracker:
    """Detect and track code changes between versions"""
    
    def __init__(self):
        self.changes = {
            "additions": [],
            "deletions": [],
            "modifications": [],
            "summary": ""
        }
    
    def compare_code(self, old_code: str, new_code: str) -> Dict:
        """
        Compare old and new code, detect changes.
        
        Returns:
            Dict with additions, deletions, modifications
        """
        logger.info(f"Comparing code - Old: {len(old_code)} chars, New: {len(new_code)} chars")
        
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        # Get unified diff
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        logger.info(f"Diff lines: {len(diff)}")
        
        # Extract functions/classes from both versions
        old_items = self._extract_code_items(old_code)
        new_items = self._extract_code_items(new_code)
        old_items.update(self._extract_class_methods(old_code))
        new_items.update(self._extract_class_methods(new_code))
        
        logger.info(f"Old items found: {list(old_items.keys())}")
        logger.info(f"New items found: {list(new_items.keys())}")
        
        # Detect changes
        additions = self._find_additions(old_items, new_items)
        deletions = self._find_deletions(old_items, new_items)
        modifications = []
        
        logger.info(f"Additions: {len(additions)}, Deletions: {len(deletions)}, Modifications: {len(modifications)}")
        
        self.changes = {
            "additions": additions,
            "deletions": deletions,
            "modifications": [],
            "diff_lines": len([l for l in diff if l.startswith('+') or l.startswith('-')]),
            "summary": self._generate_summary(additions, deletions, modifications)
        }
        
        logger.info(f"Change summary: {self.changes['summary']}")
        
        return self.changes
    
    def _extract_code_items(self, code: str) -> Dict[str, str]:
        """Extract functions and classes with their signatures"""
        items = {}
        
        # Python functions - more comprehensive pattern
        python_funcs = re.finditer(r'^\s*(def\s+(\w+)\s*\([^)]*\).*?):', code, re.MULTILINE)
        for match in python_funcs:
            name = match.group(2)
            signature = match.group(1).strip()
            items[f"function:{name}"] = signature
            logger.debug(f"Found Python function: {name}")
        
        # JavaScript/TypeScript functions
        js_funcs = re.finditer(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function|\s+(\w+)\s*\([^)]*\)\s*(?:=>|{))', code)
        for match in js_funcs:
            name = match.group(1) or match.group(2) or match.group(3)
            if name:
                items[f"function:{name}"] = match.group(0)
                logger.debug(f"Found JS function: {name}")
        
        # Java/C# methods
        java_methods = re.finditer(r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)', code)
        for match in java_methods:
            name = match.group(1)
            if name not in ['if', 'for', 'while', 'switch', 'catch']:  # Skip keywords
                items[f"function:{name}"] = match.group(0)
                logger.debug(f"Found Java/C# method: {name}")
        
        # Classes - universal pattern
        # Classes - universal pattern with inheritance
        class_matches = re.finditer(r'^\s*(class\s+(\w+)(?:\([^)]*\))?)', code, re.MULTILINE)
        for match in class_matches:
            name = match.group(2)
            signature = match.group(1).strip()
            items[f"class:{name}"] = signature
            logger.debug(f"Found class: {name}")
        
        logger.info(f"Total items extracted: {len(items)}")
        return items
    
    def _normalize_signature(self, sig: str) -> str:
        """Normalize function signature for better comparison"""
        sig = ' '.join(sig.split())
        sig = sig.replace(' (', '(').replace(' )', ')')
        sig = sig.replace(' ,', ',').replace(', ', ',')
        sig = sig.replace(' :', ':').replace(': ', ':')
        sig = sig.replace(' ->', '->')
        sig = sig.replace('(self,', '(').replace('(self)', '()')
        sig = sig.replace('(cls,', '(').replace('(cls)', '()')
        return sig.strip()
    
    def _extract_params(self, signature: str) -> set:
        """Extract parameter names from signature for comparison"""
        match = re.search(r'\((.*?)\)', signature)
        if not match:
            return set()
        
        params_str = match.group(1)
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param or param == 'self' or param == 'cls':
                continue
            param_name = re.split(r'[:\=]', param)[0].strip()
            if param_name:
                params.append(param_name)
        
        return set(params)
    def _extract_class_methods(self, code: str) -> Dict[str, str]:
        """Extract methods within classes"""
        methods = {}
        lines = code.split('\n')
        current_class = None
        indent_level = 0
        
        for i, line in enumerate(lines):
            # Detect class start
            class_match = re.match(r'^(\s*)class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(2)
                indent_level = len(class_match.group(1))
                continue
            
            # Detect methods inside class
            if current_class:
                method_match = re.match(r'^(\s+)def\s+(\w+)\s*\([^)]*\)', line)
                if method_match:
                    method_indent = len(method_match.group(1))
                    # Check if it's a direct method of current class
                    if method_indent > indent_level:
                        method_name = method_match.group(2)
                        methods[f"method:{current_class}.{method_name}"] = line.strip()
                # Exit class when indentation returns to class level or less
                elif line.strip() and not line[indent_level:].startswith(' ') and indent_level > 0:
                    current_class = None
        
        return methods

    def _normalize_class_signature(self, sig: str) -> str:
        """Normalize class signature including inheritance"""
        sig = ' '.join(sig.split())
        sig = sig.replace(' (', '(').replace(' )', ')')
        sig = sig.replace(' ,', ',')
        return sig.strip()
    def _find_additions(self, old_items: Dict, new_items: Dict) -> List[Dict]:
        """Find newly added functions/classes"""
        additions = []
        for key, value in new_items.items():
            if key not in old_items:
                item_type, name = key.split(":", 1)
                additions.append({
                    "type": item_type,
                    "name": name,
                    "signature": value
                })
                logger.info(f"Addition detected: {item_type} '{name}'")
        return additions
    
    def _find_deletions(self, old_items: Dict, new_items: Dict) -> List[Dict]:
        """Find deleted functions/classes"""
        deletions = []
        for key, value in old_items.items():
            if key not in new_items:
                item_type, name = key.split(":", 1)
                deletions.append({
                    "type": item_type,
                    "name": name,
                    "signature": value
                })
                logger.info(f"Deletion detected: {item_type} '{name}'")
        return deletions
    
    def _find_modifications(self, old_items: Dict, new_items: Dict) -> List[Dict]:
        """Find modified functions/classes"""
        modifications = []
        for key in old_items:
            if key in new_items:
                old_sig = self._normalize_signature(old_items[key])
                new_sig = self._normalize_signature(new_items[key])
                
                # Extract type and name
                item_type, name = key.split(":", 1)
                
                # Skip __init__ if parameters are essentially the same
                if name == '__init__':
                    old_params = self._extract_params(old_sig)
                    new_params = self._extract_params(new_sig)
                    if old_params == new_params:
                        continue
                elif item_type == 'class':
                    old_sig = self._normalize_class_signature(old_items[key])
                    new_sig = self._normalize_class_signature(new_items[key])
                # Compare normalized signatures
                if old_sig != new_sig:
                    modifications.append({
                        "type": item_type,
                        "name": name,
                        "old_signature": old_items[key],
                        "new_signature": new_items[key]
                    })
                    logger.info(f"Modification detected: {item_type} '{name}'")
        return modifications
    
    def _generate_summary(self, additions: List, deletions: List, modifications: List) -> str:
        """Generate human-readable summary"""
        parts = []
        if additions:
            parts.append(f"{len(additions)} addition(s)")
        if deletions:
            parts.append(f"{len(deletions)} deletion(s)")
        if modifications:
            parts.append(f"{len(modifications)} modification(s)")
        
        if not parts:
            return "No changes detected"
        
        return ", ".join(parts)
    
    def format_changes_markdown(self) -> str:
        """Format changes as markdown"""
        md = "## 🔄 Code Changes Detected\n\n"
        md += f"**Summary:** {self.changes['summary']}\n\n"
        
        if self.changes['additions']:
            md += "### ✅ Additions\n"
            for item in self.changes['additions']:
                md += f"- **{item['type'].title()}**: `{item['name']}`\n"
            md += "\n"
        
        if self.changes['deletions']:
            md += "### ❌ Deletions\n"
            for item in self.changes['deletions']:
                md += f"- **{item['type'].title()}**: `{item['name']}`\n"
            md += "\n"
        
        
        return md
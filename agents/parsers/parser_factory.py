from typing import Dict, Type
from agents.parsers.base_parser import BaseParser
from agents.parsers.python_parser import PythonParser
from agents.parsers.javascript_parser import JavaScriptParser
from agents.parsers.java_parser import JavaParser
from agents.parsers.csharp_parser import CSharpParser


class ParserFactory:
    """Factory to create language-specific parsers."""
    
    _parsers: Dict[str, Type[BaseParser]] = {
        'python': PythonParser,
        'javascript': JavaScriptParser,
        'java': JavaParser,
        'csharp': CSharpParser,
    }
    
    @classmethod
    def get_parser(cls, language: str) -> BaseParser:
        """Get parser for specified language."""
        language = language.lower()
        
        if language not in cls._parsers:
            raise ValueError(f"Unsupported language: {language}. Supported: {list(cls._parsers.keys())}")
        
        return cls._parsers[language]()
    
    @classmethod
    def detect_language(cls, file_path: str) -> str:
        """Detect language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.cs': 'csharp',
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'python'  # Default fallback
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported languages."""
        return list(cls._parsers.keys())
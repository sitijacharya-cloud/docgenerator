import io
from pathlib import Path
from typing import Union, Tuple


class CodeLoader:
    """Load and extract source code from various file types."""
    
    # Supported languages and their extensions
    LANGUAGE_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.hpp': 'C++',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'MATLAB',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.vue': 'Vue',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.pl': 'Perl',
    }
    
    @staticmethod
    def detect_language(file_path: Union[str, Path]) -> str:
        """Detect programming language from file extension."""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        return CodeLoader.LANGUAGE_EXTENSIONS.get(ext, 'Unknown')
    
    @staticmethod
    def load_code(file_path: Union[str, Path]) -> Tuple[str, str]:
        """
        Load source code from a file path.
        
        Args:
            file_path: Path to the source code file
        
        Returns:
            Tuple of (code_content, language)
        
        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        language = CodeLoader.detect_language(file_path)
        
        if language == 'Unknown':
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                code_content = f.read()
        
        return code_content, language
    
    @staticmethod
    def load_from_uploaded_file(uploaded_file) -> Tuple[str, str]:
        """
        Load source code from uploaded file object.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
        
        Returns:
            Tuple of (code_content, language)
        """
        file_name = uploaded_file.name.lower()
        
        # Detect language
        ext = '.' + file_name.rsplit('.', 1)[-1] if '.' in file_name else ''
        language = CodeLoader.LANGUAGE_EXTENSIONS.get(ext, 'Unknown')
        
        if language == 'Unknown':
            raise ValueError(f"Unsupported file format: {file_name}")
        
        # Read file content
        file_bytes = uploaded_file.read()
        
        try:
            code_content = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            code_content = file_bytes.decode('latin-1')
        
        return code_content, language
    
    @staticmethod
    def get_code_stats(code_content: str) -> dict:
        """Get statistics about the code."""
        lines = code_content.split('\n')
        
        # Count non-empty and non-comment lines (basic heuristic)
        non_empty_lines = [line for line in lines if line.strip()]
        comment_lines = [line for line in lines if line.strip().startswith(('#', '//', '/*', '*', '<!--'))]
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "comment_lines": len(comment_lines),
            "code_lines": len(non_empty_lines) - len(comment_lines),
            "char_count": len(code_content),
            "word_count": len(code_content.split()),
        }
    
    @staticmethod
    def is_supported_language(file_name: str) -> bool:
        """Check if a file is a supported code file."""
        ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        return ext in CodeLoader.LANGUAGE_EXTENSIONS
    
    @staticmethod
    def get_supported_extensions() -> list:
        """Get list of all supported file extensions."""
        return list(CodeLoader.LANGUAGE_EXTENSIONS.keys())
    
    @staticmethod
    def get_supported_languages() -> list:
        """Get list of all supported programming languages."""
        return list(set(CodeLoader.LANGUAGE_EXTENSIONS.values()))
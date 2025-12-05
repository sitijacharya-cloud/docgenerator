import os

from typing import List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.graph.state import DocumentationState
from agents.parsers.python_parser import PythonParser
from agents.generators.docstring_generator import DocstringGenerator
from agents.generators.markdown_generator import MarkdownGenerator
from agents.validators.basic_validator import BasicValidator
from agents.memory.chroma_manager import ChromaManager
from agents.memory.context_builder import ContextBuilder
from backend.app.config import get_settings
from agents.tools.relationship_analyzer import RelationshipAnalyzer
from agents.generators.diagram_generator import DiagramGenerator
from agents.generators.pdf_generator import PDFGenerator

_settings = None
_parser = None
_chroma_manager = None
_context_builder = None
_docstring_generator = None
_markdown_generator = None
_validator = None
_relationship_analyzer = None
_diagram_generator = None
_pdf_generator = None



def get_components():
    """Lazy initialization of components."""
   
    global _settings, _parser, _chroma_manager, _context_builder
    global _docstring_generator, _markdown_generator, _validator
    global _relationship_analyzer, _diagram_generator, _pdf_generator
    
    if _settings is None:
        _settings = get_settings()
    
    if _parser is None:
        _parser = PythonParser()
    
    if _chroma_manager is None:
        _chroma_manager = ChromaManager(_settings.chroma_persist_dir)
    
    if _context_builder is None:
        _context_builder = ContextBuilder(_chroma_manager)
    
    if _docstring_generator is None:
        _docstring_generator = DocstringGenerator(
            api_key=_settings.openai_api_key,
            model=_settings.openai_model,
            temperature=_settings.openai_temperature,
            max_tokens=_settings.max_tokens
        )
    
    if _markdown_generator is None:
        _markdown_generator = MarkdownGenerator(
            api_key=_settings.openai_api_key,
            model=_settings.openai_model,
            temperature=_settings.openai_temperature,
            max_tokens=3000
        )
    
    if _validator is None:
        _validator = BasicValidator()
    
    if _relationship_analyzer is None:
        _relationship_analyzer = RelationshipAnalyzer()
    
    if _diagram_generator is None:
        _diagram_generator = DiagramGenerator(
            api_key=_settings.openai_api_key,
            model=_settings.openai_model
        )
    
    if _pdf_generator is None:
        from agents.generators.pdf_generator import PDFGenerator
        _pdf_generator = PDFGenerator()
    
    
    return {
        'parser': _parser,
        'chroma_manager': _chroma_manager,
        'context_builder': _context_builder,
        'docstring_generator': _docstring_generator,
        'markdown_generator': _markdown_generator,
        'validator': _validator,
        'settings': _settings,
        'relationship_analyzer': _relationship_analyzer,
        'diagram_generator': _diagram_generator,
        'pdf_generator': _pdf_generator
    }


def parse_code_node(state: DocumentationState) -> DocumentationState:
    """Parse source code files."""
    print("🔍 Parsing code...")
    
    try:
        code_path = state['code_path']
        language = state.get('language', 'python')
        parsed_files = []
        
        # Check if path exists
        if not os.path.exists(code_path):
            return {
                **state,
                'status': 'failed',
                'errors': state.get('errors', []) + [f"Path not found: {code_path}"]
            }
        
        # Import parser factory HERE
        from agents.parsers.parser_factory import ParserFactory
        
        # Collect files based on language
        source_files = []
        if os.path.isfile(code_path):
            source_files.append(code_path)
        else:
            # Get appropriate file extensions
            extensions = {
                'python': ['.py'],
                'javascript': ['.js', '.jsx', '.ts', '.tsx'],
                'java': ['.java'],
                'csharp': ['.cs']
            }
            
            valid_exts = extensions.get(language, ['.py'])
            
            for root, dirs, files in os.walk(code_path):
                for file in files:
                    if any(file.endswith(ext) for ext in valid_exts):
                        source_files.append(os.path.join(root, file))
        
        if not source_files:
            return {
                **state,
                'status': 'failed',
                'errors': state.get('errors', []) + [f"No {language} files found"]
            }
        
        # Get appropriate parser
        parser = ParserFactory.get_parser(language)
        
        # Parse each file
        for file_path in source_files:
            try:
                parsed = parser.parse_file(file_path)
                parsed_files.append(parsed)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
        
        if not parsed_files:
            return {
                **state,
                'status': 'failed',
                'errors': state.get('errors', []) + ["Failed to parse any files"]
            }
        
        print(f"✅ Parsed {len(parsed_files)} {language} files")
        
        return {
            **state,
            'parsed_files': parsed_files,
            'status': 'parsing_complete'
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Parse error: {str(e)}"]
        }

def extract_components_node(state: DocumentationState) -> DocumentationState:
    """Extract code components from parsed files."""
    print("📦 Extracting components...")
    
    try:
        parsed_files = state['parsed_files']
        language = state.get('language', 'python')
        all_components = []
        
        # Import parser factory HERE
        from agents.parsers.parser_factory import ParserFactory
        parser = ParserFactory.get_parser(language)
        
        for parsed_file in parsed_files:
            components = parser.extract_components(parsed_file)
            all_components.extend(components)
        
        if not all_components:
            return {
                **state,
                'status': 'failed',
                'errors': state.get('errors', []) + ["No components found"]
            }
        
        print(f"✅ Extracted {len(all_components)} components")
        
        return {
            **state,
            'code_components': all_components,
            'status': 'extraction_complete'
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Extraction error: {str(e)}"]
        }

def generate_docstrings_node(state: DocumentationState) -> DocumentationState:
    """Generate docstrings using OpenAI."""
    print("✨ Generating docstrings...")
    
    try:
        components = get_components()
        code_components = state['code_components']
        language = state.get('language', 'python')
        
        docstring_generator = components['docstring_generator']
        context_builder = components['context_builder']
        chroma_manager = components['chroma_manager']
        
        # Generate docstrings with language
        docstrings = docstring_generator.generate_batch(code_components, context_builder, language)
        
        # Store in ChromaDB for future context
        for component in code_components:
            component_id = component['id']
            if component_id in docstrings:
                chroma_manager.add_documented_component(
                    component_id=component_id,
                    source_code=component['source_code'],
                    docstring=docstrings[component_id],
                    metadata={
                        'type': component['type'],
                        'language': language,
                        'file_path': component['file_path']
                    }
                )
        
        print(f"✅ Generated {len(docstrings)} docstrings")
        
        return {
            **state,
            'generated_docstrings': docstrings,
            'status': 'docstring_generation_complete'
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Docstring generation error: {str(e)}"]
        }

def validate_docstrings_node(state: DocumentationState) -> DocumentationState:
    """Validate generated docstrings."""
    print("✔️  Validating docstrings...")
    components = get_components()
    validator = components['validator']
    
    try:
        components = state['code_components']
        docstrings = state['generated_docstrings']
        
        validation_results = validator.validate_batch(components, docstrings)
        
        print(f"✅ Validation complete. Overall score: {validation_results['overall_score']:.2f}")
        
        return {
            **state,
            'validation_results': validation_results,
            'status': 'validation_complete'
        }
        
    except Exception as e:
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Validation error: {str(e)}"]
        }

def generate_markdown_node(state: DocumentationState) -> DocumentationState:
    """Generate markdown documentation."""
    print("📝 Generating markdown documentation...")
    
    try:
        components = get_components()
        markdown_generator = components['markdown_generator']
        
        project_name = state['project_name']
        code_components = state['code_components']
        docstrings = state['generated_docstrings']
        
        markdown_content = markdown_generator.generate_markdown(
            project_name, code_components, docstrings
        )
        
        # Add diagram if available
        mermaid_diagram = state.get('mermaid_diagram')
        if mermaid_diagram:
            # For markdown, include mermaid syntax
            diagram_section = f"\n\n## Architecture Diagram\n\n```mermaid\n{mermaid_diagram}\n```\n\n"
            # Insert after title
            lines = markdown_content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    insert_index = i + 1
                    break
            
            lines.insert(insert_index, diagram_section)
            markdown_content = '\n'.join(lines)
                
        print("✅ Markdown generation complete")
        
        return {
            **state,
            'markdown_content': markdown_content,
            'status': 'markdown_generation_complete'
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Markdown generation error: {str(e)}"]
        }

def save_output_node(state: DocumentationState) -> DocumentationState:
    """Save generated documentation to file."""
    print("💾 Saving output...")
    components = get_components()
    settings = components['settings']
    try:
        markdown_content = state['markdown_content']
        project_name = state['project_name']
        
        # Create output directory
        output_dir = Path(settings.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{project_name}_{timestamp}.md"
        output_path = output_dir / filename
        
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Documentation saved to: {output_path}")
        
        return {
            **state,
            'output_path': str(output_path),
            'status': 'completed'
        }
        
    except Exception as e:
        return {
            **state,
            'status': 'failed',
            'errors': state.get('errors', []) + [f"Save error: {str(e)}"]
        }
    

def analyze_relationships_node(state: DocumentationState) -> DocumentationState:
    """Analyze relationships between code components."""
    print("🔍 Analyzing relationships...")
    
    try:
        components = get_components()
        analyzer = components['relationship_analyzer']
        
        code_components = state['code_components']
        
        analysis = analyzer.analyze_relationships(code_components)
        
        print(f"✅ Found {len(analysis['classes'])} classes, {len(analysis['functions'])} functions")
        
        return {
            **state,
            'relationship_analysis': analysis,
            'status': 'analysis_complete'
        }
        
    except Exception as e:
        print(f"Warning: Relationship analysis failed: {e}")
        return {
            **state,
            'relationship_analysis': {},
            'status': 'analysis_skipped'
        }


def generate_diagram_node(state: DocumentationState) -> DocumentationState:
    """Generate Mermaid diagram."""
    print("📊 Generating diagram...")
    
    try:
        components = get_components()
        diagram_generator = components['diagram_generator']
        
        project_name = state['project_name']
        language = state.get('language', 'python')
        analysis = state.get('relationship_analysis', {})
        
        if not analysis or not analysis.get('classes'):
            print("⏭️  Skipping diagram - no classes found")
            return {
                **state,
                'mermaid_diagram': None,
                'status': 'diagram_skipped'
            }
        
        diagram = diagram_generator.generate_diagram(project_name, analysis, language)
        
        print("✅ Diagram generated")
        
        return {
            **state,
            'mermaid_diagram': diagram,
            'status': 'diagram_generation_complete'
        }
        
    except Exception as e:
        print(f"Warning: Diagram generation failed: {e}")
        return {
            **state,
            'mermaid_diagram': None,
            'status': 'diagram_failed'
        }


def generate_pdf_node(state: DocumentationState) -> DocumentationState:
    """Generate PDF from markdown."""
    print("📄 Generating PDF...")
    
    try:
        components = get_components()
        pdf_generator = components['pdf_generator']
        settings = components['settings']
        
        markdown_content = state['markdown_content']
        project_name = state['project_name']
        
        # Create output path
        from datetime import datetime
        from pathlib import Path
        
        output_dir = Path(settings.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"{project_name}_{timestamp}.pdf"
        pdf_path = output_dir / pdf_filename
        
        # Generate PDF
        pdf_generator.generate_pdf(markdown_content, str(pdf_path))
        
        print(f"✅ PDF saved to: {pdf_path}")
        
        return {
            **state,
            'pdf_path': str(pdf_path),
            'status': 'pdf_generation_complete'
        }
        
    except Exception as e:
        print(f"Warning: PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            'pdf_path': None,
            'status': 'pdf_failed'
        }
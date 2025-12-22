from typing import TypedDict, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import concurrent.futures
import json
import os
from backend.core.change_tracker import CodeChangeTracker


class SupervisorState(TypedDict):
    """State for code documentation workflow with HITL and memory"""
    # Input
    code_content: str
    language: str
    project_name: str
    
    # Outputs from workers
    code_analysis: Optional[str]
    docstrings: Optional[str]
    markdown_docs: Optional[str]
    validation_report: Optional[str]
    mermaid_diagrams: Optional[str]
    final_documentation: Optional[str]
    
    # HITL (Human-in-the-Loop)
    human_feedback: Optional[str]
    approved_sections: List[str]
    needs_review: List[str]
    
    # Memory & Context
    documentation_style: Optional[str]  # PEP 257, Google, NumPy, JSDoc, etc.
    
    previous_terminology: Dict[str, str]  # Consistent terms across modules
    user_preferences: Dict[str, Any]  # Stored preferences
    #change tracking
    previous_code: Optional[str]
    changes_detected: Optional[Dict]
    is_update: bool
    # Control
    workers_completed: List[str]
    all_workers_done: bool
    error: Optional[str]
    progress_messages: List[str]


class LangGraphSupervisorWorkflow:
    """Enhanced supervisor with ALL core functionalities"""
    
    def __init__(self, model_name: str = "gpt-5-mini", temperature: float = 0.3):
        """Initialize with memory and context management"""
        actual_model = "gpt-5-mini"
        
        # Separate LLM clients for parallel execution
        self.llm_parser = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        self.llm_docstring = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        self.llm_markdown = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        self.llm_validator = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        self.llm_diagram = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        self.llm_compiler = ChatOpenAI(model=actual_model, temperature=temperature, max_retries=2, timeout=120.0)
        
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.progress_callback = None
        
        # Memory storage for consistent documentation across projects
        self.context_memory = {}  # project_id -> context
    
    def _build_graph(self) -> StateGraph:
        """Build enhanced graph with HITL checkpoint"""
        workflow = StateGraph(SupervisorState)
        
        workflow.add_node("change_detector", self.change_detector_node)  # NEW
        workflow.add_node("parallel_workers", self.parallel_workers_node)
        workflow.add_node("diagram_generator", self.diagram_generator_node)
        workflow.add_node("validator", self.validator_node)
        workflow.add_node("human_review", self.human_review_node)
        workflow.add_node("compiler", self.compiler_node)
        
        workflow.set_entry_point("change_detector")  # CHANGED
        workflow.add_edge("change_detector", "parallel_workers")  # NEW
        workflow.add_edge("parallel_workers", "diagram_generator")
        workflow.add_edge("diagram_generator", "validator")
        workflow.add_edge("validator", "human_review")
        
        workflow.add_conditional_edges(
            "human_review",
            lambda state: "needs_review" if state.get("needs_review") else "approved",
            {
                "needs_review": "parallel_workers",
                "approved": "compiler"
            }
        )
        workflow.add_edge("compiler", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def change_detector_node(self, state: SupervisorState) -> SupervisorState:
        """Detect changes between old and new code"""
        msg = "Analyzing code changes..."
        state["progress_messages"].append(msg)
        if self.progress_callback:
            self.progress_callback(5, 100, msg)
        
        previous_code = state.get("previous_code")
        current_code = state.get("code_content")
        
        if previous_code and previous_code != current_code:
            # Changes detected - run comparison
            tracker = CodeChangeTracker()
            changes = tracker.compare_code(previous_code, current_code)
            
            state["changes_detected"] = changes
            state["is_update"] = True
            
            msg = f"🔄 Changes detected: {changes['summary']}"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(8, 100, msg)
        else:
            # No previous code or no changes
            state["changes_detected"] = None
            state["is_update"] = False
            
            msg = "📝 Processing new code (no previous version)"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(8, 100, msg)
        
        return state
    
    def parallel_workers_node(self, state: SupervisorState) -> SupervisorState:
        """Execute 3 core workers in parallel with context awareness"""
        import time
        
        msg = "Starting parallel documentation workers with context awareness..."
        state["progress_messages"].append(msg)
        if self.progress_callback:
            self.progress_callback(10, 100, msg)
        
        code_content = state["code_content"]
        language = state["language"]
        
        # Get documentation style preference
        doc_style = state.get("documentation_style") or self._detect_doc_style(language)
        state["documentation_style"] = doc_style
        
        # Load previous terminology for consistency
        prev_terms = state.get("previous_terminology", {})
        
                # Get change information if this is an update
        is_update = state.get("is_update", False)
        changes = state.get("changes_detected")
        change_context = ""
        
        if is_update and changes:
            additions = changes.get('additions', [])
            deletions = changes.get('deletions', [])
            modifications = changes.get('modifications', [])
            
            change_context = f"""
**🔄 CODE UPDATE - Focus on changed items:**
Summary: {changes.get('summary', 'Changes detected')}

Additions: {[f"{a['type']}:{a['name']}" for a in additions]}
Deletions: {[f"{d['type']}:{d['name']}" for d in deletions]}


**Instructions:**
- Update documentation for modified items
- Add documentation for new items
- Mark updated sections with 🔄
- Remove documentation for deleted items
"""
        
        def run_code_analysis():
            """Deep code parsing & analysis"""
            try:
                time.sleep(0.2)
                messages = [
                    SystemMessage(content=f"""You are an expert code analyzer for {language}. Perform deep structural analysis.

{change_context}

**Extract ALL code components:**

## Code Structure Overview
[Architecture, design patterns, organization]

## Imports and Dependencies
**External Dependencies:**
- package_name (version): purpose
- another_package: usage

**Internal Modules:**
- module.submodule: what it provides

## Functions
For EACH function:
**`function_name(param1: type, param2: type) -> return_type`**
- **Purpose**: What it does
- **Parameters**: 
  - param1 (type): description
  - param2 (type): description
- **Returns**: return_type - description
- **Raises**: ExceptionType - when and why
- **Complexity**: O(n) time, O(1) space
- **Usage Example**:
```{language}
result = function_name(arg1, arg2)
```

## Classes
For EACH class:
**`ClassName(BaseClass)`**
- **Purpose**: What it represents
- **Inheritance**: Base classes and why
- **Attributes**:
  - attr1 (type): description
  - attr2 (type): description
- **Methods**: [List with brief descriptions]
- **Design Patterns**: Observer, Factory, etc.
- **Usage Example**:
```{language}
obj = ClassName()
obj.method()
```

## Complex Constructs
- **Decorators**: @decorator_name and their effects
- **Nested Functions**: Purpose and scope
- **Generators/Iterators**: How they work
- **Context Managers**: Usage patterns

## Module Relationships
- How modules depend on each other
- Data flow between components

**Be exhaustive - extract EVERYTHING.**"""),
                    HumanMessage(content=f"**Language:** {language}\n\n**Code:**\n```{language}\n{code_content}\n```")
                ]
                response = self.llm_parser.invoke(messages)
                return ("code_analysis", response.content)
            except Exception as e:
                return ("code_analysis", f"Error: {str(e)}")
        
        def run_docstring_generation():
            """Generate docstrings with consistent style"""
            try:
                time.sleep(0.4)
                
                # Get style guide
                style_guides = {
                    "python": f"{doc_style} (PEP 257 compliant)",
                    "javascript": "JSDoc @param, @returns, @throws",
                    "typescript": "TSDoc format",
                    "java": "Javadoc /** */ format",
                    "c#": "XML documentation comments /// <summary>",
                    "go": "GoDoc // function_name does...",
                    "rust": "Rustdoc /// with markdown",
                }
                style = style_guides.get(language.lower(), "Standard documentation comments")
                
                # Build terminology context
                term_context = ""
                if prev_terms:
                    term_context = f"\n**Use consistent terminology:**\n"
                    for term, definition in prev_terms.items():
                        term_context += f"- {term}: {definition}\n"
                
                state["progress_messages"].append(f"📝 Generating {style} docstrings with consistent terminology...")
                
                example_code = self._get_docstring_example(language, style)
                
                messages = [
                    SystemMessage(content=f"""You are a docstring expert for {language}. Generate COMPLETE, CONSISTENT docstrings using {style}.

{term_context}

**Requirements:**
1. Add docstrings to ALL functions and classes
2. Follow {style} format exactly
3. Include:
   - Brief one-line summary
   - Detailed explanation (2-3 sentences)
   - ALL parameters with types and descriptions
   - Return value with type and description
   - ALL exceptions that can be raised
   - Usage example for complex functions
   - Notes about complexity, edge cases, or gotchas

**Output the COMPLETE source code with integrated docstrings.**

**Example:**
{example_code}"""),
                    HumanMessage(content=f"**Code:**\n```{language}\n{code_content}\n```\n\n**Generate complete code with all docstrings integrated.**")
                ]
                response = self.llm_docstring.invoke(messages)
                state["progress_messages"].append("Docstring generation completed with consistent style")
                return ("docstrings", response.content)
            except Exception as e:
                return ("docstrings", f"Error: {str(e)}")
        
        def run_markdown_generation():
            """Generate structured markdown documentation"""
            try:
                time.sleep(0.6)
                state["progress_messages"].append("📄 Creating comprehensive markdown documentation...")
                
                markdown_template = """**Structure:**

# Project Name - API Documentation

## Overview
[Project purpose, key features, architecture summary]

## Installation
```bash
# Installation steps
```

## Quick Start
```
# Basic usage example with actual code
```

## API Reference

### Module: module_name
[Module purpose and overview]

#### Functions

##### `function_name(param1: type, param2: type) -> return_type`

**Description:** Comprehensive explanation of what the function does, its purpose, and when to use it.

**Parameters:**
- `param1` (type): Detailed parameter description
- `param2` (type): Detailed parameter description

**Returns:**
- type: Description of return value

**Raises:**
- `ExceptionType`: When and why this exception occurs

**Example:**
```
# Complete working example
result = function_name(value1, value2)
print(result)  # Output: expected_output
```

**Notes:**
- Time complexity: O(n)
- Space complexity: O(1)
- Thread-safety: Yes/No

#### Classes

##### `ClassName`

**Description:** What this class represents and its role

**Inheritance:**
- Inherits from: BaseClass
- Implements: InterfaceA, InterfaceB

**Attributes:**
- `attr1` (type): Description and default value
- `attr2` (type): Description

**Methods:**

###### `method_name(param: type) -> return_type`
[Same format as functions]

**Usage Example:**
```
# Complete example
obj = ClassName()
result = obj.method_name(param)
```

## Architecture

### Design Patterns
- Pattern Name: Where and why it's used

### Module Relationships
```
ModuleA -> ModuleB -> ModuleC
  |          |
  v          v
ModuleD    ModuleE
```

### Data Flow
[Explain how data moves through the system]

## Advanced Usage

### Use Case 1: [Scenario]
```
# Complete code example
```

### Use Case 2: [Another Scenario]
```
# Complete code example
```

## Error Handling
```
# How to handle common errors
```

## Performance Tips
- Optimization 1
- Optimization 2

## Testing
```
# Test examples
```

## Troubleshooting
**Issue**: Common problem
**Solution**: How to fix it

## Contributing
[If open source]

**Make it comprehensive, professional, and ready for production use.**"""
                
                messages = [
                    SystemMessage(content=f"You are a technical writer. Create professional markdown documentation for {language} code.\n\n{markdown_template}"),
                    HumanMessage(content=f"**Language:** {language}\n\n**Code:**\n```{language}\n{code_content}\n```")
                ]
                response = self.llm_markdown.invoke(messages)
                state["progress_messages"].append("Markdown documentation created")
                return ("markdown_docs", response.content)
            except Exception as e:
                return ("markdown_docs", f"Error: {str(e)}")
        
        # Execute 3 workers in parallel
        try:
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(run_code_analysis),
                    executor.submit(run_docstring_generation),
                    executor.submit(run_markdown_generation)
                ]
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    worker_name, result = future.result()
                    state[worker_name] = result
                    completed += 1
                    progress = int((completed / 3) * 30) + 10  # 10-40%
                    
                    if not result.startswith("Error:"):
                        msg = f"✓ {worker_name.replace('_', ' ').title()} completed"
                        state["progress_messages"].append(msg)
                        if self.progress_callback:
                            self.progress_callback(progress, 100, msg)
            
            elapsed = time.time() - start_time
            state["all_workers_done"] = True
            msg = f"Core analysis completed in {elapsed:.1f}s"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(40, 100, msg)
            
        except Exception as e:
            state["error"] = f"Parallel execution failed: {str(e)}"
        
        return state
    
    def diagram_generator_node(self, state: SupervisorState) -> SupervisorState:
        """Generate mermaid diagrams for architecture"""
        msg = "Generating architecture diagrams..."
        state["progress_messages"].append(msg)
        if self.progress_callback:
            self.progress_callback(50, 100, msg)
        
        try:
            code_analysis = state.get("code_analysis", "")
            language = state.get("language", "")
            
            diagram_template = """**Generate 2-3 diagrams using CORRECT Mermaid syntax:**

## Architecture Diagram
```mermaid
graph TD
    A[Module A] -->|uses| B[Module B]
    A -->|depends on| C[Module C]
    B --> D[External Service]
```

## Class Hierarchy
```mermaid
classDiagram
    BaseClass <|-- DerivedClass1
    BaseClass <|-- DerivedClass2
    class BaseClass{
        +attribute1 type
        +method1() returnType
    }
    class DerivedClass1{
        +attribute2 type
        +method2() returnType
    }
```

## Sequence Diagram (if applicable)
```mermaid
sequenceDiagram
    User->>System: request()
    System->>Database: query()
    Database-->>System: result
    System-->>User: response
```

**CRITICAL: Use CORRECT Mermaid classDiagram syntax:**
- Attributes and methods MUST be inside class blocks using curly braces
- Use this format: `class ClassName{ +attr type +method() type }`
- Do NOT use colon syntax like `ClassName : +attr`
- Use actual names from the code analyzed

**Use actual names from the code. Make diagrams clear and informative.**"""
            
            messages = [
                SystemMessage(content=f"You are a diagram expert. Create mermaid diagrams for code architecture.\n\n{diagram_template}"),
                HumanMessage(content=f"**Language:** {language}\n\n**Code Analysis:**\n{code_analysis[:3000]}")
            ]
            
            response = self.llm_diagram.invoke(messages)
            state["mermaid_diagrams"] = response.content
            
            msg = "Architecture diagrams generated"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(60, 100, msg)
            
        except Exception as e:
            state["mermaid_diagrams"] = f"# Diagrams\n\n*Diagram generation encountered an issue*"
        
        return state
    
    def validator_node(self, state: SupervisorState) -> SupervisorState:
        """Validate completeness and consistency"""
        msg = "Validating documentation quality..."
        state["progress_messages"].append(msg)
        if self.progress_callback:
            self.progress_callback(70, 100, msg)
        
        try:
            code = state.get("code_content", "")
            docstrings = state.get("docstrings", "")
            markdown = state.get("markdown_docs", "")
            
            messages = [
                SystemMessage(content="""You are a documentation quality validator. Check for:

## Completeness
- ✓ All public functions documented
- ✓ All classes documented
- ✓ All methods documented
- ⚠ Missing: [list any undocumented items]

## Consistency
- Parameter names match between code and docs
- Return types are consistent
- Terminology is uniform

## Quality Issues
- ⚠ Incomplete parameter descriptions: [list]
- ⚠ Missing examples: [list]
- ⚠ Vague descriptions: [list]
- ⚠ Missing exception documentation: [list]

## Coverage Metrics
- **Functions documented:** X/Y (Z%)
- **Classes documented:** A/B (C%)
- **Overall score:** Excellent/Good/Needs Improvement

## Recommendations
1. [Specific improvement 1]
2. [Specific improvement 2]

**Flag items that MUST be reviewed by human.**"""),
                HumanMessage(content=f"**Documented Code:**\n{docstrings[:2000]}\n\n**Markdown:**\n{markdown[:2000]}")
            ]
            
            response = self.llm_validator.invoke(messages)
            state["validation_report"] = response.content
            
            # Extract items needing review
            needs_review = []
            if "⚠" in response.content or "Missing:" in response.content:
                needs_review.append("Incomplete documentation detected")
            
            state["needs_review"] = needs_review
            
            msg = "Validation completed"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(80, 100, msg)
            
        except Exception as e:
            state["validation_report"] = f"Validation error: {str(e)}"
        
        return state
    
    def human_review_node(self, state: SupervisorState) -> SupervisorState:
        """HITL checkpoint - can be customized for actual human review"""
        needs_review = state.get("needs_review", [])
        
        if needs_review and not state.get("human_feedback"):
            # In production, this would pause for human input
            msg = f"⏸ Human review checkpoint: {len(needs_review)} items need attention"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(85, 100, msg)
            
            # AUTO-APPROVE for now (can be changed to wait for feedback)
            state["approved_sections"] = ["all"]
            state["human_feedback"] = "Auto-approved for automated workflow"
            state["needs_review"] = []  # Clear to proceed
        else:
            # Already reviewed or no issues
            state["approved_sections"] = ["all"]
        
        return state
    
    def compiler_node(self, state: SupervisorState) -> SupervisorState:
        """Compile final documentation with all sections"""
        msg = "Compiling final documentation..."
        state["progress_messages"].append(msg)
        if self.progress_callback:
            self.progress_callback(90, 100, msg)
        
        try:
            project_name = state.get('project_name', 'Project')
            language = state.get('language', 'Code')
            style = state.get('documentation_style', 'Standard')
            
            # Add change tracking section if this is an update
            changes_section = ""
            if state.get("is_update") and state.get("changes_detected"):
                from backend.core.change_tracker import CodeChangeTracker
                tracker = CodeChangeTracker()
                tracker.changes = state["changes_detected"]
                changes_section = f"\n\n{tracker.format_changes_markdown()}\n---\n"
            
            final_doc = f"""# {project_name} - Code Documentation

**Language:** {language}  
**Documentation Style:** {style}  
**Generated:** Auto-generated with AI Code Documentation Agent

{changes_section}

---

# 📋 Table of Contents

1. [Code Structure Analysis](#code-structure-analysis)
2. [API Documentation](#api-documentation)
3. [Documented Source Code](#documented-source-code)
4. [Architecture Diagrams](#architecture-diagrams)
5. [Quality Validation Report](#quality-validation-report)

---

# Code Structure Analysis

{state.get('code_analysis', 'Analysis pending...')}

---

# API Documentation

{state.get('markdown_docs', 'Documentation pending...')}

---

# Documented Source Code

Below is the complete source code with comprehensive docstrings:

{state.get('docstrings', 'Docstrings pending...')}

---

# Architecture Diagrams

{state.get('mermaid_diagrams', 'No diagrams available.')}

---

# Quality Validation Report

{state.get('validation_report', 'Validation pending...')}

---

## 🔄 Human Review Status

{self._format_review_status(state)}

---

## 📚 Additional Resources

- Full API reference included above
- Source code with inline documentation
- Architecture diagrams for visual understanding
- Quality metrics and validation results

**Note:** This documentation was generated automatically and reviewed for quality and completeness.
"""
            
            state["final_documentation"] = final_doc
            
            # Store terminology for future use (Memory)
            self._extract_and_store_terminology(state)
            
            msg = "Final documentation compiled"
            state["progress_messages"].append(msg)
            if self.progress_callback:
                self.progress_callback(100, 100, msg)
            
        except Exception as e:
            state["error"] = f"Compilation failed: {str(e)}"
        
        return state
    
    def _detect_doc_style(self, language: str) -> str:
        """Detect appropriate documentation style for language"""
        styles = {
            "python": "Google Style",
            "javascript": "JSDoc",
            "typescript": "TSDoc",
            "java": "Javadoc",
            "c#": "XML Documentation",
            "go": "GoDoc",
            "rust": "Rustdoc"
        }
        return styles.get(language.lower(), "Standard")
    
    def _get_docstring_example(self, language: str, style: str) -> str:
        """Get example docstring for the language"""
        examples = {
            "python": '''
def calculate(x: int, y: int) -> int:
    """
    Calculate the sum of two integers.
    
    This function performs addition of two integer values and
    returns the result. It handles standard integer arithmetic.
    
    Args:
        x (int): The first integer value
        y (int): The second integer value
    
    Returns:
        int: The sum of x and y
    
    Raises:
        TypeError: If inputs are not integers
    
    Example:
        >>> calculate(5, 3)
        8
    """
    return x + y
''',
            "javascript": '''
/**
 * Calculate the sum of two numbers
 * 
 * @param {number} x - The first number
 * @param {number} y - The second number
 * @returns {number} The sum of x and y
 * @throws {TypeError} If inputs are not numbers
 * 
 * @example
 * calculate(5, 3); // returns 8
 */
function calculate(x, y) {
    return x + y;
}
'''
        }
        return examples.get(language.lower(), "# Standard documentation comment")
    
    def _format_review_status(self, state: SupervisorState) -> str:
        """Format human review status"""
        approved = state.get("approved_sections", [])
        feedback = state.get("human_feedback", "")
        
        if approved:
            return f"✅ **Approved Sections:** {', '.join(approved)}\n\n**Feedback:** {feedback}"
        return "⏸ Pending human review"
    
    def _extract_and_store_terminology(self, state: SupervisorState):
        """Extract terminology for future consistency (Memory)"""
        # This would store common terms for reuse across projects
        project_name = state.get("project_name", "")
        if project_name:
            self.context_memory[project_name] = {
                "style": state.get("documentation_style"),
                "timestamp": "now"
            }
    
    def process_code(self, code_content: str, language: str, project_name: str, 
                     thread_id: str, progress_callback=None, 
                     user_preferences: Dict = None, previous_code: str = None) -> Dict[str, Any]:
        """Execute the enhanced workflow with all features"""
        self.progress_callback = progress_callback
        
        # Load user preferences and previous context
        previous_context = self.context_memory.get(project_name, {})
        
        initial_state: SupervisorState = {
            "code_content": code_content,
            "language": language,
            "project_name": project_name,
            "previous_code": previous_code,
            "changes_detected": None,
            "is_update": False,
            "code_analysis": None,
            "docstrings": None,
            "markdown_docs": None,
            "validation_report": None,
            "mermaid_diagrams": None,
            "final_documentation": None,
            "human_feedback": None,
            "approved_sections": [],
            "needs_review": [],
            "documentation_style": user_preferences.get("style") if user_preferences else previous_context.get("style"),
            "previous_terminology": previous_context.get("terminology", {}),
            "user_preferences": user_preferences or {},
            "workers_completed": [],
            "all_workers_done": False,
            "error": None,
            "progress_messages": []
        }
        
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 15  # Allow for HITL loops
        }
        
        final_state = self.graph.invoke(initial_state, config)
        
        return final_state
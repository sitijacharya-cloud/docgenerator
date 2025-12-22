#  Code Documentation Agent

An intelligent AI-powered code documentation system that automatically generates comprehensive, professional documentation for your codebase using LangGraph workflows and GPT-4.

## ✨ Features

### 🔍 Intelligent Code Analysis
- Multi-language support (Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP)
- Automatic code structure parsing
- Function/class extraction and analysis
- Complexity detection

### 📝 Automated Documentation Generation
- **Inline Docstrings**: Google, NumPy, JSDoc, and language-specific styles
- **Markdown Documentation**: Professional README-style docs
- **API Documentation**: Comprehensive API reference
- **Mermaid Diagrams**: Class diagrams, flowcharts, sequence diagrams

### 🔄 Change Tracking
- Detects code modifications between versions
- Highlights additions and deletions
- Smart comparison for functions and classes


### 🎯 LangGraph Supervisor Workflow
- Parallel AI worker execution
- Code parser → Docstring generator → Markdown writer → Diagram creator
- Validation and quality checks
- Memory-aware documentation consistency

### 💾 Project Management
- Store multiple projects
- File-based storage system
- Project metadata tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend                       │
│  - File Upload  - Progress Tracking  - Documentation UI │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Backend (FastAPI)                        │
│  - REST API  - File Management  - Project Storage       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            LangGraph Supervisor Workflow                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Parser  │→ │ Docstring│→ │ Markdown │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│  ┌──────────┐  ┌──────────┐                             │
│  │ Validator│→ │ Diagrams │                             │
│  └──────────┘  └──────────┘                             │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              OpenAI GPT-4o-mini                  │
└──────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API Key


## 📖 Usage

### 1. Upload Code File

- Click **"Choose File"** or drag & drop
- Supported formats: `.py`, `.js`, `.ts`, `.java`, `.cs`, `.go`, `.rs`, `.php`
- Click **"Generate Documentation"**

### 2. Monitor Progress

Watch real-time progress as AI workers process your code:
- 🔍 Analyzing code structure
- 📝 Generating docstrings
- 📄 Creating markdown documentation
- 📊 Generating diagrams
- ✅ Validating output

### 3. View & Download Documentation

- **Inline Docstrings**: Copy annotated code
- **Markdown Docs**: Professional README
- **Mermaid Diagrams**: Visual representations
- **Download All**: ZIP package with all files

### 4. Update Existing Code

Re-upload the same filename with modifications:
- ✅ Additions highlighted
- ❌ Deletions tracked
- Change summary included in docs


## 🔧 Configuration

### Environment Variables

Create `.env` file in `backend/`:

```env
# Required
OPENAI_API_KEY=sk-...



## 📊 API Endpoints

### POST `/generate-documentation/`

Generate documentation for code file.

**Request:**
```bash
curl -X POST "http://localhost:8000/generate-documentation/" \
  -F "file=@sample.py"
```

**Response:**
```json
{
  "project_id": "uuid",
  "file_name": "sample.py",
  "language": "python",
  "documentation": {
    "inline_docstrings": "...",
    "markdown_docs": "...",
    "mermaid_diagrams": "...",
    "validation_report": "..."
  },
  "changes_detected": true
}
```

### GET `/project/{project_id}`

Retrieve project documentation.

### GET `/projects/`

List all projects.

### GET `/download/{project_id}`

Download documentation as ZIP file.

## 🧪 Example Output

### Input Code
```python
def calculate_total(items, tax_rate=0.1):
    subtotal = sum(item['price'] for item in items)
    return subtotal * (1 + tax_rate)
```

### Generated Docstring
```python
def calculate_total(items, tax_rate=0.1):
    """
    Calculate total price including tax.
    
    Args:
        items (List[Dict]): List of items with 'price' key
        tax_rate (float, optional): Tax percentage. Defaults to 0.1.
    
    Returns:
        float: Total price with tax applied
        
    Example:
        >>> items = [{'price': 10}, {'price': 20}]
        >>> calculate_total(items)
        33.0
    """
    subtotal = sum(item['price'] for item in items)
    return subtotal * (1 + tax_rate)
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🐛 Known Issues

- Large files (>1MB) may take longer to process
- Some complex nested classes may not be fully detected
- Mermaid diagrams have a complexity limit


## 💬 Support

For issues and questions:
- 📧 Email: support@codedocagent.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/code-doc-agent/issues)

## 🙏 Acknowledgments

- **LangGraph**: Workflow orchestration
- **OpenAI**: GPT-4 language models
- **FastAPI**: High-performance backend
- **React**: Interactive UI

---


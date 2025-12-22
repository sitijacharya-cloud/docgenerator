import streamlit as st
import time
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.client import APIClient
from frontend.sse_client import get_progress_stream


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"



def get_stored_code(project_name: str) -> str:
    """Get previously stored code for change tracking"""
    if 'previous_code_storage' not in st.session_state:
        st.session_state.previous_code_storage = {}
    return st.session_state.previous_code_storage.get(project_name, None)


def store_code(project_name: str, code_content: str):
    """Store code for future change tracking"""
    if 'previous_code_storage' not in st.session_state:
        st.session_state.previous_code_storage = {}
    st.session_state.previous_code_storage[project_name] = code_content
def init_session_state():
    """Initialize session state."""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    if 'processing_project_id' not in st.session_state:
        st.session_state.processing_project_id = None
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False


def get_live_progress(project_id: str) -> dict:
    """Get latest progress - non-blocking."""
    cache_key = f'progress_cache_{project_id}'
    
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {
            "status": "processing",
            "progress_message": "Connecting to backend...",
            "current_chunk": 0,
            "total_chunks": 0
        }
    
    try:
        progress = get_progress_stream(project_id, timeout=1)
        if progress and isinstance(progress, dict):
            st.session_state[cache_key].update(progress)
    except Exception:
        pass
    
    return st.session_state[cache_key]


@st.fragment(run_every=2)
def monitor_processing_inline():
    """Fragment that shows inline progress below upload section."""
    project_id = st.session_state.get('processing_project_id')
    if not project_id or not st.session_state.get('monitoring', False):
        return
    
    progress = get_live_progress(project_id)
    
    status = progress.get('status', 'processing')
    msg = progress.get('progress_message', 'Processing...')
    current = progress.get('current_chunk', 0)
    total = progress.get('total_chunks', 0)
    
    if total > 0 and current > 0:
        progress_val = current / total
        st.progress(progress_val, text=f"{msg}")
    else:
        st.progress(0, text=msg)
    
    # Check if done
    if status == 'completed':
        st.session_state.monitoring = False
        st.session_state.selected_project_id = project_id
        st.session_state.processing_project_id = None
        st.switch_page("pages/projects.py")
    elif status == 'error':
        st.session_state.monitoring = False
        st.session_state.processing_project_id = None
        st.error(f"❌ Error: {msg}")
        st.rerun()


init_session_state()

st.title("AI Code Documentation Generator")
st.caption("Upload your source code to automatically generate comprehensive documentation")

# Show supported languages
with st.expander("📋 Supported Programming Languages"):
    col1, col2, col3, col4 = st.columns(4)
    
    languages = [
        "Python", "JavaScript", "TypeScript", "Java",
        "C#", "C++", "C", "Go",
        "Rust", "Ruby", "PHP", "Swift",
        "Kotlin", "Scala", "R", "MATLAB",
        "Shell/Bash", "SQL", "HTML/CSS", "Vue",
        "Dart", "Lua", "Perl"
    ]
    
    for i, lang in enumerate(languages):
        col = [col1, col2, col3, col4][i % 4]
        with col:
            st.markdown(f"✅ {lang}")

st.divider()

st.subheader("Upload Source Code")

upload_mode = st.radio(
    "Upload Mode:", 
    ["Single File", "Multiple Files"], 
    horizontal=True
)

if upload_mode == "Single File":
    uploaded_file = st.file_uploader(
        "Choose a source code file",
        type=["py", "js", "ts", "jsx", "tsx", "java", "cs", "cpp", "c", "go", "rs", "php"],
        help="Upload a source code file to generate documentation"
    )
    uploaded_files = [uploaded_file] if uploaded_file else []
else:
    uploaded_files = st.file_uploader(
        "Choose source code files",
        type=["py", "js", "ts", "jsx", "tsx", "java", "cs", "cpp", "c", "go", "rs", "php"],
        accept_multiple_files=True,
        help="Upload multiple files from a folder"
    )
if uploaded_files:
    for uploaded_file in uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text(f"📄 {uploaded_file.name}")
            st.text(f"Size: {format_file_size(uploaded_file.size)}")
            
            from backend.core.code_loader import CodeLoader
            try:
                language = CodeLoader.detect_language(uploaded_file.name)
                st.text(f"Language: {language}")
            except:
                st.warning(f"⚠️ Could not detect language")
        
        st.divider()
    
    # Single button to process all files
    if st.button("📝 Generate Documentation for All Files", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            response = st.session_state.api_client.upload_code(
                file_bytes=file_bytes,
                filename=uploaded_file.name
            )
            project_id = response['id']
            
            st.session_state.api_client.process_project(project_id)
            
            # Store last project for viewing
            if idx == len(uploaded_files) - 1:
                st.session_state.processing_project_id = project_id
                st.session_state.monitoring = True
        
        st.success(f"✅ Uploaded {len(uploaded_files)} files!")
        time.sleep(1)
        st.rerun()
        
    st.divider()

# Show inline progress if processing
if st.session_state.get('monitoring', False) and st.session_state.get('processing_project_id'):
    st.divider()
    st.subheader("Documentation Generation Progress")
    monitor_processing_inline()

# Info section
st.divider()
st.subheader("✨ What This Tool Does")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **📝 Generates:**
    - Language-specific docstrings
    - Comprehensive API documentation
    - Code structure analysis
    - Usage examples
    - Markdown & PDF documentation
    """)

with col2:
    st.markdown("""
    **✅ Features:**
    - Multi-language support
    - Automatic validation
    - Quality assurance checks
    - Export to multiple formats
    - AI-powered insights
    """)
import streamlit as st
import requests
import time
from pathlib import Path


# API Configuration
API_BASE_URL = "http://localhost:8000/api"


st.set_page_config(
    page_title="AI Documentation Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Documentation Generator")
st.markdown("Automatically generate comprehensive documentation for your Python code using AI")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This tool uses:
    - **LangGraph** for workflow orchestration
    - **OpenAI GPT** for documentation generation
    - **ChromaDB** for context management
    - **Python AST** for code parsing
    """)
    
    st.header("📋 Features")
    st.markdown("""
    - Parse Python code
    - Generate docstrings
    - Create markdown docs
    - Validate documentation
    """)

# Main content
st.header("1️⃣ Input Configuration")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    code_path = st.text_input(
        "Code Path",
        placeholder="/path/to/your/python/code",
        help="Enter the path to a Python file or directory"
    )

with col2:
    project_name = st.text_input(
        "Project Name",
        value="my_project",
        help="Name for your documentation"
    )
with col3:
    language = st.selectbox(
        "Language",
        options=["Auto-detect", "Python", "JavaScript", "Java", "C#"],
        help="Select programming language or auto-detect"
    )
# NEW: Advanced options
with st.expander("⚙️ Advanced Options"):
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        generate_diagram = st.checkbox(
            "Generate Architecture Diagram",
            value=True,
            help="Create Mermaid diagram showing code structure"
        )
    
    with col_opt2:
        generate_pdf = st.checkbox(
            "Generate PDF",
            value=False,
            help="Export documentation as PDF (takes longer)"
        )

# Convert language selection
language_map = {
    "Auto-detect": None,
    "Python": "python",
    "JavaScript": "javascript",
    "Java": "java",
    "C#": "csharp"
}
selected_language = language_map[language]

# Generate button
if st.button("🚀 Generate Documentation", type="primary", use_container_width=True):
    if not code_path:
        st.error("Please enter a code path")
    elif not Path(code_path).exists():
        st.error(f"Path does not exist: {code_path}")
    else:
        # Create job
        with st.spinner("Starting documentation generation..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/generate-docs",
                    json={
                        "code_path": code_path,
                        "project_name": project_name,
                        "language": selected_language,
                        "generate_diagram": generate_diagram, 
                        "generate_pdf": generate_pdf  
                    },
                    timeout=None
                )
                response.raise_for_status()
                data = response.json()
                job_id = data['job_id']
                
                st.session_state.job_id = job_id
                st.success(f"Job created: {job_id}")
                
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure the backend is running on http://localhost:8000")
                st.stop()
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.stop()
        
        # Poll for completion
        st.header("2️⃣ Processing Status")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        max_attempts = 120  # 2 minutes with 1 second intervals
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status_response = requests.get(
                    f"{API_BASE_URL}/jobs/{job_id}",
                    timeout=None
                )
                status_data = status_response.json()
                current_status = status_data.get('status', 'unknown')
                
                status_text.info(f"Status: **{current_status}**")
                
                if current_status == 'completed':
                    progress_bar.progress(100)
                    st.success("✅ Documentation generated successfully!")
                    break
                elif current_status == 'failed':
                    progress_bar.progress(100)
                    error_msg = status_data.get('error', 'Unknown error')
                    st.error(f"❌ Documentation generation failed: {error_msg}")
                    break
                elif current_status == 'processing':
                    progress = min(50 + (attempt * 2), 95)
                    progress_bar.progress(progress)
                else:
                    progress = min(attempt * 3, 50)
                    progress_bar.progress(progress)
                
                time.sleep(1)
                attempt += 1
                
            except Exception as e:
                st.error(f"Error checking status: {str(e)}")
                break
        
        if attempt >= max_attempts:
            st.warning("⚠️ Job is taking longer than expected. Check back later.")

# Display results if job exists
if 'job_id' in st.session_state:
    st.header("3️⃣ Generated Documentation")
    
    try:
        docs_response = requests.get(
            f"{API_BASE_URL}/docs/{st.session_state.job_id}",
            timeout=None
        )
        
        if docs_response.status_code == 200:
            docs_data = docs_response.json()
            
            # Display markdown
            st.subheader("📄 Documentation Preview")
            markdown_content = docs_data.get('markdown_content', '')
            
            with st.container():
                st.markdown(markdown_content)
            
            # Download button
            st.download_button(
                label="⬇️ Download Markdown",
                data=markdown_content,
                file_name=f"{project_name}_documentation.md",
                mime="text/markdown",
                use_container_width=True
            )
            col_dl1, col_dl2 = st.columns(2)

            with col_dl1:
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=markdown_content,
                    file_name=f"{project_name}_documentation.md",
                    mime="text/markdown",
                    use_container_width=True)
            
            with col_dl2:
                # Check if PDF was generated
                pdf_path = docs_data.get('pdf_path')
                if pdf_path:
                    try:
                        pdf_response = requests.get(
                        f"{API_BASE_URL}/download/pdf/{st.session_state.job_id}",
                        timeout=30
                        )
                        if pdf_response.status_code == 200:
                            st.download_button(
                            label="📄 Download PDF",
                            data=pdf_response.content,
                            file_name=f"{project_name}_documentation.pdf",
                            mime="application/pdf",
                            use_container_width=True
                            )
                    except:
                        st.info("PDF not available")
                    else:
                        st.info("PDF not generated (enable in options)")

            
            # Validation results
            with st.expander("📊 Validation Results"):
                validation = docs_data.get('validation_results', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    overall_score = validation.get('overall_score', 0)
                    st.metric("Overall Score", f"{overall_score:.2%}")
                
                with col2:
                    component_count = docs_data.get('component_count', 0)
                    st.metric("Components Documented", component_count)
                
                # Component scores
                if 'component_scores' in validation:
                    st.subheader("Component Details")
                    for comp_id, result in validation['component_scores'].items():
                        with st.container():
                            score = result.get('score', 0)
                            issues = result.get('issues', [])
                            warnings = result.get('warnings', [])
                            
                            st.write(f"**{comp_id}** - Score: {score:.2%}")
                            
                            if issues:
                                st.error("Issues: " + ", ".join(issues))
                            if warnings:
                                st.warning("Warnings: " + ", ".join(warnings))
        
        elif docs_response.status_code == 404:
            st.info("Documentation not ready yet or job not found")
        
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API")
    except Exception as e:
        st.error(f"Error loading documentation: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Built with LangGraph, OpenAI, FastAPI, and Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
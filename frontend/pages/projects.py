import streamlit as st
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.client import APIClient
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api = APIClient()


def refine_with_ai(current_content: str, user_prompt: str) -> str:
    """Use LLM to refine documentation based on user prompt."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code documentation expert. Modify the documentation based on user instructions. Return the COMPLETE MODIFIED DOCUMENT with all sections intact."
                },
                {
                    "role": "user",
                    "content": f"""Documentation:\n\n{current_content}\n\nUser request: {user_prompt}\n\nReturn the ENTIRE document with requested changes as markdown."""
                }
            ],
            temperature=0.7,
        )
        
        refined = response.choices[0].message.content.strip()
        
        if refined.startswith("```markdown"):
            refined = refined[len("```markdown"):].strip()
        if refined.startswith("```"):
            refined = refined[3:].strip()
        if refined.endswith("```"):
            refined = refined[:-3].strip()
        
        return refined
    except Exception as e:
        st.error(f"AI refinement failed: {str(e)}")
        return current_content


def render_project_card(project):
    """Render project card."""
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([6, 2, 1, 1])
        
        with col1:
            st.markdown(f"### {project['name']}")
            if project.get('file_name'):
                st.caption(f"📄 {project['file_name']} • {project.get('language', 'Unknown')}")
        
        with col2:
            status = project["status"]
            if status == "completed":
                st.success("✅ Completed")
            elif status == "processing":
                st.info("⏳ Processing")
            else:
                st.error("❌ Failed")
        
        with col3:
            if status == "completed":
                if st.button("View", key=f"view_{project['id']}", use_container_width=True):
                    st.session_state.selected_project_id = project["id"]
                    st.rerun()
        
        with col4:
            if st.button("Delete", key=f"delete_{project['id']}", use_container_width=True):
                if api.delete_project(project['id']):
                    st.rerun()


def render_project_details(project_id: str):
    """Display documentation with edit capabilities."""
    try:
        project = api.get_project(project_id)
        analysis = api.get_code_analysis(project_id)
        docs = api.get_documentation(project_id)
        md_content = docs.get("content", "") if isinstance(docs, dict) else docs
        
        if f'edit_mode_{project_id}' not in st.session_state:
            st.session_state[f'edit_mode_{project_id}'] = False
        if f'edited_content_{project_id}' not in st.session_state:
            st.session_state[f'edited_content_{project_id}'] = md_content
        
        if st.button("← Back to Projects"):
            if "selected_project_id" in st.session_state:
                del st.session_state.selected_project_id
            st.rerun()
        
        st.title(f"{project['name']} Documentation")
        st.caption(f"Language: {project.get('language', 'Unknown')} | Generated: {project.get('uploaded_at', 'N/A')}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.session_state[f'edit_mode_{project_id}']:
                if st.button("Preview", use_container_width=True):
                    st.session_state[f'edit_mode_{project_id}'] = False
                    st.rerun()
            else:
                if st.button("Edit", use_container_width=True):
                    st.session_state[f'edit_mode_{project_id}'] = True
                    st.rerun()
        
        with col2:
            if st.button("AI Refine", use_container_width=True):
                st.session_state[f'show_ai_prompt_{project_id}'] = True
                st.rerun()
        
        with col3:
            current_content = st.session_state[f'edited_content_{project_id}']
            st.download_button(
                "Download MD",
                data=current_content,
                file_name=f"{project['name']}_documentation.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col4:
            current_content = st.session_state[f'edited_content_{project_id}']
            
            if f'pdf_bytes_{project_id}' not in st.session_state or \
               f'last_content_{project_id}' not in st.session_state or \
               st.session_state[f'last_content_{project_id}'] != current_content:
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_bytes = api.generate_pdf_from_content(current_content, f"{project['name']}_documentation")
                        st.session_state[f'pdf_bytes_{project_id}'] = pdf_bytes
                        st.session_state[f'last_content_{project_id}'] = current_content
                except Exception as e:
                    st.error(f"PDF failed: {str(e)}")
            
            if f'pdf_bytes_{project_id}' in st.session_state:
                st.download_button(
                    "Download PDF",
                    data=st.session_state[f'pdf_bytes_{project_id}'],
                    file_name=f"{project['name']}_documentation.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        st.divider()
        
        # AI Refine prompt
        if st.session_state.get(f'show_ai_prompt_{project_id}', False):
            with st.container(border=True):
                st.markdown("### AI Refinement")
                ai_prompt = st.text_area(
                    "What would you like to change?",
                    placeholder="e.g., Add more examples, Simplify technical terms, Add troubleshooting section",
                    height=100
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Apply Changes", type="primary"):
                        if ai_prompt:
                            with st.spinner("AI is refining..."):
                                refined_content = refine_with_ai(
                                    st.session_state[f'edited_content_{project_id}'],
                                    ai_prompt
                                )
                                st.session_state[f'edited_content_{project_id}'] = refined_content
                                st.session_state[f'show_ai_prompt_{project_id}'] = False
                                st.success("Changes applied!")
                                st.rerun()
                        else:
                            st.error("Please enter instructions")
                
                with col2:
                    if st.button("Cancel"):
                        st.session_state[f'show_ai_prompt_{project_id}'] = False
                        st.rerun()
                
                    
            st.divider()

        if st.button("📋 Review", use_container_width=True):
                            st.session_state[f'show_review_{project_id}'] = True
                            st.rerun()
            
        # Human review interface (HITL)
        if st.session_state.get(f'show_review_{project_id}', False):
            with st.container(border=True):
                st.markdown("### 📋 Human Review (HITL)")
                st.markdown("Review the generated documentation for quality and accuracy.")
                
                review_feedback = st.text_area(
                    "Review Comments",
                    placeholder="Enter feedback about documentation quality, missing items, or improvements needed...",
                    height=100
                )
                
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("✅ Approve", type="primary"):
                        import httpx
                        try:
                            httpx.post(
                                f"http://localhost:8000/projects/{project_id}/review",
                                json={
                                    "approved": True,
                                    "feedback": review_feedback or "Approved",
                                    "approved_sections": ["all"]
                                },
                                timeout=5.0
                            )
                            st.success("✅ Documentation approved!")
                            st.session_state[f'show_review_{project_id}'] = False
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Review submission failed: {e}")
                
                with col2:
                    if st.button("🔄 Request Changes"):
                        if review_feedback:
                            import httpx
                            try:
                                httpx.post(
                                    f"http://localhost:8000/projects/{project_id}/review",
                                    json={
                                        "approved": False,
                                        "feedback": review_feedback,
                                        "approved_sections": []
                                    },
                                    timeout=5.0
                                )
                                st.warning("Changes requested - feedback saved")
                                st.session_state[f'show_review_{project_id}'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Review submission failed: {e}")
                        else:
                            st.error("Please provide feedback for requested changes")
                
                with col3:
                    if st.button("Cancel"):
                        st.session_state[f'show_review_{project_id}'] = False
                        st.rerun()
            
            st.divider()
        # Edit or preview mode
        if st.session_state[f'edit_mode_{project_id}']:
            st.markdown("### Edit Documentation")
            edited = st.text_area(
                "Edit content:",
                value=st.session_state[f'edited_content_{project_id}'],
                height=600,
                key=f"editor_{project_id}"
            )
            
            if edited != st.session_state[f'edited_content_{project_id}']:
                st.session_state[f'edited_content_{project_id}'] = edited
                st.success("Changes saved")
        else:
            st.divider()
        
        import re
        
        display_content = st.session_state[f'edited_content_{project_id}']
        
        # Split by mermaid blocks
        parts = re.split(r'(```mermaid\n.*?```)', display_content, flags=re.DOTALL)
        
        for i, part in enumerate(parts):
            if part.startswith('```mermaid'):
                mermaid_code = part.replace('```mermaid\n', '').replace('```', '').strip()
                html_code = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script type="module">
                        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                        mermaid.initialize({{ 
                            startOnLoad: true, 
                            theme: 'default',
                            flowchart: {{ useMaxWidth: true }}
                        }});
                    </script>
                </head>
                <body>
                    <div class="mermaid">
                    {mermaid_code}
                    </div>
                </body>
                </html>
                """
                st.components.v1.html(html_code, height=500)
            else:
                if part.strip():
                    st.markdown(part)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("← Back"):
            if "selected_project_id" in st.session_state:
                del st.session_state.selected_project_id
            st.rerun()


# Check if viewing specific project
if "selected_project_id" in st.session_state:
    render_project_details(st.session_state.selected_project_id)
else:
    # Project list
    st.title("Documentation Projects")
    
    try:
        projects = api.list_projects()
        
        if not projects:
            st.info("🎯 No projects yet. Upload code to get started!")
            if st.button("Upload Code"):
                st.switch_page("pages/home.py")
        else:
            st.caption(f"Total: {len(projects)} project(s)")
            st.write("")
            
            for project in projects:
                render_project_card(project)
                st.write("")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
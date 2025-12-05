from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import re


class PDFGenerator:
    """Generate PDF from markdown documentation using ReportLab."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        
        # Check if style exists before adding
        def add_style_if_not_exists(name, **kwargs):
            if name not in self.styles:
                self.styles.add(ParagraphStyle(name=name, **kwargs))
        
        # Title style
        add_style_if_not_exists(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Heading 2
        add_style_if_not_exists(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Heading 3
        add_style_if_not_exists(
            'CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=HexColor('#7f8c8d'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        # Code style
        add_style_if_not_exists(
            'CustomCode',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=9,
            leftIndent=20,
            textColor=HexColor('#333333'),
            backColor=HexColor('#f4f4f4')
        )
    def generate_pdf(self, markdown_content: str, output_path: str) -> str:  # MAKE SURE THIS IS NOT INDENTED INSIDE _setup_custom_styles
        """Generate PDF from markdown content."""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Parse markdown and create story
            story = self._markdown_to_story(markdown_content)
            
            # Build PDF
            doc.build(story)
            
            return output_path
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

    
    
    def _markdown_to_story(self, markdown_content: str):
        """Convert markdown to ReportLab story."""
        story = []
        lines = markdown_content.split('\n')
        
        in_code_block = False
        is_mermaid = False 
        code_lines = []
        
        for line in lines:
            # Check for code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_lines and not is_mermaid:
                        code_text = '\n'.join(code_lines)
                        story.append(Preformatted(code_text, self.styles['CustomCode']))
                        story.append(Spacer(1, 0.2 * inch))
                    elif is_mermaid:
                        # Add note about diagram instead of code
                        story.append(Paragraph(
                            "<i>Note: Architecture diagram available in markdown version</i>",
                            self.styles['Normal']
                        ))
                        story.append(Spacer(1, 0.2 * inch))
                    code_lines = []
                    in_code_block = False
                    is_mermaid = False
                else:
                    # Start of code block
                    in_code_block = True
                    # Check if it's a mermaid diagram
                    is_mermaid = 'mermaid' in line.lower()
                continue
                        
            if in_code_block:
                code_lines.append(line)
                continue
            
            # Skip empty lines
            if not line.strip():
                story.append(Spacer(1, 0.1 * inch))
                continue
            
            # Clean the line first
            clean_line = line.strip()
            
            # Headers
            if clean_line.startswith('# '):
                text = self._clean_text(clean_line[2:])
                story.append(Paragraph(text, self.styles['CustomTitle']))
                story.append(Spacer(1, 0.2 * inch))
            
            elif clean_line.startswith('## '):
                text = self._clean_text(clean_line[3:])
                story.append(Paragraph(text, self.styles['CustomHeading2']))
                story.append(Spacer(1, 0.1 * inch))
            
            elif clean_line.startswith('### '):
                text = self._clean_text(clean_line[4:])
                story.append(Paragraph(text, self.styles['CustomHeading3']))
                story.append(Spacer(1, 0.1 * inch))
            
            # List items
            elif clean_line.startswith('- ') or clean_line.startswith('* '):
                text = '• ' + self._clean_text(clean_line[2:])
                story.append(Paragraph(text, self.styles['Normal']))
            
            # Regular paragraph
            else:
                text = self._clean_text(clean_line)
                if text:
                    story.append(Paragraph(text, self.styles['Normal']))
        
        return story

    def _clean_text(self, text: str) -> str:
        """Clean and escape text for ReportLab."""
        if not text:
            return ""
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)      # Italic
        text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)  # Inline code
        
        # Escape special characters (but not our HTML tags)
        text = re.sub(r'&(?!amp;|lt;|gt;|quot;)', '&amp;', text)
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore our HTML tags
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;font name="Courier"&gt;', '<font name="Courier">').replace('&lt;/font&gt;', '</font>')
        
        return text
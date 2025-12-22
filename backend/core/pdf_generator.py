from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Preformatted, Image
)
from reportlab.lib.colors import HexColor
from io import BytesIO
from typing import Optional
from pathlib import Path
import re
from datetime import datetime
import markdown
from html.parser import HTMLParser


class MarkdownToReportLab:
    """Convert markdown to ReportLab flowables"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for documentation"""
        
        # Heading styles
        self.styles.add(ParagraphStyle(
            name='CustomH1',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=20,
            spaceBefore=0,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 10, 0),
            borderColor=HexColor('#e1e4e8'),
            borderWidth=1,
            borderRadius=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomH2',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomH3',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomH4',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#4a5568'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Code style (check if exists first)
        if 'CustomCode' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomCode',
                parent=self.styles['Code'],
                fontSize=9,
                textColor=HexColor('#24292e'),
                backColor=HexColor('#f6f8fa'),
                borderColor=HexColor('#e1e4e8'),
                borderWidth=1,
                borderPadding=8,
                fontName='Courier',
                leftIndent=10,
                rightIndent=10,
                spaceAfter=10
            ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=HexColor('#2c3e50'),
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        ))
        
        # List style
        self.styles.add(ParagraphStyle(
            name='ListItem',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=HexColor('#2c3e50'),
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=6,
            leading=14
        ))
    
    def parse_markdown(self, md_content: str) -> list:
        """Parse markdown and convert to ReportLab flowables"""
        flowables = []
        
        # Replace mermaid diagrams with styled placeholders
        def replace_mermaid(match):
            mermaid_code = match.group(1)
            # Extract diagram type
            first_line = mermaid_code.strip().split('\n')[0]
            diagram_type = "Diagram"
            if 'graph' in first_line:
                diagram_type = "Architecture Diagram"
            elif 'classDiagram' in first_line:
                diagram_type = "Class Hierarchy Diagram"
            elif 'sequenceDiagram' in first_line:
                diagram_type = "Sequence Diagram"
            elif 'erDiagram' in first_line:
                diagram_type = "Entity Relationship Diagram"
            
            return f'\n\n**📊 {diagram_type}**\n\n*This diagram is available in the markdown version and web interface. Export the markdown file to view interactive diagrams.*\n\n'
        
        md_content = re.sub(r'```mermaid\n(.*?)```', replace_mermaid, md_content, flags=re.DOTALL)
        
        lines = md_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Headers
            if line.startswith('# '):
                text = line[2:].strip()
                flowables.append(Paragraph(text, self.styles['CustomH1']))
                flowables.append(Spacer(1, 0.1 * inch))
            elif line.startswith('## '):
                text = line[3:].strip()
                flowables.append(Spacer(1, 0.15 * inch))
                flowables.append(Paragraph(text, self.styles['CustomH2']))
            elif line.startswith('### '):
                text = line[4:].strip()
                flowables.append(Spacer(1, 0.1 * inch))
                flowables.append(Paragraph(text, self.styles['CustomH3']))
            elif line.startswith('#### '):
                text = line[5:].strip()
                flowables.append(Paragraph(text, self.styles['CustomH4']))
            
            # Code blocks
            elif line.startswith('```'):
                lang = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                code_text = '\n'.join(code_lines)
                # Use Preformatted for code blocks with CustomCode style
                code_para = Preformatted(code_text, self.styles['CustomCode'])
                flowables.append(code_para)
                flowables.append(Spacer(1, 0.1 * inch))
            
            # Horizontal rule
            elif line.strip() == '---':
                flowables.append(Spacer(1, 0.1 * inch))
                flowables.append(Table([['']], colWidths=[7*inch], 
                                      style=[('LINEABOVE', (0,0), (-1,0), 1, colors.grey)]))
                flowables.append(Spacer(1, 0.1 * inch))
            
            # Lists
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                text = line.strip()[2:].strip()
                text = f"• {text}"
                flowables.append(Paragraph(text, self.styles['ListItem']))
            
            elif re.match(r'^\d+\.\s', line.strip()):
                text = re.sub(r'^\d+\.\s', '', line.strip())
                match = re.match(r'^(\d+)\.', line.strip())
                num = match.group(1) if match else '1'
                text = f"{num}. {text}"
                flowables.append(Paragraph(text, self.styles['ListItem']))
            
            # Tables (basic support)
            elif '|' in line and line.strip().startswith('|'):
                table_lines = []
                while i < len(lines) and '|' in lines[i]:
                    if not lines[i].strip().replace('|', '').replace('-', '').strip():
                        # Skip separator line
                        i += 1
                        continue
                    cells = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                    if cells:
                        table_lines.append(cells)
                    i += 1
                i -= 1  # Adjust because outer loop will increment
                
                if table_lines:
                    # Create table
                    table = Table(table_lines)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f6f8fa')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#24292e')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#d0d7de')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f6f8fa')])
                    ]))
                    flowables.append(table)
                    flowables.append(Spacer(1, 0.1 * inch))
            
            # Regular paragraphs
            else:
                if line.strip():
                    # Handle inline code
                    text = line.strip()
                    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#24292e">\1</font>', text)
                    # Handle bold
                    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
                    # Handle italic
                    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
                    
                    flowables.append(Paragraph(text, self.styles['CustomBody']))
            
            i += 1
        
        return flowables


class PDFGenerator:
    """Generate professional PDFs from code documentation using ReportLab."""
    
    def __init__(self):
        """Initialize PDF generator."""
        self.parser = MarkdownToReportLab()
    
    def _create_cover_page(self, project_name: str) -> list:
        """Create cover page flowables"""
        flowables = []
        
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            name='CoverTitle',
            parent=styles['Title'],
            fontSize=32,
            textColor=HexColor('#1a1a1a'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=HexColor('#6a737d'),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica'
        )
        
        info_style = ParagraphStyle(
            name='CoverInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#959da5'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        note_style = ParagraphStyle(
            name='CoverNote',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#959da5'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            spaceAfter=10
        )
        
        # Add spacing to center content
        flowables.append(Spacer(1, 2.5 * inch))
        
        # Title
        flowables.append(Paragraph(project_name, title_style))
        
        # Subtitle
        flowables.append(Paragraph("Code Documentation", subtitle_style))
        
        # Add more spacing
        flowables.append(Spacer(1, 1.5 * inch))
        
        # Date
        current_date = datetime.now().strftime("%B %d, %Y")
        flowables.append(Paragraph(f"Generated: {current_date}", info_style))
        
        flowables.append(Spacer(1, 0.3 * inch))
        
        # Note about diagrams
        flowables.append(Paragraph(
            "📊 Interactive diagrams are available in the markdown export and web interface",
            note_style
        ))
        
        # Page break after cover
        flowables.append(PageBreak())
        
        return flowables
    
    def generate_pdf(
        self,
        markdown_content: str,
        output_path: str,
        project_name: str = "Project"
    ) -> str:
        """
        Generate PDF from markdown content.
        
        Args:
            markdown_content: Markdown text to convert
            output_path: Path where PDF should be saved
            project_name: Name of the project for cover page
        
        Returns:
            Path to generated PDF file
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            
            # Add cover page
            story.extend(self._create_cover_page(project_name))
            
            # Parse and add markdown content
            story.extend(self.parser.parse_markdown(markdown_content))
            
            # Build PDF
            doc.build(story)
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate PDF: {str(e)}")
    
    def generate_pdf_bytes(
        self,
        markdown_content: str,
        project_name: str = "Project"
    ) -> bytes:
        """
        Generate PDF as bytes without saving to disk.
        
        Args:
            markdown_content: Markdown text to convert
            project_name: Name of the project for cover page
        
        Returns:
            PDF file as bytes
        """
        try:
            # Create buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            
            # Add cover page
            story.extend(self._create_cover_page(project_name))
            
            # Parse and add markdown content
            story.extend(self.parser.parse_markdown(markdown_content))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Validate PDF
            if not pdf_bytes or not pdf_bytes.startswith(b'%PDF'):
                raise RuntimeError("Generated PDF is invalid or empty")
            
            if len(pdf_bytes) < 1000:
                raise RuntimeError(f"Generated PDF is suspiciously small: {len(pdf_bytes)} bytes")
            
            return pdf_bytes
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate PDF: {str(e)}")
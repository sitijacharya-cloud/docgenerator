import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from html.parser import HTMLParser
from pathlib import Path
import re


class HTMLToReportLab(HTMLParser):
    """Convert HTML to ReportLab flowables."""
    
    def __init__(self, styles):
        super().__init__()
        self.styles = styles
        self.story = []
        self.current_text = []
        self.current_style = 'BodyText'
        self.in_pre = False
        self.in_code = False
        self.table_data = []
        self.current_row = []
        self.in_table = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.current_style = 'Heading1'
        elif tag == 'h2':
            self.current_style = 'Heading2'
        elif tag == 'h3':
            self.current_style = 'Heading3'
        elif tag == 'p':
            self.current_style = 'BodyText'
        elif tag == 'pre':
            self.in_pre = True
        elif tag == 'code':
            self.in_code = True
        elif tag == 'table':
            self.in_table = True
            self.table_data = []
        elif tag == 'tr':
            self.current_row = []
        elif tag in ['td', 'th']:
            pass
        elif tag == 'br':
            self.current_text.append('<br/>')
            
    def handle_endtag(self, tag):
        text = ''.join(self.current_text).strip()
        
        if tag in ['h1', 'h2', 'h3', 'p']:
            if text:
                self.story.append(Paragraph(text, self.styles[self.current_style]))
                self.story.append(Spacer(1, 0.2*cm))
            self.current_text = []
            self.current_style = 'BodyText'
        elif tag == 'pre':
            if text:
                self.story.append(Preformatted(text, self.styles['Code']))
                self.story.append(Spacer(1, 0.3*cm))
            self.current_text = []
            self.in_pre = False
        elif tag == 'code' and not self.in_pre:
            self.in_code = False
        elif tag == 'tr':
            if self.current_row:
                self.table_data.append(self.current_row)
            self.current_row = []
        elif tag in ['td', 'th']:
            if text:
                self.current_row.append(text)
            self.current_text = []
        elif tag == 'table':
            if self.table_data:
                table = Table(self.table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                self.story.append(table)
                self.story.append(Spacer(1, 0.5*cm))
            self.in_table = False
            self.table_data = []
            
    def handle_data(self, data):
        if data.strip():
            self.current_text.append(data)


class PDFGenerator:
    """Generate PDF from markdown documentation."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='Code',
            parent=self.styles['Code'],
            fontName='Courier',
            fontSize=9,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#f4f4f4'),
            borderPadding=10,
        ))
        
        # Update existing styles
        self.styles['Heading1'].textColor = colors.HexColor('#2c3e50')
        self.styles['Heading1'].fontSize = 24
        self.styles['Heading1'].spaceAfter = 12
        
        self.styles['Heading2'].textColor = colors.HexColor('#34495e')
        self.styles['Heading2'].fontSize = 18
        self.styles['Heading2'].spaceAfter = 10
        self.styles['Heading2'].spaceBefore = 20
        
        self.styles['Heading3'].textColor = colors.HexColor('#7f8c8d')
        self.styles['Heading3'].fontSize = 14
        self.styles['Heading3'].spaceAfter = 8
    
    def generate_pdf(self, markdown_content: str, output_path: str) -> str:
        """Generate PDF from markdown content."""
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['extra', 'codehilite', 'tables', 'toc']
            )
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Parse HTML and convert to ReportLab flowables
            parser = HTMLToReportLab(self.styles)
            parser.feed(html_content)
            
            # Build PDF
            doc.build(parser.story)
            
            return output_path
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise
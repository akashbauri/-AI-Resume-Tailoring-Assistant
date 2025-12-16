import markdown
import pdfkit
from io import BytesIO
import os
import tempfile

def markdown_to_ats_pdf(markdown_file_path):
    """
    Convert markdown resume to ATS-friendly PDF
    
    Args:
        markdown_file_path: Path to markdown file
        
    Returns:
        bytes: PDF file as bytes for download
    """
    try:
        # Read markdown content
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'nl2br'])
        
        # ATS-friendly HTML template with simple styling
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0.75in;
                }}
                body {{
                    font-family: 'Arial', 'Helvetica', sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                }}
                h1 {{
                    font-size: 20pt;
                    font-weight: bold;
                    margin-top: 0;
                    margin-bottom: 8pt;
                    text-align: center;
                    color: #000000;
                }}
                h2 {{
                    font-size: 14pt;
                    font-weight: bold;
                    margin-top: 16pt;
                    margin-bottom: 8pt;
                    border-bottom: 2px solid #000000;
                    padding-bottom: 4pt;
                    color: #000000;
                }}
                h3 {{
                    font-size: 12pt;
                    font-weight: bold;
                    margin-top: 12pt;
                    margin-bottom: 6pt;
                    color: #000000;
                }}
                p {{
                    margin-top: 6pt;
                    margin-bottom: 6pt;
                }}
                ul, ol {{
                    margin-top: 6pt;
                    margin-bottom: 6pt;
                    padding-left: 20pt;
                }}
                li {{
                    margin-bottom: 4pt;
                }}
                strong {{
                    font-weight: bold;
                }}
                em {{
                    font-style: italic;
                }}
                a {{
                    color: #0000EE;
                    text-decoration: underline;
                }}
                /* Remove complex layouts */
                table {{
                    display: none;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # PDF options for ATS compatibility
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
            'dpi': 300
        }
        
        # Generate PDF
        pdf_bytes = pdfkit.from_string(html_template, False, options=options)
        
        return pdf_bytes
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        
        # Fallback: Use reportlab for simple text-based PDF
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch,
                                    leftMargin=0.75*inch, rightMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            story = []
            
            # Read markdown and convert to simple text
            with open(markdown_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# '):
                        story.append(Paragraph(line[2:], styles['Heading1']))
                    elif line.startswith('## '):
                        story.append(Paragraph(line[3:], styles['Heading2']))
                    elif line.startswith('### '):
                        story.append(Paragraph(line[4:], styles['Heading3']))
                    elif line:
                        story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as fallback_error:
            print(f"Fallback PDF generation also failed: {str(fallback_error)}")
            return None

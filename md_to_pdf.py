#!/usr/bin/env python3
"""
Convert PRODUCT_BRIEF.md to PDF using reportlab
"""

import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor

def read_markdown(file_path):
    """Read markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_markdown_to_elements(md_content):
    """Parse markdown and convert to reportlab elements"""
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=20,
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=15,
        spaceBefore=25,
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=15,
    )
    
    h4_style = ParagraphStyle(
        'CustomH4',
        parent=styles['Heading4'],
        fontSize=12,
        textColor=HexColor('#555555'),
        spaceAfter=8,
        spaceBefore=12,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=HexColor('#333333'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
    )
    
    # Split content into lines
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            elements.append(Spacer(1, 6))
            i += 1
            continue
        
        # Check for headers
        if line.startswith('# '):
            text = line[2:].strip()
            elements.append(Paragraph(escape_xml(text), title_style))
            elements.append(Spacer(1, 12))
        elif line.startswith('## '):
            text = line[3:].strip()
            elements.append(Paragraph(escape_xml(text), h1_style))
            elements.append(Spacer(1, 10))
        elif line.startswith('### '):
            text = line[4:].strip()
            elements.append(Paragraph(escape_xml(text), h2_style))
            elements.append(Spacer(1, 8))
        elif line.startswith('#### '):
            text = line[5:].strip()
            elements.append(Paragraph(escape_xml(text), h3_style))
            elements.append(Spacer(1, 6))
        elif line.startswith('##### '):
            text = line[6:].strip()
            elements.append(Paragraph(escape_xml(text), h4_style))
            elements.append(Spacer(1, 6))
        elif line.startswith('---'):
            elements.append(Spacer(1, 20))
        elif line.startswith('**') and line.endswith('**'):
            # Bold text
            text = line.strip('*')
            elements.append(Paragraph(f'<b>{escape_xml(text)}</b>', body_style))
        else:
            # Regular paragraph - process markdown formatting
            processed = process_markdown_inline(line)
            elements.append(Paragraph(processed, body_style))
        
        i += 1
    
    return elements

def process_markdown_inline(text):
    """Process inline markdown formatting"""
    # Bold **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic *text*
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Code `text`
    text = re.sub(r'`(.+?)`', r'<font face="Courier"><b>\1</b></font>', text)
    # Escape XML
    text = escape_xml(text)
    return text

def escape_xml(text):
    """Escape XML special characters"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def create_pdf(input_file, output_file):
    """Create PDF from markdown file"""
    print(f"📖 Reading {input_file}...")
    md_content = read_markdown(input_file)
    
    print("🔄 Parsing markdown...")
    elements = parse_markdown_to_elements(md_content)
    
    print(f"📄 Creating PDF: {output_file}...")
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    doc.build(elements)
    print(f"✅ PDF created successfully: {output_file}")

if __name__ == "__main__":
    input_file = "PRODUCT_BRIEF.md"
    output_file = "PRODUCT_BRIEF.pdf"
    
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        exit(1)
    
    try:
        create_pdf(input_file, output_file)
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

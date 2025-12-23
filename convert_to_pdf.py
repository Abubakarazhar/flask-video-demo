#!/usr/bin/env python3
"""
Convert PRODUCT_BRIEF.md to PDF with proper formatting
"""

import os
import sys

def convert_markdown_to_pdf():
    """Convert markdown file to PDF"""
    
    input_file = "PRODUCT_BRIEF.md"
    output_file = "PRODUCT_BRIEF.pdf"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return False
    
    # Read markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Try different conversion methods
    success = False
    
    # Method 1: Try markdown + weasyprint
    try:
        import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables', 'codehilite'])
        
        # Add CSS styling
        css_style = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            font-size: 24pt;
            color: #1a1a1a;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        h2 {
            font-size: 18pt;
            color: #2c3e50;
            border-bottom: 2px solid #34495e;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        h3 {
            font-size: 14pt;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        h4 {
            font-size: 12pt;
            color: #555;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        p {
            margin-bottom: 12px;
            text-align: justify;
        }
        ul, ol {
            margin-bottom: 15px;
            padding-left: 30px;
        }
        li {
            margin-bottom: 8px;
        }
        strong {
            color: #2c3e50;
            font-weight: bold;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            color: #555;
            font-style: italic;
        }
        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #34495e;
            color: white;
            font-weight: bold;
        }
        """
        
        # Wrap HTML content
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Factory Safety Monitoring System - Product Brief</title>
            <style>{css_style}</style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Convert to PDF
        font_config = FontConfiguration()
        HTML(string=full_html).write_pdf(output_file, font_config=font_config)
        
        print(f"✅ Successfully created {output_file} using weasyprint")
        success = True
        
    except ImportError:
        print("⚠️  weasyprint not available, trying alternative method...")
    except Exception as e:
        print(f"⚠️  weasyprint failed: {e}, trying alternative method...")
    
    # Method 2: Try markdown + pdfkit (requires wkhtmltopdf)
    if not success:
        try:
            import markdown
            import pdfkit
            
            # Convert markdown to HTML
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables'])
            
            # Add CSS styling
            css_style = """
            body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6; }
            h1 { font-size: 24pt; color: #1a1a1a; border-bottom: 3px solid #2c3e50; padding-bottom: 10px; }
            h2 { font-size: 18pt; color: #2c3e50; border-bottom: 2px solid #34495e; padding-bottom: 8px; }
            h3 { font-size: 14pt; color: #34495e; }
            """
            
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            pdfkit.from_string(full_html, output_file, options=options)
            
            print(f"✅ Successfully created {output_file} using pdfkit")
            success = True
            
        except ImportError:
            print("⚠️  pdfkit not available, trying alternative method...")
        except Exception as e:
            print(f"⚠️  pdfkit failed: {e}, trying alternative method...")
    
    # Method 3: Try markdown + xhtml2pdf
    if not success:
        try:
            import markdown
            from xhtml2pdf import pisa
            
            # Convert markdown to HTML
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables'])
            
            # Add CSS styling
            css_style = """
            body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6; }
            h1 { font-size: 24pt; color: #1a1a1a; }
            h2 { font-size: 18pt; color: #2c3e50; }
            h3 { font-size: 14pt; color: #34495e; }
            """
            
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            with open(output_file, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(full_html, dest=result_file)
            
            if pisa_status.err:
                raise Exception(f"PDF creation error: {pisa_status.err}")
            
            print(f"✅ Successfully created {output_file} using xhtml2pdf")
            success = True
            
        except ImportError:
            print("⚠️  xhtml2pdf not available...")
        except Exception as e:
            print(f"⚠️  xhtml2pdf failed: {e}")
    
    if not success:
        print("\n❌ Could not convert to PDF. Installing required packages...")
        print("\nPlease run:")
        print("  pip install markdown weasyprint")
        print("\nOr:")
        print("  pip install markdown pdfkit")
        print("  (Note: pdfkit also requires wkhtmltopdf binary)")
        print("\nOr:")
        print("  pip install markdown xhtml2pdf")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Converting PRODUCT_BRIEF.md to PDF...")
    print("")
    success = convert_markdown_to_pdf()
    if success:
        print("")
        print("✅ PDF created successfully!")
        print(f"📄 Output: PRODUCT_BRIEF.pdf")
    else:
        print("")
        print("❌ Conversion failed. Please install required packages.")
        sys.exit(1)

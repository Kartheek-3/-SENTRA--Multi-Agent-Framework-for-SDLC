import os
import zipfile
import re
from xml.sax.saxutils import escape

def markdown_to_docx(md_path, docx_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc_xml_body = []
    
    # Process lines into paragraphs and tables
    in_table = False
    table_rows = []

    for line in lines:
        line_str = line.strip()
        
        # Table handling
        if line_str.startswith('|') and line_str.endswith('|'):
            # Check if separator
            if re.match(r'^\|[\s\-:|]+\|$', line_str):
                continue
            cells = [c.strip() for c in line_str.split('|')[1:-1]]
            if not in_table:
                in_table = True
                table_rows = [cells]
            else:
                table_rows.append(cells)
            continue
        else:
            if in_table:
                # Flush table
                doc_xml_body.append(render_table(table_rows))
                in_table = False
                table_rows = []

        if not line_str:
            continue

        # Headings
        if line_str.startswith('# '):
            text = escape(line_str[2:])
            doc_xml_body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="1E3A8A"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('## '):
            text = escape(line_str[3:])
            doc_xml_body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="1E40AF"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('### '):
            text = escape(line_str[4:])
            doc_xml_body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="1D4ED8"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('#### '):
            text = escape(line_str[5:])
            doc_xml_body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading4"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="2563EB"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('- ') or line_str.startswith('* '):
            text = escape(line_str[2:])
            text = format_bold(text)
            doc_xml_body.append(f'<w:p><w:pPr><w:pStyle w:val="ListBullet"/><w:ind w:left="360"/></w:pPr><w:r><w:t>• {text}</w:t></w:r></w:p>')
        elif re.match(r'^\d+\.\s', line_str):
            m = re.match(r'^(\d+\.)\s(.*)', line_str)
            num = m.group(1)
            text = escape(m.group(2))
            text = format_bold(text)
            doc_xml_body.append(f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t>{num} </w:t></w:r><w:r><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('```'):
            continue
        elif line_str.startswith('> '):
            text = escape(line_str[2:])
            doc_xml_body.append(f'<w:p><w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="3B82F6"/></w:pPr><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:i/><w:color w:val="4B5563"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')
        elif line_str.startswith('---'):
            doc_xml_body.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pPr></w:pPr></w:p>')
        else:
            text = escape(line_str)
            text = format_bold(text)
            doc_xml_body.append(f'<w:p><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr><w:r><w:rPr><w:sz w:val="22"/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr><w:t>{text}</w:t></w:r></w:p>')

    if in_table:
        doc_xml_body.append(render_table(table_rows))

    full_document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <w:body>
        {''.join(doc_xml_body)}
        <w:sectPr>
            <w:pgSz w:w="12240" w:h="15840"/>
            <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
        </w:sectPr>
    </w:body>
</w:document>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    document_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:docDefaults>
        <w:rPrDefault>
            <w:rPr>
                <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
                <w:sz w:val="22"/>
                <w:color w:val="1F2937"/>
            </w:rPr>
        </w:rPrDefault>
    </w:docDefaults>
    <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
        <w:name w:val="Normal"/>
        <w:qFormat/>
    </w:style>
    <w:style w:type="paragraph" w:styleId="Heading1">
        <w:name w:val="heading 1"/>
        <w:qFormat/>
    </w:style>
</w:styles>'''

    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types_xml)
        z.writestr('_rels/.rels', rels_xml)
        z.writestr('word/_rels/document.xml.rels', document_rels_xml)
        z.writestr('word/document.xml', full_document_xml)
        z.writestr('word/styles.xml', styles_xml)

def format_bold(text):
    # Convert **bold** to w:t / w:b elements if necessary, or clean text
    # Simple regex replace for inline text
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    return text

def render_table(rows):
    if not rows:
        return ''
    xml = ['<w:tbl><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="none"/></w:tblBorders></w:tblPr>']
    for i, row in enumerate(rows):
        xml.append('<w:tr>')
        is_header = (i == 0)
        for cell in row:
            clean_cell = format_bold(escape(cell))
            bg_color = 'F1F5F9' if is_header else 'FFFFFF'
            b_tag = '<w:b/>' if is_header else ''
            xml.append(f'''<w:tc>
                <w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{bg_color}"/><w:tcMar><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="180" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tcMar></w:tcPr>
                <w:p><w:r><w:rPr>{b_tag}<w:sz w:val="20"/></w:rPr><w:t>{clean_cell}</w:t></w:r></w:p>
            </w:tc>''')
        xml.append('</w:tr>')
    xml.append('</w:tbl>')
    return ''.join(xml)

if __name__ == '__main__':
    md_file = os.path.join(os.path.dirname(__file__), 'SEAM_FINAL_YEAR_PROJECT_REPORT.md')
    docx_file = os.path.join(os.path.dirname(__file__), 'SEAM_FINAL_YEAR_PROJECT_REPORT.docx')
    print(f'Converting {md_file} to {docx_file}...')
    markdown_to_docx(md_file, docx_file)
    print('Conversion successful!')

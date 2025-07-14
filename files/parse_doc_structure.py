from docx import Document
import re

def extract_headings_and_paragraphs(doc):
    content = []
    for paragraph in doc.paragraphs:
        # 判断段落级别，并按照不同级别处理
        if paragraph.style.name.startswith('Heading'):
            level = int(re.search(r'\d+', paragraph.style.name).group())  # 提取出级别号
            content.append((level, paragraph.text))  # 存储级别和文本
        else:
            content.append(('Paragraph', paragraph.text))  # 存储段落文本
    return content

# 打开文档
file_path = './yonbin/agent/计算机视觉.docx'
doc = Document(file_path)

# 解析文档结构
content = extract_headings_and_paragraphs(doc)

# 打印文档结构
for item in content:
    print(item)
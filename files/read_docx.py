from docx import Document

# 定义文档路径
file_path = './yonbin/agent/计算机视觉.docx'

# 打开文档
try:
    doc = Document(file_path)
    print('文档已成功打开')
except Exception as e:
    print(f'无法打开文档: {e}')
    exit()

# 读取段落内容
print('开始读取文档内容...')
doc_content = [paragraph.text for paragraph in doc.paragraphs]

# 输出文档内容
for line in doc_content:
    print(line)
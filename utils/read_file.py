"""
文件读取函数
"""


def read_file_with_encoding(file_path: str) -> str:
    encodings = ['utf-8-sig', 'gb2312']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue  # 如果解码失败，继续尝试下一种编码
    print(f"错误：{file_path}解码失败")

BLOCK_PATTERN = r"^[\w\-.]+\s*=\s*{"  # 捕获<name> = {<content>}样式的代码块，<name>必须顶行写
CUS_BLOCK_PATTERN = r"{}\s*="  # 自定义的block_pattern
NUMERIC_ATTRIBUTE_PATTERN = r"\s*=\s*([\d\-.]+)"  # 用于捕获数字类型的属性，可以处理负数和小数
NON_NUMERIC_ATTRIBUTE_PATTERN = r"\s*=\s*([\w\-.]+)"


def extract_blocks_to_dict(path: str) -> dict:
    """
    extract_all_blocks的快捷版本，以path为输入，专门处理<str> = {<content>}格式的代码块
    :param path: 文件路径
    :return: <str>：<content>格式的字典
    """
    content = txt_combiner_remove_comment(path)  # 此处会移除注释
    return extract_all_blocks(BLOCK_PATTERN, content, "{")


def extract_one_block(str_name: str, text: str):
    """
    只会提取一个特定的block
    :param str_name: block的name
    :param text: 待提取文本
    :return: 提取出的block
    """
    one_block_pattern = CUS_BLOCK_PATTERN.format(str_name)
    match = re.search(one_block_pattern, text)
    if not match:
        return None
    name, block = extract_bracket_content(text, match.start(), "{")
    return block


def get_numeric_attribute(name: str, text: str):
    """
    输入数字类型属性的名称和待查询文本，输出属性的值
    :param name: 属性的名称
    :param text: 待查询文本
    :return: 属性的值
    """
    if name.startswith("_"):
        start = ""
    else:
        start = "\\b"
    na_pattern = re.compile(f"{start}{name}{NUMERIC_ATTRIBUTE_PATTERN}")
    match = na_pattern.search(text)
    if match:
        return match.group(1)
    else:
        return None


def get_non_numeric_attribute(name: str, text: str):
    if name.startswith("_"):
        start = ""
    else:
        start = "\\b"
    na_pattern = re.compile(f"{start}{name}{NON_NUMERIC_ATTRIBUTE_PATTERN}")
    match = na_pattern.search(text)
    if match:
        return match.group(1)
    else:
        return None

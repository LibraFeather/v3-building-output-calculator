import os
import re

#TODO 旧文件基本可以放弃了
# 文件夹位置
VANILLA_FOLDER = r"E:\\Steam\\steamapps\\common\\Victoria 3\\game"  # 游戏文件位置
MODIFIED_FOLDER = r"input"  # 或者直接设置到mod的路径

# 文件位置
METADATA_PATH = r".metadata\\metadata.json"

# 正则表达式
replace_paths_pattern = re.compile(r"\"replace_paths\"\s*:\s*\[([\d\D]+?)]")
path_pattern = re.compile(r"[\w\-/]+")
block_pattern = (r"^[\w\-.]+\s*=\s*{") # 捕获<name> = {<content>}样式的代码块，<name>必须顶行写
block_pattern_cus = r"{}\s*="  # 自定义的block_pattern
name_pattern = re.compile(r"[\w\-.]+")
numeric_attribute_pattern = (r"\s*=\s*([\d\-.]+)") # 用于捕获数字类型的属性，可以处理负数和小数
non_numeric_attribute_pattern = r"\s*=\s*([\w\-.]+)"
localization_pattern = r"^ [\w\-.]+:.+"
loc_replace_pattern = re.compile(r"\$([\w\-.]+)\$")


def get_list_replace_paths():
    _METADATA_PATH = os.path.join(MODIFIED_FOLDER, METADATA_PATH)
    if os.path.exists(_METADATA_PATH):
        with open(_METADATA_PATH, "r", encoding="utf-8-sig") as f:
            content = f.read()
        match = replace_paths_pattern.search(content)
        if match:
            list_replace_paths = path_pattern.findall(match.group(1))
            for i in range(len(list_replace_paths)):
                list_replace_paths[i] = list_replace_paths[i].replace("/", "\\")
            return list_replace_paths
        else:
            return []
    else:
        return []


list_replace_path = get_list_replace_paths()


def get_file_paths(folder_name):
    file_paths = {}

    input_folder_path = os.path.join(MODIFIED_FOLDER, folder_name)
    if folder_name in list_replace_path:
        if os.path.exists(input_folder_path):
            for root, _, files in os.walk(input_folder_path):
                for file in files:
                    file_paths[file] = os.path.join(root, file)
            return list(file_paths.values())

    # 读取vanilla文件夹内的文件
    VANILLA_FOLDER_path = os.path.join(VANILLA_FOLDER, folder_name)
    for root, _, files in os.walk(VANILLA_FOLDER_path):
        for file in files:
            file_paths[file] = os.path.join(root, file)

    # 检查input文件夹内是否有相同文件并替换

    if os.path.exists(input_folder_path):
        for root, _, files in os.walk(input_folder_path):
            for file in files:
                file_paths[file] = os.path.join(root, file)

    return list(file_paths.values())


def get_input_test_content() -> str:
    """
    将input_test.txt变为字符串，仅用于测试程序运行
    :return : test.txt文件的内容字符串
    """
    with open("input_test.txt", "r", encoding="utf-8-sig") as file:
        test_content = file.read()
    return test_content


def to_output_test_txt(content: str):
    """
    将字符串变为output_test.txt，仅用于测试程序运行
    """
    with open("output_test.txt", "w", encoding="utf-8-sig") as file:
        file.write(content)


def txt_combiner_folder(path: str) -> str:
    """
    组合给定文件夹下的所有非.info文件，然后将他们以字符串类型输出
    :param path: 给定的路径
    :return : 组合后的字符串
    """
    content = ""
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(".info"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content += f.read()
                    # 额外加一个\n，确保位于行首的字符依然位于行首
                    content += "\n"
    return content


def txt_combiner(path: str) -> str:
    """
    组合给定路径下的所有非.info文件，然后将他们以字符串类型输出
    :param path: 给定的路径
    :return : 组合后的字符串
    """
    content = ""
    list_file_path = get_file_paths(path)
    if list_file_path:
        for file_path in list_file_path:
            if not file_path.endswith(".info"):
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content += f.read()
                    # 额外加一个\n，确保位于行首的字符依然位于行首
                    content += "\n"
    else:
        print(f"找不到{path}，请确认游戏路径是否设置正确")
    return content


def txt_combiner_rc(path: str) -> str:
    """
    txt_combiner的移除注释版本，仅移除#后的内容，不要在处理本地化文件的时候使用这个！
    :param path: 给定的路径
    :return: 组合后的字符串
    """
    return re.sub(r"#.*$", "", txt_combiner(path), flags=re.MULTILINE)


def _extract_bracket_content(text: str, start: int, char: str):
    """
    提取给定字符之间的内容
    :param text: 待检索文本
    :param start: 字符开始位置
    :param char: 待匹配字符
    :return: 字符之间的字符串（包括两端）
    """
    if char in ["{", "[", "("]:
        open_bracket = char
        close_bracket = {"{": "}", "[": "]", "(": ")"}[char]
        stack = []
        first_open_bracket_pos = -1  # 用于保存第一个open_bracket的位置
        for i in range(start, len(text)):
            if text[i] == open_bracket:
                if first_open_bracket_pos == -1:
                    first_open_bracket_pos = i
                stack.append(i)
            elif text[i] == close_bracket:
                stack.pop()
                if not stack:
                    return (
                        text[start : first_open_bracket_pos - 1],
                        text[first_open_bracket_pos + 1 : i],
                    )  # 不包括两端的括号
    elif char in ['"', "'"]:
        first_quote_pos = text.find(char, start)  # 捕获第一个引号的位置
        if first_quote_pos != -1:
            end = text.find(char, first_quote_pos + 1)
            if end != -1:
                return (
                    text[start : first_quote_pos - 1],
                    text[first_quote_pos + 1 : end],
                )
    return None


def extract_all_blocks(pattern: str, text: str, char: str) -> dict:
    """
    提取<str> = {<content>}格式的代码块
    对于{、[或(，会匹配第一个匹配的}、]或)，"或'则只会匹配下一个"或'
    以<str>：<content>的字典形式返回
    :param pattern: 代码块开头<str> = {的格式
    :param text: 待检索的文本
    :param char: 待配对的字符类型，只能是{、[、(、"或‘
    :return: <str>：<content>格式的字典
    """
    dict_block = {}
    for match in re.finditer(pattern, text, re.MULTILINE):
        name, block = _extract_bracket_content(text, match.start(), char)
        name = (
            name_pattern.search(name).group(0) if name_pattern.search(name) else "None"
        )
        if block:
            if name in dict_block.keys():
                print(f"{name}重复出现")
            dict_block[name] = block
    return dict_block


def extract_blocks_to_dict(path: str) -> dict:
    """
    extract_all_blocks的快捷版本，以path为输入，专门处理<str> = {<content>}格式的代码块
    :param path: 文件路径
    :return: <str>：<content>格式的字典
    """
    content = txt_combiner_rc(path)  # 此处会移除注释
    return extract_all_blocks(block_pattern, content, "{")


def extract_one_block(str_name: str, text):
    one_block_pattern = block_pattern_cus.format(str_name)
    match = re.search(one_block_pattern, text)
    if not match:
        return None
    name, block = _extract_bracket_content(text, match.start(), "{")
    return block


def search_numeric_attribute(name: str, text: str):
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
    na_pattern = re.compile(f"{start}{name}{numeric_attribute_pattern}")
    match = na_pattern.search(text)
    if match:
        return match.group(1)
    else:
        return None


def search_non_numeric_attribute(name: str, text: str):
    if name.startswith("_"):
        start = ""
    else:
        start = "\\b"
    na_pattern = re.compile(f"{start}{name}{non_numeric_attribute_pattern}")
    match = na_pattern.search(text)
    if match:
        return match.group(1)
    else:
        return None


class Localization:
    def __init__(self, path):
        """
        :param path: 本地化文件的路径
        """
        self.path = path
        self.dict_all = self._create_dict_all()

    def _create_dict_all(self) -> dict:
        """
        创建一个包含所有本地化键的字典
        """
        content = txt_combiner(self.path)
        dict_loc = extract_all_blocks(localization_pattern, content, '"')
        for key, value in dict_loc.items():
            replace_list = loc_replace_pattern.findall(value)
            for replace in replace_list:
                if replace in dict_loc.keys():
                    value = value.replace(f"${replace}$", dict_loc[replace])
                    # print(f"{key}中的{replace}被替换为{dict_loc[replace]}")
            dict_loc[key] = value
        return dict_loc

    def create_dict_used(self, dict_list_loc: dict) -> dict:
        """
        这部字典仅包含使用的本地化键
        :param dict_list_loc: 使用的本地化键的列表的字典
        """
        dict_used = {}
        list_used = []
        for value in dict_list_loc.values():
            list_used.extend(value)
        for key in list_used:
            if key in self.dict_all:
                dict_used[key] = self.dict_all[key]
            else:
                print(f"找不到{key}的本地化")
                dict_used[key] = key
        return dict_used

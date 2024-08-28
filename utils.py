"""
整个utils文件分成三部分：
1. 从P语言配置文件中提取字符串整体
2. 从字符串中通过正则表达式生成数据
3. 处理生成后数据
"""

# TODO 原本想做成独立于tree.py的通用工具函数，后面想还是算了，直接整合进tree.py里面来，所以这个文件最终也是要被放弃的
import os
import re
import json

from constants.constant import MODFILE_FOLDER, METADATA_PATH, VANILLA_FOLDER, LOGIC_KEYS_LIST, GOODS_PATH, POP_TYPES_PATH
from constants.pattern import REPLACE_PATHS_PATTERN, PATH_PATTERN, BLOCK_PATTERN, BLOCK_PATTERN_CUS, \
                              NAME_PATTERN, NUMERIC_ATTRIBUTE_PATTERN, NON_NUMERIC_ATTRIBUTE_PATTERN, \
                              LOCALIZATION_PATTERN, LOCALIZATION_REPLACE_PATTERN, BLOCK_PATTERN_0, \
                              OPERATOR_PATTERN
from models.model import GoodsInfo, PopTypesInfo


class Utils():
    # def __init__(self) -> None:
    #     self.list_replace_path = ''

    # def get_modfile_replace_paths_list(self):
    #     _METADATA_PATH = os.path.join(MODFILE_FOLDER, METADATA_PATH)
        
    #     if not os.path.exists(_METADATA_PATH): return []

    #     try:
    #         with open(_METADATA_PATH, "r", encoding="utf-8-sig") as f:
    #             content = f.read()
    #     except (IOError, OSError) as e:
    #         print(f"读取文件失败: {_METADATA_PATH}, {e}")
    #         return []

    #     match = re.compile(REPLACE_PATHS_PATTERN).search(content)
    #     if not match: return []

    #     list_replace_paths = [path.replace("/", "\\") for path in re.compile(PATH_PATTERN).findall(match.group(1))]
    #     return list_replace_paths

# ! 第1部分
    def get_config_file_paths(self, folder_name):
        file_paths = {}

        # TODO 等完成了重构再考虑Mod的事情
        # input_folder_path = os.path.join(MODFILE_FOLDER, folder_name)
        # if folder_name in self.list_replace_path and self.list_replace_path != '':
        #     if os.path.exists(input_folder_path):
        #         for root, _, files in os.walk(input_folder_path):
        #             for file in files:
        #                 file_paths[file] = os.path.join(root, file)
        #         return list(file_paths.values())

        # 读取vanilla文件夹内的文件
        vanilla_folder_path = os.path.join(VANILLA_FOLDER, folder_name)
        for root, _, files in os.walk(vanilla_folder_path):
            for file in files:
                file_paths[file] = os.path.join(root, file)

        # 检查input文件夹内是否有相同文件并替换

        # if os.path.exists(input_folder_path):
        #     for root, _, files in os.walk(input_folder_path):
        #         for file in files:
        #             file_paths[file] = os.path.join(root, file)

        return list(file_paths.values())

    def txt_combiner_folder(self, path: str) -> str:
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

    def extract_all_from_config_file_paths(self, path: str) -> str:
        """
        组合给定路径下的所有非.info文件，然后将他们以字符串类型输出
        :param path: 给定的路径
        :return : 组合后的字符串
        """
        content = ""
        list_file_path = self.get_config_file_paths(path)
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

    def extract_all_from_config_file_paths_without_notes(self, path: str) -> str:
        """
        txt_combiner的移除注释版本，仅移除#后的内容，不要在处理本地化文件的时候使用这个！
        :param path: 给定的路径
        :return: 组合后的字符串
        """
        return re.sub(r"#.*$", "", self.extract_all_from_config_file_paths(path), flags=re.MULTILINE)


#! 第2部分
    def _extract_bracket_content(self, text: str, start: int, char: str):
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
                        return text[start:first_open_bracket_pos - 1], text[first_open_bracket_pos + 1:i]  # 不包括两端的括号
        elif char in ["\"", "\'"]:
            first_quote_pos = text.find(char, start)  # 捕获第一个引号的位置
            if first_quote_pos != -1:
                end = text.find(char, first_quote_pos + 1)
                if end != -1:
                    return text[start:first_quote_pos - 1], text[first_quote_pos + 1:end]
        return None


    def extract_all_blocks(self, pattern: str, text: str, char: str) -> dict:
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
            name, block = self._extract_bracket_content(text, match.start(), char)
            name = re.compile(NAME_PATTERN).search(name).group(0) if re.compile(NAME_PATTERN).search(name) else "None"
            if block:
                if name in dict_block.keys():
                    print(f"{name}重复出现")
                dict_block[name] = block
        return dict_block

    def extract_blocks_to_dict(self, path: str) -> dict:
        """
        extract_all_blocks的快捷版本，以path为输入，专门处理<str> = {<content>}格式的代码块
        :param path: 文件路径
        :return: <str>：<content>格式的字典
        """
        content = self.extract_all_from_config_file_paths_without_notes(path)  # 此处会移除注释
        return self.extract_all_blocks(BLOCK_PATTERN_0, content, "{")

    def extract_one_block(self, str_name: str, text: str):
        """
        只会提取一个特定的block
        :param str_name: block的name
        :param text: 待提取文本
        :return: 提取出的block
        """
        one_block_pattern = BLOCK_PATTERN_CUS.format(str_name)
        match = re.search(one_block_pattern, text)
        if not match:
            return None
        name, block = self._extract_bracket_content(text, match.start(), "{")
        return block

    def get_numeric_attribute(self, name: str, text: str):
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

    def get_non_numeric_attribute(self, name: str, text: str):
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

#! 第3部分
# ------------------------------------------------------------------------------------------
# 以下函数用于通过递归方法获得递归字典
    def find_first_operator(self, s: str, start=0):
        """
        寻找operator的位置
        :param s: 待查询字符串
        :param start: 起始位置
        :return: 返回operator，开始位置和结束位置
        """
        # 搜索第一个匹配项
        match = re.compile(OPERATOR_PATTERN).search(s[start:])
        if match:
            operator = match.group()
            start_pos = match.start() + start  # 相对位置，所以要加上start
            end_pos = match.end() + start
            return operator, start_pos, end_pos
        else:
            return None, -1, -1


    def convert_to_number(self, value: str):
        """
        尝试将字符串转换为数值类型
        :param value: 待转换的字符串
        :return: 转换后的数值或原字符串
        """
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value


    def parse_text_block(self, start: int, text: str) -> tuple:
        """
        解析文本的一个block，返回block名称、内容和新的起始位置
        :param text: 待处理文本
        :param start: 开始位置
        :return: block名称、内容和新的起始位置
        """

        def find_bracket_content(_start: int) -> tuple:
            """
            查找并返回从指定位置开始的花括号内的内容
            :param _start: 开始位置
            :return: 花括号内的内容和新的起始位置
            """
            stack = []
            for k in range(_start, len(text)):
                if text[k] == "{":
                    stack.append(k)
                elif text[k] == "}":
                    stack.pop()
                    if not stack:
                        return text[_start + 1:k], k + 1  # 不包括两端的括号
            print(f"文件出现花括号不匹配")
            return text[_start + 1:], len(text) + 1  # 如果花括号不匹配，输出后面全部的文件

        operator, operator_start, operator_end = self.find_first_operator(text, start)
        if operator is not None:
            name = text[start:operator_start].strip() + (f".[{operator}]" if operator != "=" else "")  # 记录符号
            for i in range(operator_end, len(text)):
                if text[i] == "{":
                    match_indicator = re.compile(NAME_PATTERN).search(text[operator_end:i])
                    if match_indicator:
                        name += f".[{match_indicator.group(0)}]"  # 这一段是用来处理颜色的
                    content, new_start = find_bracket_content(i)
                    return name, content, new_start
                elif text[i] == "\n":
                    content = text[operator_end: i].strip()
                    new_start = i + 1
                    return name, content, new_start
            content = text[operator_end:].strip()
            new_start = len(text) + 1
            return name, content, new_start
        # print("easytool.auto_text_divider_part运行异常")
        return "", "", len(text) + 1


    def divide_text_into_dict(self, text, override=True) -> dict:
        """
        将文本分割成不同的部分，并存储在字典中
        :param override: 重复的value是否覆盖
        :param text: 待分割文本
        :return: block名称和内容的字典
        """
        text = re.sub(r"#.*$", "", text, flags=re.MULTILINE)
        start = 0
        dict_blocks = {}
        dict_logic_key = {logic_key: -1 for logic_key in LOGIC_KEYS_LIST}
        while start < len(text):  # parse_text_block会返回下一个block的开始位置，如果开始位置比文件长度还长，那么终止循环
            key, value, start = self.parse_text_block(start, text)
            if key in LOGIC_KEYS_LIST:
                dict_logic_key[key] += 1
                key = f"{key}.[{dict_logic_key[key]}]"
            if key:  # 防止异常值进入字典，这里认为value可以为空
                if key in dict_blocks:
                    if override:
                        print(f"{key}重复出现，新值将会覆盖旧值")
                        dict_blocks[key] = self.convert_to_number(value)
                    else:  # 把新值加在旧值后面
                        if isinstance(dict_blocks[key], list):
                            dict_blocks[key].append(value)
                        else:
                            dict_blocks[key] = [dict_blocks[key], value]
                else:
                    dict_blocks[key] = self.convert_to_number(value)
        return dict_blocks

    def divide_text_into_dict_from_path(self, path: str, override=True) -> dict:
        """
        将文本分割成不同的部分，并存储在字典中
        :param path: 待处理的路径
        :param override: 重复的value是否覆盖
        :return: block名称和内容的字典
        """
        list_file_paths = self.get_config_file_paths(path)  # 获取所有的路径
        dict_blocks = {}
        for file_path in list_file_paths:
            if not file_path.endswith(".info"):  # 忽略info文件
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                content = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
                start = 0
                dict_logic_key = {logic_key: -1 for logic_key in LOGIC_KEYS_LIST}
                while start < len(content):  # parse_text_block会返回下一个block的开始位置，如果开始位置比文件长度还长，那么终止循环
                    key, value, start = self.parse_text_block(start, content)
                    if key in LOGIC_KEYS_LIST:
                        dict_logic_key[key] += 1
                        key = f"{key}.[{dict_logic_key[key]}]"
                    if key:  # 防止异常值进入字典，这里认为value可以为空
                        if key in dict_blocks:
                            if override:
                                print(f"{key}重复出现，新值将会覆盖旧值")
                                dict_blocks[key] = self.convert_to_number(value)
                            else:  # 把新值加在旧值后面
                                if isinstance(dict_blocks[key], list):
                                    dict_blocks[key].append(value)
                                else:
                                    dict_blocks[key] = [dict_blocks[key], value]
                        else:
                            dict_blocks[key] = self.convert_to_number(value)
        return dict_blocks

    def divide_dict_value(self, dict_block: dict) -> dict:
        """
        递归函数，进一步对dict的value进行解析
        :param dict_block: 待解析的dict
        :return: 递归解析后的dict
        """

        def process_content(content):
            """
            处理字符串内容，递归解析或分割为列表
            :param content: 待处理的字符串内容
            :return: 处理后的内容
            """
            if any(op in content for op in ("<", "=", ">")):
                return self.divide_dict_value(self.divide_text_into_dict(content, False))
            match_whitespace = re.search(r"\s", content)
            if match_whitespace:
                return [self.convert_to_number(item) for item in re.compile(NAME_PATTERN).findall(content)]
            return content

        for key, value in dict_block.items():
            if isinstance(value, str):
                dict_block[key] = process_content(value)
            elif isinstance(value, list):
                dict_block[key] = [process_content(item) if isinstance(item, str) else item for item in value]
        return dict_block

    def get_nested_dict_from_path(self, path: str, override=True) -> dict:
        """
        从路径获取嵌套字典
        :param path: 路径
        :param override: 新值是否覆盖旧值
        :return: 嵌套字典
        """
        nested_dict = self.divide_text_into_dict_from_path(path, override)
        nested_dict = self.divide_dict_value(nested_dict)
        return nested_dict

    def _create_goods_info(self) -> dict:
        """
        创建一个储存商品名称和基础价格信息的字典
        :return: 储存商品名称和基础价格信息的字典
        """
        dict_good_blocks = Utils.extract_blocks_to_dict(self, GOODS_PATH)
        dict_good = {}
        for good, good_block in dict_good_blocks.items():
            cost = Utils.get_numeric_attribute(self, "cost", good_block)
            if cost is None:
                print(f"找不到{good}的基础价格，因此{good}将被忽略")
                continue
            # 价格是整数，为了兼容性考虑，这里记为浮点数
            dict_good[good] = float(cost)
        return dict_good
# ------------------------------------------------------------------------------------------
# 以下为处理本地化的类
class Localization:
    """
    用于处理本地化
    """

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
        content = Utils.extract_all_from_config_file_paths(self.path)
        dict_loc = Utils.extract_all_blocks(LOCALIZATION_PATTERN, content, "\"")
        for key, value in dict_loc.items():
            replace_list = re.compile(LOCALIZATION_REPLACE_PATTERN).findall(value)
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

# ------------------------------------------------------------------------------------------
# 以下为测试函数
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


def find_value(value_0, dict_0: dict):
    list_keys = []
    for key, value in dict_0.items():
        if key == value_0:
            list_keys.append(key)
        elif value == value_0:
            list_keys.append(key)
        elif isinstance(value, list):
            for x in value:
                if isinstance(x, dict):
                    has_value = find_value(value_0, x)
                    if has_value:
                        list_keys.append(key)
        elif isinstance(value, dict):
            has_value = find_value(value_0, value)
            if has_value:
                list_keys.append(key)
    return list_keys


if __name__ == '__main__':
    a = Utils()
    a.get_config_file_paths(GOODS_PATH)
    # a.txt_combiner(r'E:\\Jeux\\Codes\\Victoria3\building_output_calculator\\input\\common\\production_methods')
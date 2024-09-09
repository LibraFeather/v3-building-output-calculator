# ------------------------------------------------------------------------------------------

# 文本提取函数

# ------------------------------------------------------------------------------------------
import re
import utils.pathproc as pp
import utils.error as error
import utils.read_file as rf

# 正则表达式
OPERATOR_PATTERN = re.compile(r"(<|<=|=|>=|>)")
LOCALIZATION_PATTERN = re.compile(r"^\s+[\w\-.]+:.+", re.MULTILINE)
LOCALIZATION_REPLACE_PATTERN = re.compile(r"\$([\w\-.]+)\$")

GOOD_MODIFIER_PATTERN = re.compile(r"\bgoods_(?P<io_type>input|output)_(?P<key_word>[\w\-]+?)_(?P<am_type>add|mult)\b")
BUILDING_EMPLOYMENT_MODIFIER_PATTERN = re.compile(
    r"\bbuilding_employment_(?P<key_word>[\w\-]+?)_(?P<am_type>add|mult)\b")
BUILDING_SUBSISTENCE_OUTPUT_MODIFIER_PATTERN = re.compile(r"\bbuilding_subsistence_output_(?P<am_type>add|mult)\b")

# 其他变量
LIST_LOGIC_KEYS = ['if', 'else_if', 'else', 'add', 'multiply', 'divide']


# ------------------------------------------------------------------------------------------
# 以下函数专门处理本地化
def parse_yaml_line(line):
    # 查找冒号位置，分割键和值
    parts = line.split(':', 1)
    if len(parts) == 2:
        key = parts[0].strip()
        value = parts[1].strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return key, value
    return None, None


def extract_localization_blocks(yaml_content: str, localization_dict=None) -> dict:
    if localization_dict is None:
        localization_dict = {}

    lines = yaml_content.split('\n')

    for line in lines:
        new_line = []
        in_single_quote = False
        in_double_quote = False
        for char in line:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            if not in_single_quote and not in_double_quote and char == '#':
                break
            new_line.append(char)

        # 处理行的其余部分（如果存在）
        new_line = ''.join(new_line).rstrip()
        if new_line:
            name, block = parse_yaml_line(new_line)
            if block:
                if name in localization_dict.keys():
                    pass
                else:
                    localization_dict[name] = block
    return localization_dict


def get_localization_dict() -> dict:
    localization_dict = {}
    localization_paths_list = pp.get_localization_paths()
    for localization_path in localization_paths_list:
        text = rf.read_file_with_encoding(localization_path)
        extract_localization_blocks(text, localization_dict)
    return localization_dict


def calibrate_localization_dict(localization_dict_used: dict, localization_dict_all: dict):
    for key, value in localization_dict_used.items():
        replace_list = LOCALIZATION_REPLACE_PATTERN.findall(value)
        if replace_list:
            for replace in replace_list:
                if replace in localization_dict_all.keys():
                    value = value.replace(f"${replace}$", localization_dict_all[replace])
            localization_dict_used[key] = value


# ------------------------------------------------------------------------------------------
# 以下函数用于通过递归方法获得递归字典
def find_first_operator(text: str, start=0) -> tuple:
    """
    寻找operator的位置
    :param text: 待查询字符串
    :param start: 起始位置
    :return: 返回operator，开始位置和结束位置
    """
    # 搜索第一个匹配项
    match = OPERATOR_PATTERN.search(text[start:])
    if not match:
        return None, -1, -1
    operator = match.group()
    start_pos = match.start() + start  # 相对位置，所以要加上start
    end_pos = match.end() + start
    return operator, start_pos, end_pos


def convert_to_number(value: str) -> int | float | str:
    """
    尝试将字符串转换为数值类型
    """
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_text_block(start: int, text: str, file_path: str) -> tuple:
    """
    解析文本的一个block，返回block名称、内容和新的起始位置
    :param text: 待处理文本
    :param start: 开始位置
    :param file_path: 文件路径
    :return: block名称、内容和新的起始位置
    """

    def parse_bracket_content(_start: int) -> tuple:
        """
        查找并返回从指定位置开始的花括号内的内容
        :param _start: 开始位置
        :return: 花括号内的内容和新的起始位置
        """
        stack = []
        for k in range(_start, len_text):
            if text[k] == '{':
                stack.append(k)
            elif text[k] == '}':
                stack.pop()
                if not stack:
                    return " " + text[_start + 1:k], k + 1  # 不包括两端的括号
        if file_path is not None:
            print(f"错误：{file_path}花括号不匹配")
        else:
            print(f"错误：文件花括号不匹配")
        return text[_start + 1:], len_text + 1  # 如果花括号不匹配，输出后面全部的文件

    def parse_quotation_mark_content(_start: int) -> tuple:
        for k in range(_start + 1, len_text):  # 跳过第一个引号，只需要知道第二个引号的位置
            if text[k] == '"':
                return text[_start:k + 1], k + 1  # 包括两端的引号
            elif text[k] == '\n':
                print("提醒：引号包裹的内容疑似出现跨行，可能导致异常")
                return text[_start:k], k + 1  # 假定引号内容不会换行

    operator, operator_start, operator_end = find_first_operator(text, start)
    len_text = len(text)
    if operator is None:
        return '', '', len_text + 1
    name = text[start:operator_start].strip() + (f".[{operator}]" if operator != '=' else '')  # 记录符号，除非是等号
    first_non_space = re.search(r"\S+", text[operator_end:len_text])
    if first_non_space is None:
        return name, '', len_text + 1
    first_non_space_start = operator_end + first_non_space.start()
    first_non_space_end = operator_end + first_non_space.end()
    bracket = re.search(r"\{", first_non_space.group())
    if first_non_space.group()[0] == '@':
        content = re.search(r".*", text[first_non_space_start:len_text])
        return name, content.group(), first_non_space_start + content.end()
    if bracket:
        bracket_start = first_non_space_start + bracket.start()
        name += f".[{text[first_non_space_start:bracket_start]}]" if text[first_non_space_start:bracket_start] else ''
        return name, *parse_bracket_content(bracket_start)
    if first_non_space.group()[0] == '"':
        return name, *parse_quotation_mark_content(first_non_space_start)
    second_non_space = re.search(r"\S+", text[first_non_space_end:len_text])
    if second_non_space is None:
        return name, first_non_space.group(), len_text + 1
    second_non_space_start = first_non_space_end + second_non_space.start()
    if second_non_space.group()[0] == '{':
        name += f".[{first_non_space.group()}]"
        return name, *parse_bracket_content(second_non_space_start)
    return name, first_non_space.group(), second_non_space_start


def convert_text_into_dict(text: str, blocks_dict=None, logic_keys_dict=None, override=True, file_path=None) -> dict:
    if blocks_dict is None:
        blocks_dict = {}
    if logic_keys_dict is None:
        logic_keys_dict = {logic_key: -1 for logic_key in LIST_LOGIC_KEYS}
    text = re.sub(r"#.*$", '', text, flags=re.MULTILINE)
    start = 0
    while start < len(text):
        key, value, start = parse_text_block(start, text, file_path)
        if not key:
            continue
        value = convert_to_number(value)
        if key in LIST_LOGIC_KEYS:
            logic_keys_dict[key] += 1
            key = f"{key}.[{logic_keys_dict[key]}]"
            blocks_dict[key] = value
            continue
        if key not in blocks_dict:
            blocks_dict[key] = value
            continue
        if override:
            print(f"提醒：{key}重复出现，新值将会覆盖旧值")
            blocks_dict[key] = value
            continue
        if isinstance(blocks_dict[key], list):
            blocks_dict[key].append(value)
            continue
        blocks_dict[key] = [blocks_dict[key], value]
    return blocks_dict


def convert_text_into_dict_from_path(path: str, override=True) -> dict:
    """
    将文本分割成不同的部分，并存储在字典中
    :param path: 待处理的路径
    :param override: 重复的value是否覆盖
    :return: block名称和内容的字典
    """
    list_file_paths = pp.get_file_paths_list(path)  # 获取所有的路径
    blocks_dict = {}
    logic_keys_dict = {logic_key: -1 for logic_key in LIST_LOGIC_KEYS}
    for file_path in list_file_paths:  # 对文件分别进行处理，以防止格式错误造成污染
        if not file_path.endswith('.info'):  # 忽略info文件，这个文件的作用类似注释
            text = rf.read_file_with_encoding(file_path)
            convert_text_into_dict(text, blocks_dict, logic_keys_dict, override, file_path)
    return blocks_dict


def divide_dict_value(blocks_dict: dict) -> dict:
    """
    递归函数，进一步对dict的value进行解析
    :param blocks_dict: 待解析的dict
    :return: 递归解析后的dict
    """

    def process_content(content) -> str | list | dict:
        """
        处理字符串内容，递归解析或分割为列表
        """
        if not content.strip():  # 内容为空时，返回一个空字典
            return {}
        if content[0] in ['"', '@']:
            return content
        if any(op in content for op in ('<', '=', '>')):  # 这里通过这三个符号判断是否能够进一步解析
            return get_nested_dict_from_text(content, override=False)
        match_whitespace = re.search(r"\s", content)
        if match_whitespace is None:
            return content
        return [convert_to_number(item) for item in re.findall(r"\S+", content)]

    for key, value in blocks_dict.items():
        if isinstance(value, str):
            blocks_dict[key] = process_content(value)
        elif isinstance(value, list):
            blocks_dict[key] = [process_content(item) if isinstance(item, str) else item for item in value]
    return blocks_dict


def get_nested_dict_from_path(path: str, override=True) -> dict:
    """
    从路径获取嵌套字典
    :param path: 路径
    :param override: 新值是否覆盖旧值
    :return: 嵌套字典
    """
    nested_dict = convert_text_into_dict_from_path(path, override)
    nested_dict = divide_dict_value(nested_dict)
    return nested_dict


def get_nested_dict_from_text(text: str, override=True) -> dict:
    nested_dict = convert_text_into_dict(text, override=override)
    nested_dict = divide_dict_value(nested_dict)
    return nested_dict


# ------------------------------------------------------------------------------------------
# 以下函数用于解析modifier
def wrong_format(modifier_name: str):
    error.can_not_parse(modifier_name)


def parse_good_modifier(modifier: str) -> dict | None:
    modifier_match = GOOD_MODIFIER_PATTERN.match(modifier)
    if modifier_match is None:
        return wrong_format(modifier)
    else:
        return {
            'category': 'goods',
            'key_word': modifier_match.group('key_word'),
            'io_type': modifier_match.group('io_type'),
            'am_type': modifier_match.group('am_type')
        }


def parse_building_modifier(modifier: str) -> dict:  # TODO 这个函数仅能识别buildings_employment_开头的modifier，之后也许可以升级
    modifier_match = BUILDING_EMPLOYMENT_MODIFIER_PATTERN.match(modifier)
    if modifier_match is not None:
        return {
            'category': ('building', 'employment'),
            'key_word': modifier_match.group('key_word'),
            'am_type': modifier_match.group('am_type')
        }
    modifier_match = BUILDING_SUBSISTENCE_OUTPUT_MODIFIER_PATTERN.match(modifier)
    if modifier_match is not None:
        return {
            'category': ('building', 'subsistence_output'),
            'am_type': modifier_match.group('am_type')
        }


def parse_modifier(modifier: str) -> dict | None:
    split_list = modifier.split('_')
    if len(split_list) < 3:  # modifier应该至少3个单位长
        return wrong_format(modifier)

    match split_list[0]:
        case 'goods':
            return parse_good_modifier(modifier)
        case 'building':
            return parse_building_modifier(modifier)
        case 'unit':  # 为了防止报错
            return None
        case _:
            return wrong_format(modifier)


def parse_modifier_dict(modifier_dict: dict) -> dict:
    modifier_info_dict = {}
    for modifier, value in modifier_dict.items():
        modifier_info = parse_modifier(modifier)
        if modifier_info is None:
            continue
        if not isinstance(value, (int, float)):
            error.wrong_type(modifier, '数值')
            continue
        modifier_info['value'] = value
        modifier_info_dict[modifier] = modifier_info
    return modifier_info_dict


def calibrate_modifier_dict(modifier_dict: dict) -> dict:
    for modifier, value in modifier_dict.items():
        if isinstance(value, list):
            modifier_dict[modifier] = float(sum(value))
    return modifier_dict


# ------------------------------------------------------------------------------------------

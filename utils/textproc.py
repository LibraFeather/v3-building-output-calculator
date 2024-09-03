# ------------------------------------------------------------------------------------------

# 文本提取函数

# ------------------------------------------------------------------------------------------
import re
import utils.pathproc as pp

# 正则表达式
NAME_PATTERN = re.compile(r"[\w\-.]+")
OPERATOR_PATTERN = re.compile(r"(<|<=|=|>=|>)")

GOOD_MODIFIER_PATTERN = re.compile(r"\bgoods_(?P<io_type>input|output)_(?P<key_word>[\w\-]+?)_(?P<am_type>add|mult)\b")
BUILDING_EMPLOYMENT_MODIFIER_PATTERN = re.compile(
    r"\bbuilding_employment_(?P<key_word>[\w\-]+?)_(?P<am_type>add|mult)\b")

# 其他变量
list_logic_keys = ["if", "else_if", "else", "add", "multiply", "divide"]


def txt_combiner(path: str) -> str:
    content = ""
    file_paths_list = pp.get_file_paths_list(path)
    if file_paths_list:
        for file_path in file_paths_list:
            if not file_path.endswith(".info"):
                with open(file_path, "r", encoding="utf-8-sig") as file:
                    content += file.read() + "\n"
    else:
        print(f"找不到{path}，请确认路径是否设置正确")
    return content


def txt_combiner_remove_comment(path: str) -> str:
    """
    txt_combiner的移除注释版本，仅移除#后的内容，不要在处理本地化文件的时候使用这个！
    """
    return re.sub(r"#.*$", "", txt_combiner(path), flags=re.MULTILINE)


def extract_bracket_content(text: str, start: int, char: str):
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
        name, block = extract_bracket_content(text, match.start(), char)
        name = NAME_PATTERN.search(name).group(0) if NAME_PATTERN.search(name) else "None"
        if block:
            if name in dict_block.keys():
                print(f"{name}重复出现")
            dict_block[name] = block
    return dict_block


# ------------------------------------------------------------------------------------------
# 以下函数用于通过递归方法获得递归字典
def find_first_operator(s: str, start=0):
    """
    寻找operator的位置
    :param s: 待查询字符串
    :param start: 起始位置
    :return: 返回operator，开始位置和结束位置
    """
    # 搜索第一个匹配项
    match = OPERATOR_PATTERN.search(s[start:])
    if match:
        operator = match.group()
        start_pos = match.start() + start  # 相对位置，所以要加上start
        end_pos = match.end() + start
        return operator, start_pos, end_pos
    else:
        return None, -1, -1


def convert_to_number(value: str):
    """
    尝试将字符串转换为数值类型
    """
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        return value


def parse_text_block(start: int, text: str) -> tuple:
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
        for k in range(_start, len_text):
            if text[k] == "{":
                stack.append(k)
            elif text[k] == "}":
                stack.pop()
                if not stack:
                    return text[_start + 1:k], k + 1  # 不包括两端的括号
        print(f"文件出现花括号不匹配")
        return text[_start + 1:], len_text + 1  # 如果花括号不匹配，输出后面全部的文件

    def find_quotation_mark(_start: int) -> tuple:
        for k in range(_start + 1, len_text):  # 跳过第一个引号，只需要知道第二个引号的位置
            if text[k] == "\"":
                return text[_start:k + 1], k + 1  # 包括两端的引号
            elif text[k] == "\n":
                print("引号包裹的内容疑似出现跨行，可能导致异常")
                return text[_start:k], k + 1  # 假定引号内容不会换行

    operator, operator_start, operator_end = find_first_operator(text, start)
    len_text = len(text)
    name = ""
    content = ""
    new_start = None
    if operator is not None:
        name = text[start:operator_start].strip() + (f".[{operator}]" if operator != "=" else "")  # 记录符号，除非是等号
        for i in range(operator_end, len_text):
            if text[i] == "\n":
                new_start = i + 1
                break
            if text[i] not in (" ", "\t"):  # 找到第一个非空白字符的位置
                if text[i] == "{":
                    content, new_start = find_bracket_content(i)
                    break
                if text[i] == "\"":
                    content, new_start = find_quotation_mark(i)
                    break
                # 以上两个if不满足时才会执行
                for j in range(i, len_text):
                    if text[j].isspace() or text[j] == "{":
                        content = text[i:j]
                        if text[j] == "\n":
                            new_start = j + 1
                            break
                        if text[j] == "{":
                            name += f".[{content}]"  # 这一段是用来处理颜色的
                            content, new_start = find_bracket_content(j)
                            break
                        else:  # 这里text[j]是\t或者空格
                            for m in range(j + 1, len_text):
                                if text[m] == "\n":
                                    new_start = m + 1
                                    break
                                if text[m] == "{":
                                    name += f".[{content}]"  # 这一段是用来处理颜色的
                                    content, new_start = find_bracket_content(m)
                                    break
                                if text[m] not in (" ", "\t"):
                                    new_start = m
                                    break
                        break
                    if new_start is not None:
                        break
            if new_start is not None:
                break

        if new_start is None:
            content = text[operator_end:].strip()
            new_start = len_text + 1
    else:
        new_start = len_text + 1
    return name, content, new_start


def divide_text_into_dict(text, override=True) -> dict:
    """
    将文本分割成不同的部分，并存储在字典中
    :param override: 重复的value是否覆盖
    :param text: 待分割文本
    :return: block名称和内容的字典
    """
    text = re.sub(r"#.*$", "", text, flags=re.MULTILINE)
    start = 0
    dict_blocks = {}
    dict_logic_key = {logic_key: -1 for logic_key in list_logic_keys}
    while start < len(text):  # parse_text_block会返回下一个block的开始位置，如果开始位置比文件长度还长，那么终止循环
        key, value, start = parse_text_block(start, text)
        value = convert_to_number(value)
        if key in list_logic_keys:
            dict_logic_key[key] += 1
            key = f"{key}.[{dict_logic_key[key]}]"
        if key:  # 防止异常值进入字典，这里认为value可以为空
            if key in dict_blocks:
                if override:
                    print(f"{key}重复出现，新值将会覆盖旧值")
                    dict_blocks[key] = value
                else:  # 把新值加在旧值后面
                    if isinstance(dict_blocks[key], list):
                        dict_blocks[key].append(value)
                    else:
                        dict_blocks[key] = [dict_blocks[key], value]
            else:
                dict_blocks[key] = value
    return dict_blocks


def divide_text_into_dict_from_path(path: str, override=True) -> dict:
    """
    将文本分割成不同的部分，并存储在字典中
    :param path: 待处理的路径
    :param override: 重复的value是否覆盖
    :return: block名称和内容的字典
    """
    list_file_paths = pp.get_file_paths_list(path)  # 获取所有的路径
    dict_blocks = {}
    for file_path in list_file_paths:  # 对文件分别进行处理，以防止格式错误造成污染
        if not file_path.endswith(".info"):  # 忽略info文件，这个文件的作用类似注释
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            content = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
            start = 0
            dict_logic_key = {logic_key: -1 for logic_key in list_logic_keys}  # 这些键不应该被合并，通过这种方式来区分
            while start < len(content):  # parse_text_block会返回下一个block的开始位置，如果开始位置比文件长度还长，那么终止循环
                key, value, start = parse_text_block(start, content)
                value = convert_to_number(value)
                if key in list_logic_keys:
                    dict_logic_key[key] += 1
                    key = f"{key}.[{dict_logic_key[key]}]"
                if key:  # 防止异常值进入字典，这里认为value可以为空
                    if key in dict_blocks:
                        if override:
                            print(f"{key}重复出现，新值将会覆盖旧值")
                            dict_blocks[key] = value
                        else:  # 把新值加在旧值后面
                            if isinstance(dict_blocks[key], list):
                                dict_blocks[key].append(value)
                            else:
                                dict_blocks[key] = [dict_blocks[key], value]
                    else:
                        dict_blocks[key] = value
    return dict_blocks


def divide_dict_value(dict_block: dict) -> dict:
    """
    递归函数，进一步对dict的value进行解析
    :param dict_block: 待解析的dict
    :return: 递归解析后的dict
    """

    def process_content(content):
        """
        处理字符串内容，递归解析或分割为列表
        """
        if any(op in content for op in ("<", "=", ">")):  # 这里通过这三个符号判断是否能够进一步解析
            return divide_dict_value(divide_text_into_dict(content, False))
        match_whitespace = re.search(r"\s", content)
        if match_whitespace:  # 不可解析时，如果内容被空白分割，那么将其转化为列表
            return [convert_to_number(item) for item in NAME_PATTERN.findall(content)]
        return content

    for key, value in dict_block.items():
        if isinstance(value, str):
            dict_block[key] = process_content(value)
        elif isinstance(value, list):
            dict_block[key] = [process_content(item) if isinstance(item, str) else item for item in value]
    return dict_block


def get_nested_dict_from_path(path: str, override=True) -> dict:
    """
    从路径获取嵌套字典
    :param path: 路径
    :param override: 新值是否覆盖旧值
    :return: 嵌套字典
    """
    nested_dict = divide_text_into_dict_from_path(path, override)
    nested_dict = divide_dict_value(nested_dict)
    return nested_dict


def get_nested_dict_from_text(text: str, override=True) -> dict:
    nested_dict = divide_text_into_dict(text, override)
    nested_dict = divide_dict_value(nested_dict)
    return nested_dict


# ------------------------------------------------------------------------------------------
def wrong_format(modifier_name: str):
    print(f"{modifier_name}存在格式错误")
    return None


# 以下函数用于解析modifier
def parse_good_modifier(modifier: str):
    modifier_match = GOOD_MODIFIER_PATTERN.match(modifier)
    if modifier_match is None:
        return wrong_format(modifier)
    else:
        return {
            "category": "goods",
            "key_word": modifier_match.group("key_word"),
            "io_type": modifier_match.group("io_type"),
            "am_type": modifier_match.group("am_type")
        }


def parse_building_modifier(modifier: str):  # TODO 这个函数仅能识别buildings_employment_开头的modifier，之后也许可以升级
    modifier_match = BUILDING_EMPLOYMENT_MODIFIER_PATTERN.match(modifier)
    if modifier_match is None:
        return None
    else:
        return {
            "category": "building_employment",
            "key_word": modifier_match.group("key_word"),
            "am_type": modifier_match.group("am_type")
        }


def parse_modifier(modifier: str):
    split_list = modifier.split("_")
    if len(split_list) < 3:  # modifier应该至少3个单位长
        return wrong_format(modifier)

    match split_list[0]:
        case "goods":
            return parse_good_modifier(modifier)
        case "building":
            return parse_building_modifier(modifier)
        case _:
            return wrong_format(modifier)


def parse_modifier_dict(modifier_dict: dict) -> dict:
    modifier_info_dict = {}
    for modifier, value in modifier_dict.items():
        modifier_info = parse_modifier(modifier)
        if modifier_info is None:
            continue
        if not isinstance(value, (int, float)):
            print(f"{modifier}的值{value}不是数值")
            continue
        modifier_info["value"] = value
        modifier_info_dict[modifier] = modifier_info
    return modifier_info_dict


def calibrate_modifier_dict(modifier_dict: dict) -> dict:
    for modifier, value in modifier_dict.items():
        if isinstance(value, list):
            modifier_dict[modifier] = float(sum(value))
    return modifier_dict


# ------------------------------------------------------------------------------------------
# 以下函数待清理

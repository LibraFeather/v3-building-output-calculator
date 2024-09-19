"""
错误处理函数
"""
import os.path
import re

from utils.config_loader import open_json
from utils.config import VANILLA_PATH

config = open_json('config\\warning_settings.json')

if config is not None:
    SHOW_DUPLICATE_KEY_WARNING = config.get('SHOW_DUPLICATE_KEY_WARNING', '') == 'True'
    SHOW_LOCALIZATION_WARNING = config.get('SHOW_LOCALIZATION_WARNING', '') == 'True'
    SHOW_LACK_LOCALIZATION_WARNING = config.get('SHOW_LACK_LOCALIZATION_WARNING', '') == 'True'
else:
    SHOW_DUPLICATE_KEY_WARNING = True
    SHOW_LOCALIZATION_WARNING = True
    SHOW_LACK_LOCALIZATION_WARNING = False


# ------------------------------------------------------------------------------------------
# 以下函数为内部函数

def assumption_value(error_info: str, value, show_error=True):
    if show_error:
        if value is None:
            print(error_info)
        else:
            print(error_info + f"，因此假定为{value}")
    return value


def merge_game_objects(object_names) -> str:
    object_names = [str(item) for item in object_names]
    return ".".join(object_names)


def redundant_bracket(path: str):
    print(f"错误：多余大括号，{path}")


def lack_attribute(*object_names, attribute: str, value=None, show_error=False):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象属性缺失，{object_name}.{attribute}"
    return assumption_value(error_info, value, show_error)


def lack_localization(object_name: str, show_error=True):
    if SHOW_LACK_LOCALIZATION_WARNING and show_error:
        print(f"提醒：对象本地化缺失，{object_name}")


# ------------------------------------------------------------------------------------------
# 以下函数为内外部共用函数

def wrong_type(*object_names, obj_type, value=None):
    object_name = merge_game_objects(object_names)
    if obj_type == '异常':
        error_info = f"错误：对象类型异常，{object_name}"
    else:
        error_info = f"错误：对象类型异常，{object_name}的类型不是{obj_type}"
    return assumption_value(error_info, value)


# 基本函数
def lack_definition(*object_names: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象无定义，{object_name}"
    assumption_value(error_info, value)
    return value


def can_not_parse(*object_names, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"提醒：对象无法解析，{object_name}"
    return assumption_value(error_info, value)


# ------------------------------------------------------------------------------------------

def has_attribute(obj_info, attribute: str, show_error=True) -> bool:  # TODO 函数行为待进一步确认
    if attribute in obj_info.block:
        return True
    else:
        return lack_attribute(obj_info.obj_type, obj_info.loc_key, attribute=attribute,
                              value=False, show_error=show_error)


def get_attribute(obj_info, attribute: str, value, value_type, show_error=True):
    if attribute not in obj_info.block:
        if show_error:
            lack_attribute(obj_info.obj_type, obj_info.loc_key, attribute=attribute)
        return value
    attribute_value = obj_info.block[attribute]
    return check_attribute_value(obj_info.obj_type, obj_info.loc_key, attribute,
                                 attribute_value=attribute_value, value=value, value_type=value_type,
                                 show_error=show_error)


def check_attribute_value(*object_names, attribute_value, value, value_type, show_error=True):
    """
    get_attribute的子函数
    """
    object_name = merge_game_objects(object_names)
    if isinstance(attribute_value, value_type):
        return attribute_value
    if not attribute_value:
        error_info = f"错误：属性的值为空，{object_name}"
        return assumption_value(error_info, value, show_error)
    if isinstance(attribute_value, list):
        value = check_attribute_value(
            *object_names, attribute_value=attribute_value[-1], value=0, value_type=value_type)
        error_info = f"错误：属性多次赋值，{object_name}"
        return assumption_value(error_info, value)
    wrong_type(*object_names, attribute_value, obj_type=value_type)
    return value


def check_modifier_dict_value(obj_info) -> dict:
    """
    保证修正字典是值只能是int或者float
    """
    modifier_dict = {}
    for key, value in obj_info.block.items():
        if isinstance(value, (int, float)):
            modifier_dict[key] = value
        elif isinstance(value, list):
            total = 0
            all_numeric = True
            for item in value:
                if isinstance(item, (int | float)):
                    total += item
                else:
                    print(f"错误：修正的值异常，{obj_info.obj_type}.{obj_info.loc_key}.{key}.{item}")
                    all_numeric = False
            if all_numeric:
                print(f"提醒：修正可合并，{obj_info.obj_type}.{obj_info.loc_key}.{key}")
            modifier_dict[key] = total
        else:
            error_info = f"错误：修正的值异常，{obj_info.obj_type}.{obj_info.loc_key}.{key}.{value}"
            modifier_dict[key] = assumption_value(error_info, 0)
    return modifier_dict


def find_numeric_value(obj, attribute, var_dict: dict) -> int | float:
    """
    现仅用于处理建筑造价
    """
    value = 0
    var_value = getattr(obj, attribute)
    if isinstance(var_value, str):
        if var_value not in var_dict:
            return lack_definition(obj.obj_type, obj.loc_key, attribute, var_value, value=value)
        if not isinstance(var_dict[var_value].value, (int, float)):
            return wrong_type('scrit_values', var_value, obj_type=(int, float), value=value)
        return var_dict[var_value].value
    if isinstance(var_value, (int, float)):
        return var_value
    return wrong_type(obj.obj_type, obj.loc_key, attribute, var_value, obj_type='异常', value=value)


# ------------------------------------------------------------------------------------------
# 以下函数仅用于utils.obj.get_loc
def get_localization(key: str, loc_dict: dict, show_error=True) -> str:
    if key in loc_dict:
        return loc_dict[key]
    else:
        lack_localization(key, show_error)
        return key


def localize_principle(local_loc_dict: dict, principles: list, global_loc_dict: dict):
    for principle in principles:
        principle_match = re.search(r"principle_(?P<name>[\w\-]+?)_(?P<value>\d+)", principle)
        if principle_match is None:
            local_loc_dict[principles] = principle
            continue
        principle_group = 'principle_group_' + principle_match.group('name')
        if principle_group in global_loc_dict:
            local_loc_dict[principle] = (global_loc_dict[principle_group]
                                         + principle_match.group('value'))
        else:
            lack_localization(principle_group)
            local_loc_dict[principle] = principle


def check_long_building_name(loc_dict: dict, buildings: list):
    for building in buildings:  # dummy building的本地化值过长，需要被替换，这里用本地化值的长度作为依据
        if len(loc_dict[building]) > 50:
            print(f"提醒：本地化值过长，{building}，因此被dummy代替")
            loc_dict[building] = 'dummy'


# ------------------------------------------------------------------------------------------
# 一下函数仅作用于GameObject类

def check_existence(obj, attribute, objs: dict):
    if isinstance(attribute, list):
        valid_list = []
        for name in attribute:
            if name not in objs:
                lack_definition(obj.obj_type, obj.loc_key, name)
            else:
                valid_list.append(name)
        return valid_list
    elif isinstance(attribute, str):
        if attribute and attribute not in objs:
            lack_definition(obj.obj_type, obj.loc_key, attribute)
            return ''
        else:
            return attribute
    else:
        wrong_type(obj.obj_type, obj.loc_key, attribute, obj_type=(list, str))


# ------------------------------------------------------------------------------------------
# 以下函数仅作用于textproc的非本地化内容

def check_remaining(path: str, text: str):
    """
    用于检查文本是否存在无法解析的内容
    """
    if text:
        if path is None:
            path = ''
        if text == '}':
            redundant_bracket(path)
        else:
            print(f"错误：文件存在无法解析内容，{path}.{text}")


def wrong_quotes(path: str, text: str):
    if path is None:
        path = ''
    print(f"错误：引号未闭合，{path}.{text}")


def wrong_name(path: str, names: list, text: str):
    if path is None:
        path = ''
    for name in names:
        if name == '}':
            redundant_bracket(path)
        else:
            print(f"错误：文本异常，{path}\n######\n{text}\n######\n")


def check_bracket(path: str):
    if path is None:
        path = ''
    print(f"错误：文件缺失花括号，{path}")


def duplicate_key(key: str, path=None):
    if SHOW_DUPLICATE_KEY_WARNING:
        if path is None:
            return print(f"提醒：重复对象，{key}")
        key_type = 'Mod'
        if is_subpath(VANILLA_PATH, path):
            key_type = 'Vanilla'
        path = os.path.basename(path)
        print(f"提醒：重复对象，{key_type}.{path}.{key}")


def is_subpath(parent, child):
    """
    duplicate_key的子函数
    """
    parent = os.path.normpath(parent)
    child = os.path.normpath(child)

    if child.startswith(parent):
        if child[len(parent):].startswith(os.sep):
            return True
    return False


def get_surrounding_lines_by_char(text, char_index, lines_before=3, lines_after=3):
    lines = text.split('\n')

    line_number = 0
    current_char_index = 0
    for i, line in enumerate(lines):
        if current_char_index + len(line) > char_index:
            line_number = i
            break
        current_char_index += len(line)

    start_line = max(0, line_number - lines_before)
    end_line = min(len(lines) - 1, line_number + lines_after)

    surrounding_lines = lines[start_line:end_line + 1]

    return '\n'.join(surrounding_lines)


# ------------------------------------------------------------------------------------------
# 以下函数仅作用于textproc的本地化内容

def empty_key(value: str):
    if SHOW_LOCALIZATION_WARNING:
        print(f"错误：本地化键缺失，{value}的本地化键")


def empty_value(key: str):
    if SHOW_LOCALIZATION_WARNING:
        print(f"错误：本地化值缺失，{key}的本地化值")


def check_quotation_mark(key: str, value: str):
    if SHOW_LOCALIZATION_WARNING:
        print(f"错误：本地化值引号缺失，{key}: {value}")


def check_unclosed_quotes(key: str, value: str):
    if SHOW_LOCALIZATION_WARNING:
        print(f"错误：本地化值引号未闭合，{key}: {value}")


# ------------------------------------------------------------------------------------------
# 其他函数


def check_objects_dict(objs: dict, obj_type: str) -> dict:
    """
    用于确保字典确实是一个字典
    """
    valid_objs = {}
    for obj, obj_info in objs.items():
        if not isinstance(obj_info.block, dict):
            if obj[0] != "@":
                print(f"错误：文件格式错误，{obj_type}.{obj}")
        else:
            valid_objs[obj] = obj_info
    return valid_objs


def check_bg_loop(bg_info):
    """
    仅用于处理建筑组是否无限递归
    """
    print(f"错误：建筑组无限递归，{bg_info.obj_type}.{bg_info.loc_key}")
    return []


def get_era_num(era, tech) -> int:
    """
    处理科技时代的特化函数
    """
    if isinstance(era, int):
        return era
    elif isinstance(era, str):
        num_match = re.search(r"\d+", era)
        if num_match:
            return int(num_match.group(0))
        else:
            return can_not_parse(tech.obj_type, tech.loc_key, 'era', era, value=0)
    else:
        return wrong_type(tech.obj_type, tech.loc_key, 'era', era, obj_type=int, value=0)


def check_filename(filename):
    """
    用于检测输出的文件名是否带有非法字符
    """
    illegal_chars_regex = r'[<>:"/\\|?*]'
    if re.search(illegal_chars_regex, filename):
        print(f"错误：非法字符，{filename}")
        return re.sub(illegal_chars_regex, '', filename)
    else:
        return filename


def can_not_output(name: str):
    """
    用于处理未知错误导致的文件无法输出
    """
    print(f"错误：未知错误，{name}无法输出")

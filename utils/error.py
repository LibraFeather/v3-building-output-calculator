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
    SHOW_DUPLICATE_KEY_WARNING = False
    SHOW_LOCALIZATION_WARNING = False
    SHOW_LACK_LOCALIZATION_WARNING = False


# ------------------------------------------------------------------------------------------
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


def check_remaining(path: str, text: str):
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


def wrong_name(path: str, names: list):
    if path is None:
        path = ''
    for name in names:
        if name == '}':
            redundant_bracket(path)
        else:
            print(f"错误：名称错误，{path}.{name}")


def redundant_bracket(path: str):
    print(f"错误：多余大括号，{path}")


def wrong_type(*object_names, object_type, value=None):
    object_name = merge_game_objects(object_names)
    if object_type == '异常':
        error_info = f"错误：对象类型异常，{object_name}"
    else:
        error_info = f"错误：对象类型异常，{object_name}的类型不是{object_type}"
    assumption_value(error_info, value)


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


def check_bracket(path: str):
    if path is None:
        path = ''
    print(f"错误：文件缺失花括号，{path}")


# 基本函数
def lack_definition(*object_names: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象无定义，{object_name}"
    assumption_value(error_info, value)
    return value


def lack_attribute(*object_names, attribute: str, value=None, show_error=False):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象属性缺失，{object_name}.{attribute}"
    return assumption_value(error_info, value, show_error)


def lack_localization(object_name: str, show_error=True):
    if SHOW_LACK_LOCALIZATION_WARNING and show_error:
        print(f"提醒：对象本地化缺失，{object_name}")


def can_not_parse(*object_names, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"提醒：对象无法解析，{object_name}"
    assumption_value(error_info, value)


def can_not_output(name: str):
    print(f"错误：未知错误，{name}无法输出")


def check_filename(filename):
    illegal_chars_regex = r'[<>:"/\\|?*]'
    if re.search(illegal_chars_regex, filename):
        print(f"错误：非法字符，{filename}")
        return re.sub(illegal_chars_regex, '', filename)
    else:
        return filename


def check_objects_dict(objs: dict, obj_type: str) -> dict:
    valid_objs = {}
    for obj, obj_info in objs.items():
        if not isinstance(obj_info.block, dict):
            if obj[0] != "@":
                print(f"错误：文件格式错误，{obj_type}.{obj}")
        else:
            valid_objs[obj] = obj_info
    return valid_objs


def check_parent_group(bg_info):
    print(f"错误：建筑组无限递归，{bg_info.obj_type}.{bg_info.loc_key}")


def duplicate_key(key: str, path=None):
    if SHOW_DUPLICATE_KEY_WARNING:
        if path is None:
            return print(f"提醒：重复对象，{key}")
        key_type = 'Mod'
        if is_subpath(VANILLA_PATH, path):
            key_type = 'Vanilla'
        path = os.path.basename(path)
        print(f"提醒：重复对象，{key_type}.{path}.{key}")


def is_subpath(parent_path, child_path):
    # 将路径转换为规范化的形式，以避免路径中的"."和".."造成的歧义
    parent_path = re.escape(parent_path)
    child_path = re.escape(child_path)

    # 构建正则表达式，用于匹配子路径
    # 这个正则表达式检查child_path是否以parent_path开头，并且之后是路径分隔符或字符串结束
    pattern = f"^{re.escape(parent_path)}(?=/|\\Z)"

    # 使用正则表达式进行匹配
    return re.search(pattern, child_path) is not None


# ------------------------------------------------------------------------------------------
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
    wrong_type(*object_names, attribute_value, object_type=value_type)
    return value


def check_modifier_dict_value(obj_info) -> dict:
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


def has_attribute(obj_info, attribute: str, show_error=True) -> bool:  # TODO 函数行为待进一步确认
    if attribute in obj_info.block:
        return True
    else:
        return lack_attribute(obj_info.obj_type, obj_info.loc_key, attribute=attribute,
                              value=False, show_error=show_error)


def get_localization(key: str, loc_dict: dict, show_error=True) -> str:
    if key in loc_dict:
        return loc_dict[key]
    else:
        lack_localization(key, show_error)
        return key


def find_numeric_value(var_value, var_dict: dict) -> int | float:
    value = 0
    if isinstance(var_value, str):
        if var_value not in var_dict:
            lack_definition(var_value, value=value)
            return value
        if not isinstance(var_dict[var_value], (int, float)):
            wrong_type(var_value, object_type=(int, float), value=value)
            return value
        return var_dict[var_value]
    if isinstance(var_value, (int, float)):
        return var_value
    wrong_type(var_value, object_type='异常', value=value)
    return value


# ------------------------------------------------------------------------------------------
def get_era_num(era, tech: str) -> int:
    if isinstance(era, int):
        return era
    elif isinstance(era, str):
        num_match = re.search(r"\d+", era)
        if num_match:
            return int(num_match.group())
        else:
            era_num = 0
            can_not_parse(tech, era, value=era_num)
            return era_num
    else:
        wrong_type(tech, era, object_type=int)


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

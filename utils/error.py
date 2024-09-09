"""
错误处理函数
"""
import re


# ------------------------------------------------------------------------------------------
# 基本函数
def lack_definition(*object_names: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：{object_name}无定义"
    assumption_value(error_info, value)


def lack_attribute(*object_names, attribute: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：{object_name}缺失{attribute}"
    assumption_value(error_info, value)


def lack_localization(object_name: str):
    print(f"提醒：{object_name}缺失本地化")


def wrong_type(*object_names, object_type, value=None):
    object_name = merge_game_objects(object_names)
    if object_type == '异常':
        error_info = f"错误：{object_name}格式异常"
    else:
        error_info = f"错误：{object_name}的类型不是{object_type}"
    assumption_value(error_info, value)


def wrong_path(path: str):
    print(f"错误：路径{path}设置错误")


def can_not_parse(*object_names, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"提醒：{object_name}无法被解析"
    assumption_value(error_info, value)


def merge_game_objects(object_names) -> str:
    return ".".join(object_names)


def assumption_value(error_info: str, value):
    if value is None:
        print(error_info)
    else:
        print(error_info + f"，因此假定为{value}")


# ------------------------------------------------------------------------------------------
def get_attribute(object_name: str, object_blocks_dict: dict, attribute: str, value=None, show_error=True):
    if attribute in object_blocks_dict[object_name]:
        return object_blocks_dict[object_name][attribute]
    else:
        if show_error:
            lack_attribute(object_name, attribute=attribute)
        return value


def has_attribute(object_name: str, object_blocks_dict: dict, attribute: str, show_error=True) -> bool:
    if attribute in object_blocks_dict[object_name]:
        return True
    else:
        if show_error:
            lack_attribute(object_name, attribute=attribute)
        return False


def get_localization(key: str, localization_dict: dict) -> str:
    if key in localization_dict:
        return localization_dict[key]
    else:
        lack_localization(key)
        return key


def find_numeric_value(var_value, var_dict: dict) -> int | float:
    value = 0
    if isinstance(var_value, str):
        if var_value not in var_dict:
            lack_definition(var_value, value=value)
            return value
        if not isinstance(var_dict[var_value], (int, float)):
            wrong_type(var_value, object_type='数值', value=value)
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
    num_match = re.search(r"\d+", era)
    if num_match:
        return int(num_match.group())
    else:
        era_num = 0
        can_not_parse(tech, era, value=era_num)
        return era_num


def process_principle(principle_keys: list, localization_dict_used: dict, localization_dict_all: dict):
    for principle_key in principle_keys:
        principle_match = re.search(r"principle_(?P<name>[\w\-]+?)_(?P<value>\d+)", principle_key)
        if principle_match is None:
            localization_dict_used[principle_keys] = principle_key
            continue
        principle_group_key = 'principle_group_' + principle_match.group('name')
        if principle_group_key in localization_dict_all:
            localization_dict_used[principle_key] = (localization_dict_all[principle_group_key]
                                                     + principle_match.group('value'))
        else:
            lack_localization(principle_group_key)
            localization_dict_used[principle_key] = principle_key


def process_long_building_name(buildings: list, localization_dict_used: dict):
    for building in buildings:  # dummy building的本地化值过长，需要被替换，这里用本地化值的长度作为依据
        if len(localization_dict_used[building]) > 50:
            print(f"提醒：{building}的本地化值过长，因此被dummy代替")
            localization_dict_used[building] = 'dummy'

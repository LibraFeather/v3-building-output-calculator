"""
错误处理函数
"""
import re

from utils.config_loader import open_json

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
def assumption_value(error_info: str, value):
    if value is None:
        print(error_info)
    else:
        print(error_info + f"，因此假定为{value}")


def merge_game_objects(object_names) -> str:
    object_names = [str(item) for item in object_names]
    return ".".join(object_names)


def wrong_name(*object_names: str):
    object_name = merge_game_objects(object_names)
    print(f"错误：名称错误，{object_name}")


def wrong_type(*object_names, object_type, value=None):
    object_name = merge_game_objects(object_names)
    if object_type == '异常':
        error_info = f"错误：对象类型异常，{object_name}"
    else:
        error_info = f"错误：对象类型异常，{object_name}的类型不是{object_type}"
    assumption_value(error_info, value)


def wrong_path(path: str, path_type: str):
    print(f"错误：路径错误，{path_type}，{path}")


def wrong_localization(key: str, value: str):
    if SHOW_LOCALIZATION_WARNING:
        print(f"错误：本地化值异常，{key}的{value}")


# 基本函数
def lack_definition(*object_names: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象无定义，{object_name}"
    assumption_value(error_info, value)


def lack_attribute(*object_names, attribute: str, value=None):
    object_name = merge_game_objects(object_names)
    error_info = f"错误：对象属性缺失，{object_name}的{attribute}"
    assumption_value(error_info, value)


def lack_localization(object_name: str):
    if SHOW_LACK_LOCALIZATION_WARNING:
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


def check_objects_dict(objects_dict: dict, object_type: str) -> dict:
    processed_objects_dict = {}
    for game_object, game_object_info in objects_dict.items():
        if not isinstance(game_object_info, dict):
            if game_object[0] != "@":
                print(f"错误：文件格式错误，{object_type}的{game_object}")
        else:
            processed_objects_dict[game_object] = game_object_info
    return processed_objects_dict


def duplicate_key(key: str):
    if SHOW_DUPLICATE_KEY_WARNING:
        print(f"提醒：重复出现{key}，新值将会覆盖旧值")


# ------------------------------------------------------------------------------------------
def get_attribute(object_name: str, object_blocks_dict: dict, attribute: str, value, value_type, show_error=True):
    if attribute not in object_blocks_dict[object_name]:
        if show_error:
            lack_attribute(object_name, attribute=attribute)
        return value
    if isinstance(object_blocks_dict[object_name][attribute], value_type):
        return object_blocks_dict[object_name][attribute]
    wrong_type(object_name, attribute, object_blocks_dict[object_name][attribute], object_type=value_type)
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
    elif isinstance(era, str):
        num_match = re.search(r"\d+", era)
        if num_match:
            return int(num_match.group())
        else:
            era_num = 0
            can_not_parse(tech, era, value=era_num)
            return era_num
    else:
        wrong_type(era, object_type='数值')


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
            print(f"提醒：本地化值过长，{building}，因此被dummy代替")
            localization_dict_used[building] = 'dummy'

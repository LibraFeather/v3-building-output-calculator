# ------------------------------------------------------------------------------------------

# 错误处理函数

# ------------------------------------------------------------------------------------------
import re


# ------------------------------------------------------------------------------------------
# 基本函数
def lack_definition(name: str, value=None):
    error_info = f"错误：{name}无定义"
    assumption_value(error_info, value)


def lack_attribute(object_name: str, attribute_name: str, value=None):
    error_info = f"错误：{object_name}缺失{attribute_name}"
    assumption_value(error_info, value)


def lack_localization(object_name: str):
    print(f"提醒：{object_name}缺失本地化")


def wrong_type(object_name: str, object_type, value=None):
    if object_type == '异常':
        error_info = f"错误：{object_name}格式异常"
    else:
        error_info = f"错误：{object_name}的类型不是{object_type}"
    assumption_value(error_info, value)


def wrong_path(path: str):
    print(f"错误：路径{path}设置错误")


def assumption_value(error_info: str, value):
    if value is None:
        print(error_info)
    else:
        print(error_info + f"，因此假定为{value}")


def can_not_parse(*object_names, value=None):
    object_name = ".".join(object_names)
    error_info = f"提醒：{object_name}无法被解析"
    assumption_value(error_info, value)


# ------------------------------------------------------------------------------------------
def get_attribute(object_name: str, object_blocks_dict: dict, attribute_name: str, value=None, show_error=True):
    if attribute_name in object_blocks_dict[object_name]:
        return object_blocks_dict[object_name][attribute_name]
    else:
        if show_error:
            lack_attribute(object_name, attribute_name)
        return value


def has_attribute(object_name: str, object_blocks_dict: dict, attribute_name: str, show_error=True) -> bool:
    if attribute_name in object_blocks_dict[object_name]:
        return True
    else:
        if show_error:
            lack_attribute(object_name, attribute_name)
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
            lack_definition(var_value, value)
            return value
        if not isinstance(var_dict[var_value], (int, float)):
            wrong_type(var_value, '数值', value)
            return value
        return var_dict[var_value]
    if isinstance(var_value, (int, float)):
        return var_value
    wrong_type(var_value, '异常', value)
    return value


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

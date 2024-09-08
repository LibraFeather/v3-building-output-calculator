def lack_definition(name: str, value=None):
    error_info = f"错误：{name}无定义"
    assumption_value(error_info, value)


def lack_attribute(object_name: str, attribute_name: str, value=None):
    error_info = f"错误：{object_name}缺失{attribute_name}"
    assumption_value(error_info, value)


def lack_localization(object_name: str):
    print(f"提醒：{object_name}缺失本地化")


def wrong_type(object_name: str, object_type, value=None):
    if object_type == "异常":
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


def can_not_parse(object_name: str, value=None):
    error_info = f"提醒：{object_name}无法被解析"
    assumption_value(error_info, value)

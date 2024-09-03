# ------------------------------------------------------------------------------------------

# 测试函数

# ------------------------------------------------------------------------------------------
import json
import os

from constants.path import OUTPUT_PATH


# ------------------------------------------------------------------------------------------
# 以下函数用于输入测试内容和输出测试结果
def get_input_test_content() -> str:
    """
    将input_test.txt变为字符串，仅用于测试程序运行
    """
    with open("input_test.txt", "r", encoding="utf-8-sig") as file:
        test_content = file.read()
    return test_content


def output_to_test_json(test_var):
    """
    将字符串变为output_test.json，仅用于测试程序运行
    """
    with open(f"{OUTPUT_PATH}\\test.json", "w", encoding="utf-8-sig") as json_file:
        json.dump(test_var, json_file, indent=4, ensure_ascii=False)


def output_to_test_txt(test_var):
    """
    将字符串变为output_test.txt，仅用于测试程序运行
    """
    with open(f"{OUTPUT_PATH}\\test.txt", "w", encoding="utf-8-sig") as text_file:
        text_file.write(test_var)


# ------------------------------------------------------------------------------------------
def txt_combiner_from_one_folder(path: str) -> str:
    """
    组合给定文件夹下的所有非.info文件，然后将他们以字符串类型输出
    """
    content = ""
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8-sig") as _file:
                content += _file.read() + "\n"
    return content


# ------------------------------------------------------------------------------------------
# 以下为开发中函数
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

# ------------------------------------------------------------------------------------------

# 配置文件

# ------------------------------------------------------------------------------------------

import json
import os
import sys


def get_config_path(file_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # 如果是打包后的程序
        application_path = os.path.dirname(sys.executable)
        return os.path.join(application_path, file_path)
    else:
        # 如果是未打包的脚本
        application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, "..", file_path)


def open_json(file_path: str):
    try:
        with open(get_config_path(file_path), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"错误：找不到{file_path}")


GOODS_COST_OFFSET = open_json("config\\goods_cost.json")

config = open_json("config\\path.json")
if config is not None:
    MOD_PATH = config.get("MOD_PATH", "")
    VANILLA_PATH = config.get("VANILLA_PATH", "")
    LOCALIZATION_PATH = config.get("LOCALIZATION_PATH", "")

# 路径处理函数

import os
import json

from config.path import MOD_PATH, VANILLA_PATH

REPLACE_PATH_STR = "replace_paths"
GAME_CUSTOM_DATA_STR = "game_custom_data"
METADATA_PATH = ".metadata\\metadata.json"

replace_paths_list = []


# ------------------------------------------------------------------------------------------
# 以下代码用于更新replace_paths_list
def update_replace_paths_list():
    global replace_paths_list  # 这里需要对其赋值，因此必须使用global
    metadata_path = os.path.join(MOD_PATH, METADATA_PATH)
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8-sig") as file:
            config_dict = json.load(file)
        if GAME_CUSTOM_DATA_STR in config_dict:
            if REPLACE_PATH_STR in config_dict[GAME_CUSTOM_DATA_STR]:
                replace_paths_list = config_dict[GAME_CUSTOM_DATA_STR][REPLACE_PATH_STR]
                replace_paths_list = [path.replace("/", "\\") for path in replace_paths_list]


update_replace_paths_list()  # 更新被替代的路径


# ------------------------------------------------------------------------------------------
# 以下函数用于处理路径和文件
def get_file_paths_list(folder_path: str):
    def update_paths_dict(path):
        for root, _, files in os.walk(path):
            for file in files:
                file_paths[file] = os.path.join(root, file)

    file_paths = {}
    input_folder_path = os.path.join(MOD_PATH, folder_path)
    vanilla_folder_path = os.path.join(VANILLA_PATH, folder_path)

    if folder_path in replace_paths_list and os.path.exists(input_folder_path):  # 如果路径在replace_paths_list内，则忽略vanilla_folder_path
        update_paths_dict(input_folder_path)
        return list(file_paths.values())

    update_paths_dict(vanilla_folder_path)
    if os.path.exists(input_folder_path):  # 检查input文件夹内是否有相同文件并替换
        update_paths_dict(input_folder_path)

    return list(file_paths.values())

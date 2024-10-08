"""
路径处理函数
"""
import os
import json

import utils.config as c

REPLACE_PATH_STR = 'replace_paths'
GAME_CUSTOM_DATA_STR = 'game_custom_data'

METADATA_PATH = '.metadata\\metadata.json'

replace_paths_list = []


def update_replace_paths_list():
    global replace_paths_list  # 这里需要对其赋值，因此必须使用global
    metadata_path = os.path.join(c.get_mod_path(), METADATA_PATH)
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8-sig') as file:
            config_dict = json.load(file)
        if GAME_CUSTOM_DATA_STR in config_dict:
            if REPLACE_PATH_STR in config_dict[GAME_CUSTOM_DATA_STR]:
                replace_paths_list = config_dict[GAME_CUSTOM_DATA_STR][REPLACE_PATH_STR]


update_replace_paths_list()  # 更新被替代的路径


# ------------------------------------------------------------------------------------------
# 以下函数用于处理路径和文件
def update_paths_dict(path: str, paths_dict: dict, is_localization=False):
    for root, _, files in os.walk(path):
        for file in files:
            if is_localization and not file.endswith(f"l_{c.LOCALIZATION}.yml"):
                continue
            relative_path = os.path.relpath(str(os.path.join(root, file)), path)  # 使用相对路径，防止因为文件名重复而覆盖
            paths_dict[relative_path] = os.path.join(root, file)


def get_file_paths(folder_path: str):
    is_localization = True if folder_path == 'localization' else False

    file_paths = {}
    vanilla_folder_path = os.path.join(c.get_vanilla_path(), folder_path)
    mod_folder_path = os.path.join(c.get_mod_path(), folder_path)

    if folder_path in replace_paths_list and os.path.exists(
            mod_folder_path):  # 如果路径在replace_paths_list内，则忽略vanilla_folder_path
        update_paths_dict(mod_folder_path, file_paths, is_localization)
        return list(file_paths.values())

    update_paths_dict(vanilla_folder_path, file_paths, is_localization)
    if os.path.exists(mod_folder_path):  # 检查input文件夹内是否有相同文件并替换
        update_paths_dict(mod_folder_path, file_paths, is_localization)

    return list(file_paths.values())

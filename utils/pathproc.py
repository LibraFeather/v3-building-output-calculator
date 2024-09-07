# ------------------------------------------------------------------------------------------

# 路径处理函数

# ------------------------------------------------------------------------------------------
import os
import json

import config.path as cp

REPLACE_PATH_STR = "replace_paths"
GAME_CUSTOM_DATA_STR = "game_custom_data"

METADATA_PATH = ".metadata\\metadata.json"

replace_paths_list = []


def update_replace_paths_list():
    global replace_paths_list  # 这里需要对其赋值，因此必须使用global
    metadata_path = os.path.join(cp.MOD_PATH, METADATA_PATH)
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
                relative_path = os.path.relpath(str(os.path.join(root, file)), path)  # 使用相对路径，防止因为文件名重复而覆盖
                file_paths[relative_path] = os.path.join(root, file)

    file_paths = {}
    mod_folder_path = os.path.join(cp.MOD_PATH, folder_path)
    vanilla_folder_path = os.path.join(cp.VANILLA_PATH, folder_path)

    if folder_path in replace_paths_list and os.path.exists(
            mod_folder_path):  # 如果路径在replace_paths_list内，则忽略vanilla_folder_path
        update_paths_dict(mod_folder_path)
        return list(file_paths.values())

    update_paths_dict(vanilla_folder_path)
    if os.path.exists(mod_folder_path):  # 检查input文件夹内是否有相同文件并替换
        update_paths_dict(mod_folder_path)

    return list(file_paths.values())


def get_localization_paths() -> list:
    def add_path_to_list(path: str, paths_list: list):
        for root, _, files in os.walk(path):
            for file in files:
                paths_list.append(os.path.join(root, file))

    localization_paths_list = []
    mod_localization_path = os.path.join(cp.MOD_PATH, "localization\\replace")
    if os.path.exists(mod_localization_path):
        mod_localization_path = os.path.join(mod_localization_path, cp.LOCALIZATION_PATH)
        add_path_to_list(mod_localization_path, localization_paths_list)
        return localization_paths_list
    mod_localization_path = os.path.join(cp.MOD_PATH, f"localization\\{cp.LOCALIZATION_PATH}\\replace")
    if os.path.exists(mod_localization_path):
        add_path_to_list(mod_localization_path, localization_paths_list)
        return localization_paths_list
    vanilla_localization_path = os.path.join(cp.VANILLA_PATH, f"localization\\{cp.LOCALIZATION_PATH}")
    add_path_to_list(vanilla_localization_path, localization_paths_list)
    return localization_paths_list

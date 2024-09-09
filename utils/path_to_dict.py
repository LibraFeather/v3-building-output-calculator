# ------------------------------------------------------------------------------------------

# 游戏文件转字典库

# ------------------------------------------------------------------------------------------
import os

import utils.textproc as tp

# 文件路径

GAME_OBJECT_PATH_DICT = {
    'buildings': 'buildings',
    'building_groups': 'building_groups',
    'goods': 'goods',
    'laws': 'laws',
    'pop_types': 'pop_types',
    'power_bloc_identities': 'power_bloc_identities',
    'power_bloc_principles': 'power_bloc_principles',
    'production_method_groups': 'production_method_groups',
    'production_methods': 'production_methods',
    'script_values': 'script_values',
    'technologies': 'technology\\technologies'
}


def get_nested_dict(folder_path: str, path='common') -> dict:
    return tp.get_nested_dict_from_path(os.path.join(path, folder_path))


def get_game_object_dict(game_objects_list: list) -> dict:
    return {game_object: get_nested_dict(GAME_OBJECT_PATH_DICT[game_object]) for game_object in game_objects_list}

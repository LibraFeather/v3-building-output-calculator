"""
游戏对象转字典函数
"""
import os

import utils.textproc as tp

# 文件路径

OBJ_TYPE_PATH_DICT = {
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


def get_objs_dict(folder_path: str, path='common') -> dict:
    return tp.get_nested_dict_from_path(os.path.join(path, folder_path))


def get_obj_types_dict(obj_types_list: list) -> dict:
    return {obj_type: get_objs_dict(OBJ_TYPE_PATH_DICT[obj_type]) for obj_type in obj_types_list}

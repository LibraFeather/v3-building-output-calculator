"""
配置文件
"""
import os

from utils.config_loader import open_json

config = open_json('config\\config.json')


if isinstance(config, dict):
    MOD_PATH = config.get('MOD_PATH', '_input')
    VANILLA_PATH = config.get('VANILLA_PATH', '')
    LOCALIZATION = config.get('LOCALIZATION', 'simp_chinese')

    GOODS_COST_OFFSET = config.get('GOODS_COST_OFFSET', {})
else:
    MOD_PATH = '_input'
    VANILLA_PATH = ''
    LOCALIZATION = 'simp_chinese'

    GOODS_COST_OFFSET = {}


def check_path(path: str, path_type: str):
    if os.path.exists(path):
        return path
    wrong_path(path, path_type)
    if path_type == 'MOD_PATH':
        return '_input'
    else:
        return ''


def wrong_path(path: str, path_type: str):
    print(f"错误：路径错误，{path_type}.{path}")


def get_mod_path():
    return check_path(MOD_PATH, 'MOD_PATH')


def get_vanilla_path():
    return check_path(VANILLA_PATH, 'VANILLA_PATH')

"""
配置文件
"""
import os

from utils.config_loader import open_json

config = open_json('config\\config.json')

if isinstance(config, dict):
    MOD_PATH = config.get('MOD_PATH', '')
    VANILLA_PATH = config.get('VANILLA_PATH', '')
    LOCALIZATION = config.get('LOCALIZATION', '')

    GOODS_COST_OFFSET = config.get('GOODS_COST_OFFSET', {})
else:
    MOD_PATH = ''
    VANILLA_PATH = ''
    LOCALIZATION = 'english'

    GOODS_COST_OFFSET = {}


def check_path(path: str, path_type: str):
    if not os.path.exists(path):
        print(f"错误：路径错误，{path_type}.{path}")


def get_mod_path():
    check_path(MOD_PATH, 'MOD_PATH')
    return MOD_PATH


def get_vanilla_path():
    check_path(VANILLA_PATH, 'VANILLA_PATH')
    return VANILLA_PATH

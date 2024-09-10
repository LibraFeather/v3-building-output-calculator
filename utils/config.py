"""
配置文件
"""
import os

from utils.error import wrong_path
from utils.config_loader import open_json

config = open_json('config\\config.json')

if isinstance(config, dict):
    MOD_PATH = config.get('MOD_PATH', '')
    VANILLA_PATH = config.get('VANILLA_PATH', '')
    LOCALIZATION_PATH = config.get('LOCALIZATION_PATH', '')

    GOODS_COST_OFFSET = config.get('GOODS_COST_OFFSET', {})
else:
    MOD_PATH = ''
    VANILLA_PATH = ''
    LOCALIZATION_PATH = ''

    GOODS_COST_OFFSET = {}


def check_path(path: str, path_type: str):
    if not os.path.exists(path):
        wrong_path(path, path_type)


def get_mod_path():
    check_path(MOD_PATH, '输入路径')
    return MOD_PATH


def get_vanilla_path():
    check_path(VANILLA_PATH, '原版路径')
    return VANILLA_PATH

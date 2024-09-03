# ------------------------------------------------------------------------------------------

# 游戏文件转字典库

# ------------------------------------------------------------------------------------------
import os

import utils.textproc as tp

# 文件路径
GOODS_PATH = "common\\goods"  # 商品
POP_TYPES_PATH = "common\\pop_types"  # pop类型
PM_PATH = "common\\production_methods"  # 生产方式
PMG_PATH = "common\\production_method_groups"  # 生产方式组
BUILDINGS_PATH = "common\\buildings"  # 建筑
SCRIPT_VALUE_PATH = "common\\script_values"
TECHNOLOGIES_PATH = "common\\technologies"

LOCALIZATION_PATH = "localization\\simp_chinese"  # 本地化


def get_nested_dict(folder_path: str, path="common") -> dict:
    return tp.get_nested_dict_from_path(os.path.join(path, folder_path))

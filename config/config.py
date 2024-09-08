# ------------------------------------------------------------------------------------------

# 配置文件

# ------------------------------------------------------------------------------------------

import json
import os


def get_config_path(file_name: str):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)


# 配置商品价格，数值表示相对于基础价格的倍数，原版游戏的数值范围是0.25~1.75
with open(get_config_path("goods_cost.json"), 'r') as f:
    GOODS_COST_OFFSET = json.load(f)

# 配置路径
with open(get_config_path("path.json"), 'r') as f:
    config = json.load(f)

MOD_PATH = config['MOD_PATH']
VANILLA_PATH = config['VANILLA_PATH']
LOCALIZATION_PATH = config['LOCALIZATION_PATH']

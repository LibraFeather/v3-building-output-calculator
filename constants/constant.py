#########################################

# 放置一般常量，便于维护
#TODO 整理常量排列

#########################################

VANILLA_FOLDER = r"E:\\Steam\\steamapps\\common\\Victoria 3\\game"  # 游戏文件位置
MODFILE_FOLDER = r"input"  # 或者直接设置到mod的路径

# 文件位置
METADATA_PATH = r".metadata\\metadata.json"

GOODS_PATH = r"common\\goods"  # 商品
POP_TYPES_PATH = r"common\\pop_types"  # pop类型
PM_PATH = r"common\\production_methods"  # 生产方式
PMG_PATH = r"common\\production_method_groups"  # 生产方式组
BUILDINGS_PATH = r"common\\buildings"  # 建筑
LOCALIZATION_PATH = r"localization\\simp_chinese"  # 本地化
SCRPIT_VALUE_PATH = r"common\\script_values"

LOGIC_KEYS_LIST = ["if", "else_if", "else", "add", "multiply", "divide"]



BUILDING_COST_CONVERT_DICT = {
                                            'construction_cost_canal': 5000,
                                            'construction_cost_monument': 2500,
                                            'construction_cost_very_high': 800,
                                            'construction_cost_high': 600,
                                            'construction_cost_medium': 400,
                                            'construction_cost_low': 200,
                                            'construction_cost_very_low': 100,
                                            }
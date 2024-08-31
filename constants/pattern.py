#######################################

# 放置正则表达式常量
# TODO 整理常量排列

#######################################

REPLACE_PATHS_PATTERN = r"\"replace_paths\"\s*:\s*\[([\d\D]+?)]"
PATH_PATTERN = r"[\w\-/]+"
BLOCK_PATTERN = r"^[\w\-.]+\s*=\s*{"  # 捕获<name> = {<content>}样式的代码块，<name>必须顶行写
BLOCK_PATTERN_0 = r"^[\w\-.]+\s*=\s*{"  # 捕获<name> = {<content>}样式的代码块，<name>必须顶行写
BLOCK_PATTERN_CUS = r"{}\s*="  # 自定义的block_pattern
NAME_PATTERN = r"[\w\-.]+"
NUMERIC_ATTRIBUTE_PATTERN = r"\s*=\s*([\d\-.]+)"  # 用于捕获数字类型的属性，可以处理负数和小数
NON_NUMERIC_ATTRIBUTE_PATTERN = r"\s*=\s*([\w\-.]+)"
LOCALIZATION_PATTERN = r"^\s+[\w\-.]+:.+"
LOCALIZATION_REPLACE_PATTERN = r"\$([\w\-.]+)\$"
OPERATOR_PATTERN = r"(<|<=|=|>=|>)"

TREE_FINDCHILD_PATTERN = r"[\w\-]+"

PM_GOODS_INFO_PATTERN = r"\bgoods_{}.+"
PM_GOODS_PATTERN = r"put_([\w\-]+)_(\w+)"
PM_EMPLOYMENT_PATTERN = r"building_employment_.+"  # pm的劳动力信息
PM_EMPLOYMENT_TYPE_PATTERN = r"building_employment_([\w\-]+)_add"  # pm的劳动力的类型

"""
Calista C.Manstainne 于2024.8.24开始重构
整体思路：
1. 用正则表达式处理p语言字段的同时，做出存储各类数据的容器
2. 按照建筑-生产方式群-生产方式结构生成一棵树，数据来源之前的容器
3. 根据这棵树，处理各项数据，做成表格导出（计划新开一个文件来处理）
"""

import re
from collections import Counter

import utils.textproc as tp

# TODO 按照类型排列
from constants.path import GOODS_PATH, POP_TYPES_PATH, BUILDINGS_PATH, PMG_PATH, PM_PATH, LOCALIZATION_PATH, \
    SCRIPT_VALUE_PATH
from constants.str import COST_STR, WAGE_WEIGHT_STR, REQUIRED_CONSTRUCTION_STR, PRODUCTION_METHOD_GROUPS_STR, \
    PRODUCTION_METHODS_STR, BUILDING_MODIFIERS_STR, WORKFORCE_SCALED_STR, LEVEL_SCALED_STR
from models.model import NormalNode, BuildingNode, PMNode

LOCALIZATION_PATTERN = r"^\s+[\w\-.]+:.+"
LOCALIZATION_REPLACE_PATTERN = r"\$([\w\-.]+)\$"


class BuildingInfoTree:
    def __init__(self) -> None:
        self.scrit_value_info = self.__get_scrit_value_info()
        self.goods_info = self.__get_goods_info()
        self.pop_types_info = self.__get_pops_info()
        self.buildings_info = self.__get_buildings_info()
        self.pmgs_info = self.__get_pmgs_info()
        self.pms_info = self.__get_pms_info()
        self.localization_info = self.__get_localization_info()

        self.automation_pm_list = self.__get_automation_pm_list()

        self.tree = self.generate_tree()

    @staticmethod
    def __get_scrit_value_info() -> dict:
        return tp.get_nested_dict_from_path(SCRIPT_VALUE_PATH)

    # ! 预备部分，创建各项存储字典
    @staticmethod
    def __get_goods_info() -> dict:
        """
        商品名称: 基础价格
        """
        good_blocks_dict = tp.get_nested_dict_from_path(GOODS_PATH)
        goods_dict = {}
        for good in good_blocks_dict:
            if COST_STR in good_blocks_dict[good]:
                goods_dict[good] = float(good_blocks_dict[good][COST_STR])
            else:
                goods_dict[good] = 0.0
                print(f"未找到{good}的{COST_STR}，因此假定其为0.0")
        return goods_dict

    @staticmethod
    def __get_pops_info() -> dict:
        """
        pop类型: 工资权重
        """
        pop_blocks_dict = tp.get_nested_dict_from_path(POP_TYPES_PATH)
        pops_dict = {}
        for pop_type in pop_blocks_dict:
            if WAGE_WEIGHT_STR in pop_blocks_dict[pop_type]:
                pops_dict[pop_type] = float(pop_blocks_dict[pop_type][WAGE_WEIGHT_STR])
            else:
                pops_dict[pop_type] = 0.0
                print(f"未找到{pop_type}的{WAGE_WEIGHT_STR}，因此假定其为0.0")
        return pops_dict

    def __get_buildings_info(self) -> dict:
        """
        建筑: 建造花费， 生产方式组
        """

        def building_cost_converter(building_cost_str):
            if isinstance(building_cost_str, str):
                if building_cost_str not in self.scrit_value_info:
                    print(f"{building_cost_str}无定义，假定为0.0")
                    return 0.0
                if not isinstance(self.scrit_value_info[building_cost_str], (int, float)):
                    print(f"{building_cost_str}的值{self.scrit_value_info[building_cost_str]}不是数值，假定为0.0")
                    return 0.0
                return self.scrit_value_info[building_cost_str]
            if isinstance(building_cost_str, (int, float)):
                return building_cost_str
            print(f"{building_cost_str}格式异常，假定为0.0")
            return 0.0

        buildings_dict = {}
        building_blocks_dict = tp.get_nested_dict_from_path(BUILDINGS_PATH)
        for building in building_blocks_dict:
            if REQUIRED_CONSTRUCTION_STR in building_blocks_dict[building]:
                building_cost = building_cost_converter(
                    building_blocks_dict[building][REQUIRED_CONSTRUCTION_STR])
            else:
                building_cost = 0.0
                # print(f"未找到{building}的{REQUIRED_CONSTRUCTION_STR}，因此假定其为0.0")
            if PRODUCTION_METHOD_GROUPS_STR in building_blocks_dict[building]:
                pmgs_list = building_blocks_dict[building][PRODUCTION_METHOD_GROUPS_STR]
            else:
                pmgs_list = []
                print(f"{building}格式异常，未找到任何生产方式组")
            buildings_dict[building] = {'cost': building_cost, 'pmgs': pmgs_list}
        return buildings_dict

    @staticmethod
    def __get_pmgs_info() -> dict:
        """
        生产方式组: 生产方式
        """
        pmg_blocks_dict = tp.get_nested_dict_from_path(PMG_PATH)
        pmgs_dict = {}
        for pmg in pmg_blocks_dict:
            if PRODUCTION_METHODS_STR in pmg_blocks_dict[pmg]:
                pms_list = pmg_blocks_dict[pmg][PRODUCTION_METHODS_STR]
            else:
                pms_list = []
                print(f"{pmg}格式异常，未找到任何生产方式")
            pmgs_dict[pmg] = pms_list
        return pmgs_dict

    def __get_pms_info(self) -> dict:
        pm_blocks_dict = tp.get_nested_dict_from_path(PM_PATH)
        pms_dict = {}
        for pm in pm_blocks_dict:
            pms_dict[pm] = {"input": {}, "output": {}, "workscale": {}}
            if BUILDING_MODIFIERS_STR not in pm_blocks_dict[pm]:
                # print(f"{pm}中缺少{BUILDING_MODIFIERS_STR}")
                continue

            modifier_dict = Counter()
            if WORKFORCE_SCALED_STR in pm_blocks_dict[pm][BUILDING_MODIFIERS_STR]:
                modifier_dict.update(tp.calibrate_modifier_dict(
                    dict(pm_blocks_dict[pm][BUILDING_MODIFIERS_STR][WORKFORCE_SCALED_STR])))  # 防止空值
            if LEVEL_SCALED_STR in pm_blocks_dict[pm][BUILDING_MODIFIERS_STR]:
                modifier_dict.update(
                    tp.calibrate_modifier_dict(dict(pm_blocks_dict[pm][BUILDING_MODIFIERS_STR][LEVEL_SCALED_STR])))
            modifier_dict = tp.parse_modifier_dict(dict(modifier_dict))
            for modifier, modifier_info in modifier_dict.items():
                if modifier_info["am_type"] != "add":  # 暂时只允许add类modifier
                    print(f"{pm}的{modifier}的{modifier_info["am_type"]}不是add，因此被忽略")
                    continue
                match modifier_info["category"]:
                    case "goods":
                        if modifier_info["key_word"] not in self.goods_info:
                            print(f"未找到{pm}中{modifier_info["key_word"]}的定义")
                            continue
                        pms_dict[pm][modifier_info["io_type"]][modifier_info["key_word"]] = modifier_info["value"]
                    case "building_employment":
                        if modifier_info["key_word"] not in self.pop_types_info:
                            print(f"未找到{pm}中{modifier_info["key_word"]}的定义")
                            continue
                        pms_dict[pm]["workscale"][modifier_info["key_word"]] = modifier_info["value"]

        return pms_dict

    def __get_localization_info(self) -> dict:
        content = tp.txt_combiner(LOCALIZATION_PATH)
        localization_dict_all = tp.extract_all_blocks(LOCALIZATION_PATTERN, content, "\"")

        localization_keys_used = list(self.buildings_info.keys()) + list(self.pmgs_info.keys()) + list(
            self.pms_info.keys())
        localization_dict_used = {}
        for key in localization_keys_used:
            if key in localization_dict_all:  # 一些键没有对应的值
                localization_dict_used[key] = localization_dict_all[key]
            else:
                print(f"找不到{key}的本地化")
                localization_dict_used[key] = key

        for key, value in localization_dict_used.items():
            replace_list = re.findall(LOCALIZATION_REPLACE_PATTERN, value)
            if replace_list:
                for replace in replace_list:
                    if replace in localization_dict_all.keys():
                        value = value.replace(f"${replace}$", localization_dict_all[replace])
                localization_dict_used[key] = value

        # dummy building的本地化值过长，需要被替换，这里用本地化值的长度作为依据
        for building in self.buildings_info:
            if len(localization_dict_used[building]) > 50:
                print(f"{building}的本地化值过长，被dummy代替")
                localization_dict_used[building] = "dummy"

        return localization_dict_used

    def __get_automation_pm_list(self):
        return [pm for pmg, pm_list in self.pmgs_info.items() if self.localization_info[pmg] == "自动化" for pm in
                pm_list]

    # ------------------------------------------------------------------------------------------
    # ! 按建筑-生产方式群-生产方式创建信息树
    def generate_tree(self) -> list:
        tree_list = self.parse_buildings()
        return tree_list

    def parse_buildings(self) -> list:
        buildings_list = []
        for building, building_info in self.buildings_info.items():
            buildings_list.append(BuildingNode(
                localization_key=building,
                localization_value=self.localization_info[building],
                children=self.parse_pmgs(building_info['pmgs']),
                building_cost=building_info['cost']
            ))

        return buildings_list

    def parse_pmgs(self, pmgs: list) -> list:
        pmgs_list = []
        for pmg in pmgs:
            if pmg in self.pmgs_info:
                pmgs_list.append(NormalNode(
                    localization_key=pmg,
                    localization_value=self.localization_info[pmg],
                    children=self.parse_pms(self.pmgs_info[pmg])
                ))
            else:
                print(f"{pmg}无定义")

        return pmgs_list

    def parse_pms(self, pms) -> list:
        pms_list = []
        for pm in pms:
            if pm in self.pms_info:
                pms_list.append(PMNode(
                    localization_key=pm,
                    localization_value=self.localization_info[pm],
                    good_input=self.pms_info[pm]['input'],
                    good_output=self.pms_info[pm]['output'],
                    workforce=self.pms_info[pm]['workscale'],
                    children=[]
                ))
            else:
                print(f"{pm}无定义")
        return pms_list

"""
Calista C.Manstainne 于2024.8.24开始重构
整体思路：
1. 用正则表达式处理p语言字段的同时，做出存储各类数据的容器
2. 按照建筑-生产方式群-生产方式结构生成一棵树，数据来源之前的容器
3. 根据这棵树，处理各项数据，做成表格导出（计划新开一个文件来处理）
"""

import re
import utils.textproc as tp
import utils.test as t

# TODO 按照类型排列
from constants.constant import GOODS_PATH, POP_TYPES_PATH, BUILDING_COST_CONVERT_DICT, BUILDINGS_PATH, PMG_PATH, \
    PM_PATH, LOCALIZATION_PATH
from constants.pattern import TREE_FINDCHILD_PATTERN, PM_GOODS_INFO_PATTERN, PM_GOODS_PATTERN, PM_EMPLOYMENT_PATTERN, \
    PM_EMPLOYMENT_TYPE_PATTERN, LOCALIZATION_PATTERN, LOCALIZATION_REPLACE_PATTERN
from models.model import NormalNode, BuildingNode, PMNode


class BuildingInfoTree:
    def __init__(self) -> None:
        self.goods_info = self.__get_goods_info()
        self.pop_types_info = self.__get_pops_info()
        self.buildings_info = self.__get_buildings_info()
        self.pmgs_info = self.__get_pmgs_info()
        self.pms_info = self.__get_pms_info()
        self.localization_info = self.__get_localization_info()

        self.tree = self.generate_tree()

    # ! 预备部分，创建各项存储字典
    @staticmethod
    def __get_goods_info() -> dict:
        """
        两列数据：商品名称和基础价格
        """
        dict_good_blocks = tp.extract_blocks_to_dict(GOODS_PATH)
        goods_dict = {}
        for good, good_block in dict_good_blocks.items():
            cost = tp.get_numeric_attribute("cost", good_block)
            if cost is None:
                print(f"找不到{good}的基础价格，因此{good}将被忽略")
                continue
            # 价格是整数，为了兼容性考虑，这里记为浮点数
            goods_dict[good] = float(cost)
        return goods_dict

    @staticmethod
    def __get_pops_info() -> dict:
        """
        两列数据：pop类型/工资权重
        """
        dict_pop_blocks = tp.extract_blocks_to_dict(POP_TYPES_PATH)
        pops_dict = {}
        for pop_type, pop_type_block in dict_pop_blocks.items():
            wage_weight = tp.get_numeric_attribute("wage_weight", pop_type_block)
            if wage_weight is None:
                wage_weight = 0
                print(f"未找到{pop_type}的wage_weight，因此假定为0")
            pops_dict[pop_type] = float(wage_weight)
        return pops_dict

    def __get_buildings_info(self) -> dict:
        buildings_dict = {}
        building_blocks_dict = tp.extract_blocks_to_dict(BUILDINGS_PATH)

        for building, building_block in building_blocks_dict.items():
            building_cost_str = tp.get_non_numeric_attribute("required_construction", building_block)
            building_cost = self.__building_cost_converter(building_cost_str)
            pmg_block = tp.extract_one_block("production_method_groups", building_block)
            if pmg_block is None:
                print(f"{building}格式异常，未找到任何生产方式组")
            pmg_block_split = re.compile(TREE_FINDCHILD_PATTERN).findall(pmg_block)
            buildings_dict[building] = {'cost': building_cost, 'pmgs': pmg_block_split}

        return buildings_dict

    @staticmethod
    def __get_pmgs_info() -> dict:
        dict_pmg_blocks = tp.extract_blocks_to_dict(PMG_PATH)
        pmgs_dict = {}
        for pmg, pmg_block in dict_pmg_blocks.items():
            pm_block = tp.extract_one_block("production_methods", pmg_block)
            if pm_block is None:
                print(f"{pmg}格式异常，因此无法找到任何生产方式")
                continue
            pms_list = []
            for pm in re.compile(TREE_FINDCHILD_PATTERN).findall(pm_block):
                pms_list.append(pm)
            pmgs_dict[pmg] = pms_list
        return pmgs_dict

    def __get_pms_info(self) -> dict:
        """
        获取生产方式的字典
        :return : 生产方式的字典
        """
        dict_pm_blocks = tp.extract_blocks_to_dict(PM_PATH)
        dict_pm = {}
        for pm, pm_block in dict_pm_blocks.items():
            dict_pm[pm] = {}
            dict_pm[pm]['input'] = self.__add_good_info_for_pm(pm, pm_block, 'input')
            dict_pm[pm]['output'] = self.__add_good_info_for_pm(pm, pm_block, 'output')
            dict_pm[pm]['workscale'] = self.__add_employment_info_for_pm(pm, pm_block)
        return dict_pm

    @staticmethod
    def __building_cost_converter(building_cost_str):
        if building_cost_str in BUILDING_COST_CONVERT_DICT.keys():
            return BUILDING_COST_CONVERT_DICT[building_cost_str]
        else:
            return 0.0

    def __add_good_info_for_pm(self, pm, pm_block, io_type) -> dict:
        goods_info_str_list = re.findall(PM_GOODS_INFO_PATTERN.format(io_type), pm_block)
        goods_info_dict = {}
        for goods_input in goods_info_str_list:
            matched_good_str = re.compile(PM_GOODS_PATTERN).search(goods_input)
            if not matched_good_str:
                print(f"{pm}中的{goods_input}格式异常，无法捕获商品名称")
                continue
            good = matched_good_str.group(1)
            am_type = matched_good_str.group(2)  # add 或 mult
            if am_type not in ["add", "mult"]:
                print(f"{pm}中的{goods_input}格式异常，无法确认add或mult")
                continue
            # 确保商品存在于商品的字典中
            if good not in self.goods_info.keys():
                print(f"未找到{pm}中{good}的定义")
                continue
            number = tp.get_numeric_attribute(f"_{am_type}", goods_input)
            if number is None:
                print(f"{pm}中的{goods_input}格式异常，无法捕获{good}的{io_type}数量")
                continue
            # 商品数量大部分都是整数，但是自给农场是小数，这里统一以浮点数记录
            number = float(number)
            goods_info_dict[good] = number
        return goods_info_dict

    def __get_localization_info(self) -> dict:
        content = tp.txt_combiner(LOCALIZATION_PATH)
        t.output_to_test_txt(content)
        localization_dict_all = tp.extract_all_blocks(LOCALIZATION_PATTERN, content, "\"")
        t.output_to_test_json(localization_dict_all)

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

    def __add_employment_info_for_pm(self, pm, pm_block) -> dict:
        list_workforce_add = re.compile(PM_EMPLOYMENT_PATTERN).findall(pm_block)
        workforce_info_dict = {}
        for workforce_add in list_workforce_add:
            match_workforce = re.compile(PM_EMPLOYMENT_TYPE_PATTERN).search(workforce_add)
            if not match_workforce:
                print(f"{pm}中的{workforce_add}格式异常，无法捕获人群名称")
                continue
            workforce = match_workforce.group(1)
            if workforce not in self.pop_types_info.keys():
                print(f"未找到{pm}中{workforce}的定义")
                continue
            number = tp.get_numeric_attribute("_add", workforce_add)
            if number is None:
                print(f"未找到{pm}中{workforce}的数量")
                continue
            # 劳动力数量应该是整数
            number = int(number)
            workforce_info_dict[workforce] = number
        return workforce_info_dict

    # ! 按建筑-生产方式群-生产方式创建信息树
    def generate_tree(self):
        tree_list = self.parse_buildings()
        return tree_list

    def parse_buildings(self):
        buildings_list = []
        for building, building_info in self.buildings_info.items():
            buildings_list.append(BuildingNode(
                name=building,
                localization_key=self.localization_info[building],
                children=self.parse_pmgs(building_info['pmgs']),
                building_cost=building_info['cost']
            ))

        return buildings_list

    def parse_pmgs(self, pmgs: list):
        pmgs_list = []
        for pmg in pmgs:
            if pmg in self.pmgs_info:
                pmgs_list.append(NormalNode(
                    name=pmg,
                    localization_key=self.localization_info[pmg],
                    children=self.parse_pms(self.pmgs_info[pmg])
                ))
            else:
                print(f"{pmg}无定义")

        return pmgs_list

    def parse_pms(self, pms):
        pms_list = []
        for pm in pms:
            if pm in self.pms_info:
                pms_list.append(PMNode(
                    name=pm,
                    localization_key=self.localization_info[pm],
                    good_input=self.pms_info[pm]['input'],
                    good_output=self.pms_info[pm]['output'],
                    workforce=self.pms_info[pm]['workscale'],
                    children=[]
                ))
            else:
                print(f"{pm}无定义")
        return pms_list

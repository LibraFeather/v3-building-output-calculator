'''
Calista C.Manstainne 于2024.8.24开始重构
整体思路：
1. 用正则表达式处理p语言字段的同时，做出存储各类数据的容器
2. 按照建筑-生产方式群-生产方式结构生成一棵树，数据来源之前的容器
3. 根据这棵树，处理各项数据，做成表格导出（计划新开一个文件来处理）
'''

import re
import os


#TODO 按照类型排列
from constants.constant import GOODS_PATH, POP_TYPES_PATH, VANILLA_FOLDER, BUILDINGS_PATH, BUILDING_COST_CONVERT_DICT, PMG_PATH, PM_PATH
from constants.pattern import BLOCK_PATTERN_0, NAME_PATTERN, NUMERIC_ATTRIBUTE_PATTERN, BLOCK_PATTERN_CUS, TREE_FINDCHILD_PATTERN, NON_NUMERIC_ATTRIBUTE_PATTERN, \
                              PM_GOODS_INFO_PATTERN, PM_GOODS_PATTERN, PM_EMPLOYMENT_PATTERN, PM_EMPLOYMENT_TYPE_PATTERN
from models.model import NormalNode, BuildingNode, PMNode

class BuildingInfoTree:
    def __init__(self) -> None:
        self.tree = []

        self.goods_info = self.__get_goods_info()
        self.pop_types_info = self.__get_pops_info()
        self.buildings_info = self.__get_buildings_info()
        self.pmgs_info =  self.__get_pmgs_info()
        self.pms_info = self.__get_pms_info()

#! 预备部分，创建各项存储字典
    def __get_goods_info(self) -> dict:
        """
        两列数据：商品名称和基础价格
        """
        dict_good_blocks = self.extract_blocks_to_dict(GOODS_PATH)
        goods_dict = {}
        for good, good_block in dict_good_blocks.items():
            cost = self.get_numeric_attribute("cost", good_block)
            if cost is None:
                print(f"找不到{good}的基础价格，因此{good}将被忽略")
                continue
            # 价格是整数，为了兼容性考虑，这里记为浮点数
            goods_dict[good] = float(cost)
        return goods_dict
    
    def __get_pops_info(self) -> dict:
        """
        两列数据：pop类型/工资权重
        """
        dict_pop_blocks = self.extract_blocks_to_dict(POP_TYPES_PATH)
        pops_dict = {}
        for pop_type, pop_type_block in dict_pop_blocks.items():
            wage_weight = self.get_numeric_attribute("wage_weight", pop_type_block)
            if wage_weight is None:
                wage_weight = 0
                print(f"未找到{pop_type}的wage_weight，因此假定为0")
            pops_dict[pop_type] = float(wage_weight)
        return pops_dict

    def __get_buildings_info(self) -> dict:
        buildings_list = []
        building_blocks_dict = self.extract_blocks_to_dict(BUILDINGS_PATH)

        for building, building_block in building_blocks_dict.items():
            building_cost_str = self.get_non_numeric_attribute("required_construction", building_block)
            building_cost = self.building_cost_converter(building_cost_str)
            buildings_list.append({'name': building, 'cost': building_cost})
        
        return buildings_list

    def __get_pmgs_info(self) -> dict:
        dict_pmg_blocks = self.extract_blocks_to_dict(PMG_PATH)
        pmgs_list = []
        for pmg, pmg_block in dict_pmg_blocks.items():
            pmg_dict = {}
            pm_block = self.extract_one_block("production_methods", pmg_block)
            if pm_block is None:
                print(f"{pmg}格式异常，因此无法找到任何生产方式")
                continue
            pms_list = []
            for pm in re.compile(TREE_FINDCHILD_PATTERN).findall(pm_block):
                pms_list.append(pm)
            pmg_dict[pmg] = pms_list
            pmgs_list.append(pmg_dict)
        return pmgs_list

    def __get_pms_info(self) -> dict:
        """
        获取生产方式的字典
        :return : 生产方式的字典
        """
        dict_pm_blocks = self.extract_blocks_to_dict(PM_PATH)
        dict_pm = {}
        for pm, pm_block in dict_pm_blocks.items():
            dict_pm[pm] = {}
            dict_pm[pm]['input'] = self.__add_good_info_for_pm(pm, pm_block, 'input')
            dict_pm[pm]['output'] = self.__add_good_info_for_pm(pm, pm_block, 'output')
            dict_pm[pm]['workscale'] = self.__add_employment_info_for_pm(pm, pm_block)
        return dict_pm

    def building_cost_converter(self, building_cost_str):
        if building_cost_str in BUILDING_COST_CONVERT_DICT.keys():
            return BUILDING_COST_CONVERT_DICT[building_cost_str]
        else:
            return 0.0

    def __add_good_info_for_pm(self, pm, pm_block, io_type) -> list:
        goods_info_str_list = re.findall(PM_GOODS_INFO_PATTERN.format(io_type), pm_block)
        goods_info_list = []
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
            number = self.get_numeric_attribute(f"_{am_type}", goods_input)
            if number is None:
                print(f"{pm}中的{goods_input}格式异常，无法捕获{good}的{io_type}数量")
                continue
            # 商品数量大部分都是整数，但是自给农场是小数，这里统一以浮点数记录
            number = float(number)
            goods_info_list.append({'good': good, 'number': number})
        return goods_info_list
    
    def __add_employment_info_for_pm(self, pm, pm_block) -> list:
        list_workforce_add = re.compile(PM_EMPLOYMENT_PATTERN).findall(pm_block)
        workforce_info_list = []
        for workforce_add in list_workforce_add:
            match_workforce = re.compile(PM_EMPLOYMENT_TYPE_PATTERN).search(workforce_add)
            if not match_workforce:
                print(f"{pm}中的{workforce_add}格式异常，无法捕获人群名称")
                continue
            workforce = match_workforce.group(1)
            if workforce not in self.pop_types_info.keys():
                print(f"未找到{pm}中{workforce}的定义")
                continue
            number = self.get_numeric_attribute("_add", workforce_add)
            if number is None:
                print(f"未找到{pm}中{workforce}的数量")
                continue
            # 劳动力数量应该是整数
            number = int(number)
            workforce_info_list.append({'workforce': workforce, 'number': number})
        return workforce_info_list

#! 按建筑-生产方式群-生产方式创建信息树
#TODO 重构生成树代码
    def generate_tree(self):
        # buildings_block_dict = self.parse_buildings()
        # return buildings_block_dict
        pm_dict_total = self.__get_pms_info()
        print(pm_dict_total)

    def parse_buildings(self):
        dict_building_blocks = self.extract_blocks_to_dict(BUILDINGS_PATH)
        for building, building_block in dict_building_blocks.items():
            building_cost_str = self.get_non_numeric_attribute("required_construction", building_block)
            building_cost = self.building_cost_converter(building_cost_str)

            self.tree.append(BuildingNode(
                name = building,
                localization_key = building,
                children = self.parse_pmgs(building, building_block),
                building_cost = building_cost
            ))

    def parse_pmgs(self, building, building_block):
        node_list = []

        pmg_block = self.extract_one_block("production_method_groups", building_block)
        if pmg_block is None:
            print(f"{building}格式异常，未找到任何生产方式组")
        pmg_block_splited = re.compile(TREE_FINDCHILD_PATTERN).findall(pmg_block)

        for pmg in pmg_block_splited:
            node_list.append(NormalNode(
                name = pmg,
                localization_key = pmg,
                children = self.parse_pms(pmg, pmg_block)
            ))

        return node_list

    def parse_pms(self, pmg, pmg_block):
        return 1

#! 生成树要使用的通用工具
    def get_config_file_paths(self, folder_name):
        file_paths = {}

        #TODO 等完成了重构再考虑Mod的事情
        # input_folder_path = os.path.join(MODFILE_FOLDER, folder_name)
        # if folder_name in self.list_replace_path and self.list_replace_path != '':
        #     if os.path.exists(input_folder_path):
        #         for root, _, files in os.walk(input_folder_path):
        #             for file in files:
        #                 file_paths[file] = os.path.join(root, file)
        #         return list(file_paths.values())

        # 读取vanilla文件夹内的文件
        vanilla_folder_path = os.path.join(VANILLA_FOLDER, folder_name)
        for root, _, files in os.walk(vanilla_folder_path):
            for file in files:
                file_paths[file] = os.path.join(root, file)

        # 检查input文件夹内是否有相同文件并替换

        # if os.path.exists(input_folder_path):
        #     for root, _, files in os.walk(input_folder_path):
        #         for file in files:
        #             file_paths[file] = os.path.join(root, file)

        return list(file_paths.values())

    def extract_all_from_config_file_paths(self, path: str) -> str:
        """
        组合给定路径下的所有非.info文件，然后将他们以字符串类型输出
        :param path: 给定的路径
        :return : 组合后的字符串
        """
        content = ""
        list_file_path = self.get_config_file_paths(path)
        if list_file_path:
            for file_path in list_file_path:
                if not file_path.endswith(".info"):
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        content += f.read()
                        # 额外加一个\n，确保位于行首的字符依然位于行首
                        content += "\n"
        else:
            print(f"找不到{path}，请确认游戏路径是否设置正确")
        return content

    def extract_all_from_config_file_paths_without_notes(self, path: str) -> str:
        """
        txt_combiner的移除注释版本，仅移除#后的内容，不要在处理本地化文件的时候使用这个！
        :param path: 给定的路径
        :return: 组合后的字符串
        """
        return re.sub(r"#.*$", "", self.extract_all_from_config_file_paths(path), flags=re.MULTILINE)

    def _extract_bracket_content(self, text: str, start: int, char: str):
        """
        提取给定字符之间的内容
        :param text: 待检索文本
        :param start: 字符开始位置
        :param char: 待匹配字符
        :return: 字符之间的字符串（包括两端）
        """
        if char in ["{", "[", "("]:
            open_bracket = char
            close_bracket = {"{": "}", "[": "]", "(": ")"}[char]
            stack = []
            first_open_bracket_pos = -1  # 用于保存第一个open_bracket的位置
            for i in range(start, len(text)):
                if text[i] == open_bracket:
                    if first_open_bracket_pos == -1:
                        first_open_bracket_pos = i
                    stack.append(i)
                elif text[i] == close_bracket:
                    stack.pop()
                    if not stack:
                        return text[start:first_open_bracket_pos - 1], text[first_open_bracket_pos + 1:i]  # 不包括两端的括号
        elif char in ["\"", "\'"]:
            first_quote_pos = text.find(char, start)  # 捕获第一个引号的位置
            if first_quote_pos != -1:
                end = text.find(char, first_quote_pos + 1)
                if end != -1:
                    return text[start:first_quote_pos - 1], text[first_quote_pos + 1:end]
        return None

    def extract_blocks_to_dict(self, path: str) -> dict:
        """
        extract_all_blocks的快捷版本，以path为输入，专门处理<str> = {<content>}格式的代码块
        :param path: 文件路径
        :return: <str>：<content>格式的字典
        """
        content = self.extract_all_from_config_file_paths_without_notes(path)  # 此处会移除注释
        return self.extract_all_blocks(BLOCK_PATTERN_0, content, "{")

    def extract_all_blocks(self, pattern: str, text: str, char: str) -> dict:
        """
        提取<str> = {<content>}格式的代码块
        对于{、[或(，会匹配第一个匹配的}、]或)，"或'则只会匹配下一个"或'
        以<str>：<content>的字典形式返回
        :param pattern: 代码块开头<str> = {的格式
        :param text: 待检索的文本
        :param char: 待配对的字符类型，只能是{、[、(、"或‘
        :return: <str>：<content>格式的字典
        """
        dict_block = {}
        for match in re.finditer(pattern, text, re.MULTILINE):
            name, block = self._extract_bracket_content(text, match.start(), char)
            name = re.compile(NAME_PATTERN).search(name).group(0) if re.compile(NAME_PATTERN).search(name) else "None"
            if block:
                if name in dict_block.keys():
                    print(f"{name}重复出现")
                dict_block[name] = block
        return dict_block

    def extract_one_block(self, str_name: str, text: str):
        """
        只会提取一个特定的block
        :param str_name: block的name
        :param text: 待提取文本
        :return: 提取出的block
        """
        one_block_pattern = BLOCK_PATTERN_CUS.format(str_name)
        match = re.search(one_block_pattern, text)
        if not match:
            return None
        _, block = self._extract_bracket_content(text, match.start(), "{")
        return block

    def get_numeric_attribute(self, name: str, text: str):
        """
        输入数字类型属性的名称和待查询文本，输出属性的值
        :param name: 属性的名称
        :param text: 待查询文本
        :return: 属性的值
        """
        if name.startswith("_"):
            start = ""
        else:
            start = "\\b"
        na_pattern = re.compile(f"{start}{name}{NUMERIC_ATTRIBUTE_PATTERN}")
        match = na_pattern.search(text)
        if match:
            return match.group(1)
        else:
            return None

    def get_non_numeric_attribute(self, name: str, text: str):
        if name.startswith("_"):
            start = ""
        else:
            start = "\\b"
        na_pattern = re.compile(f"{start}{name}{NON_NUMERIC_ATTRIBUTE_PATTERN}")
        match = na_pattern.search(text)
        if match:
            return match.group(1)
        else:
            return None

if __name__ == '__main__':
    building_info_tree = BuildingInfoTree()
    building_info_tree.generate_tree()
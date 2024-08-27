import itertools
import re
import json
from typing import Dict, TypedDict
from models.goods_info import GoodsInfo
import pandas as pd

import easytool as et

#TODO 旧文件基本可以放弃了
# 输出路径
OUTPUT_PATH = "output"

# 游戏文件路径
GOODS_PATH = r"common\\goods"  # 商品
POP_TYPES_PATH = r"common\\pop_types"  # pop类型
PM_PATH = r"common\\production_methods"  # 生产方式
PMG_PATH = r"common\\production_method_groups"  # 生产方式组
BUILDINGS_PATH = r"common\\buildings"  # 建筑
LOCALIZATION_PATH = r"localization\\simp_chinese"  # 本地化
SCRPIT_VALUE_PATH = r"common\\script_values"

# 正则表达式模式
pm_goods_increase_pattern = r"\bgoods_{}.+"  # pm中输入输出商品的格式
pm_goods_pattern = re.compile(r"put_([\w\-]+)_(\w+)")
pm_employment_pattern = re.compile(r"building_employment_.+")  # pm的劳动力信息
pm_employment_type_pattern = re.compile(r"building_employment_([\w\-]+)_add")  # pm的劳动力的类型
str_pm_in_pmg = "production_methods"  # 生产方式组代码块中的生产方式
str_pmg_in_building = "production_method_groups"  # 建筑代码块中的生产方式组代码块
content_pattern = re.compile(r"[\w\-]+")  # 捕获位于父代码块的子代码块的内容，比如位于建筑代码块中的生产方式组
construction_cost_pattern = re.compile(r"\bconstruction_cost.+")


# 变量的类型限制
# ------------------------------------------------------------------------------------------


class PmAttributesDict(TypedDict):
    df_pm_goods: pd.DataFrame
    df_pm_workforce: pd.DataFrame


PMDict = Dict[str, PmAttributesDict]
PMGDict = Dict[str, PMDict]
BuildingsDict = Dict[str, PMGDict]


# ------------------------------------------------------------------------------------------
class ScripValuesInfo:
    def __init__(self, path=SCRPIT_VALUE_PATH):
        self.path = path
        self.dict_construction_cost = self._create_dict_construction_cost()

    def _create_dict_construction_cost(self) -> dict:
        dict_construction_cost = {}
        content = et.txt_combiner_rc(self.path)
        list_cc_values = construction_cost_pattern.findall(content)
        for cc_value in list_cc_values:
            name = et.name_pattern.search(cc_value).group(0)
            value = et.search_non_numeric_attribute(name, cc_value)
            dict_construction_cost[name] = int(value)
        return dict_construction_cost


class GoodsInfo:
    """
    以数据帧类型储存商品的名称和基础价格
    """

    def __init__(self, path=GOODS_PATH):
        """
        :param path: 商品文件的路径
        """
        self.path = path
        self.dict = self._create_dict()
        self.df = pd.DataFrame.from_dict(
            self.dict, orient="index", columns=["cost"]
        )  # 商品名称和基础价格的数据帧
        self.list = list(self.dict.keys())

    def _create_dict(self) -> dict:
        """
        创建一个储存商品名称和基础价格信息的数据帧
        :return: 储存商品名称和基础价格信息的数据帧
        """
        dict_good_blocks = et.extract_blocks_to_dict(self.path)
        dict_good = {}
        for good, good_block in dict_good_blocks.items():
            cost = et.search_numeric_attribute("cost", good_block)
            if cost is None:
                print(f"找不到{good}的基础价格，因此{good}将被忽略")
                continue
            dict_good[good] = float(cost)  # 价格是整数，为了兼容性考虑，这里记为浮点数
        return dict_good

    def create_empty_df_pm_goods(self) -> pd.DataFrame:
        """
        返回一个空的关于商品的数据帧，用于储存运算信息
        """
        df_pm_goods = self.df.copy()
        for column in [
            "input_add",
            "output_add",
            "input_cost",
            "output_cost",
            "input_mult",
            "output_mult",
        ]:
            df_pm_goods[column] = 0.0
        df_pm_goods = df_pm_goods.drop(columns=["cost"])
        return df_pm_goods


class POPTypesInfo:
    """
    以数据帧类型储存pop类型的名称和数量
    """

    def __init__(self, path=POP_TYPES_PATH):
        """
        :param path: pop类型文件的路径
        """
        self.path = path
        self.dict = self._create_dict()
        self.list = list(self.dict.keys())
        self.df = pd.DataFrame.from_dict(
            self.dict, orient="index", columns=["wage_weight"]
        )
        self.df_poptype_num = (
            self._create_df_poptype_num()
        )  # pop类型的名称和数量的数据帧

    def _create_dict(self) -> dict:
        """
        创建一个储存pop类型名称和数量信息的数据帧
        :return: 储存pop类型名称和数量信息的数据帧
        """
        dict_pop_blocks = et.extract_blocks_to_dict(self.path)
        dict_pop = {}
        for pop_type, pop_type_block in dict_pop_blocks.items():
            wage_weight = et.search_numeric_attribute("wage_weight", pop_type_block)
            if wage_weight is None:
                wage_weight = 0
                print(f"未找到{pop_type}的wage_weight，因此假定为0")
            dict_pop[pop_type] = float(wage_weight)
        return dict_pop

    def _create_df_poptype_num(self) -> pd.DataFrame:
        """
        :return: pop类型的名称和数量的数据帧
        """
        df_poptype_num = self.df.copy()
        df_poptype_num["number"] = 0
        df_poptype_num = df_poptype_num.drop(columns=["wage_weight"])
        return df_poptype_num


class PMInfo:
    """
    以字典类型储存生产方式的属性，包含商品和劳动力的信息
    """

    def __init__(
        self, goods_info: GoodsInfo, pop_types_info: POPTypesInfo, path=PM_PATH
    ):
        """
        :param goods_info: 商品信息的类
        :param pop_types_info: pop类型信息的类
        :param path: 生产方式文件的路径
        """
        self.path = path
        self.list_goods = goods_info.list
        self.list_pop_types = pop_types_info.list
        self.dict = self._create_dict(goods_info, pop_types_info)  # 生产方式的字典
        self.list = list(self.dict.keys())

    def _create_dict(self, goods_info, pop_types_info) -> PMDict:
        """
        获取生产方式的字典，格式如下
        dict_pm = {
            "pm1": {
                "df_pm_goods": df_pm_goods
                "df_pm_workforce": df_workforce
            }
        }
        :return : 生产方式的字典
        """
        dict_pm_blocks = et.extract_blocks_to_dict(self.path)
        dict_pm = {}
        for pm, pm_block in dict_pm_blocks.items():
            dict_pm[pm] = self._create_dict_pm_attributes(
                pm, pm_block, goods_info, pop_types_info
            )
        return dict_pm

    @staticmethod
    def _create_dict_pm_attributes(
        pm: str, pm_block: str, goods_info, pop_types_info
    ) -> PmAttributesDict:
        """
        获取给定生产方式的属性，然后以字典类型输出
        :param pm: 给定生产方式
        :param pm_block: 给定生产方式的代码块
        :return : 生产方式属性的字典
        """
        df_pm_goods = goods_info.create_empty_df_pm_goods()

        def update_df_pm_goods(df: pd.DataFrame, _io_type: str) -> pd.DataFrame:
            """
            获取给定pm的input或output需要的商品名称和数量，然后以数据帧类型输出
            :param df: 就是外层函数里的df_pm_goods
            :param _io_type: input或output
            :return : 商品名称和数量的数据帧，定义参考create_empty_df_pm_goods
            """
            list_goods_increase = re.findall(
                pm_goods_increase_pattern.format(_io_type), pm_block
            )  # pm_goods_increase_pattern不区分add还是mult
            for goods_increase in list_goods_increase:
                match_good = pm_goods_pattern.search(goods_increase)
                if not match_good:
                    print(f"{pm}中的{goods_increase}格式异常，无法捕获商品名称")
                    continue
                good = match_good.group(1)
                am_type = match_good.group(2)  # add 或 mult
                if am_type not in ["add", "mult"]:
                    print(f"{pm}中的{goods_increase}格式异常，无法确认add或mult")
                    continue
                if good not in df.index:  # 确保商品存在于商品的字典中
                    print(f"未找到{pm}中{good}的定义")
                    continue
                number = et.search_numeric_attribute(f"_{am_type}", goods_increase)
                if number is None:
                    print(
                        f"{pm}中的{goods_increase}格式异常，无法捕获{good}的{_io_type}数量"
                    )
                    continue
                # 商品数量大部分都是整数，但是自给农场是小数，这里统一以浮点数记录
                number = float(number)
                df.at[good, f"{_io_type}_{am_type}"] = number
            return df

        def create_dict_workforce(_pop_types_info) -> pd.DataFrame:
            """
            获取给定生产方式需要的劳动力种类和数量，然后以数据帧类型输出
            :return : 劳动力种类和数量的数据帧，包含全部劳动力类型
            """
            df_workforce = _pop_types_info.df_poptype_num.copy()
            list_workforce_add = pm_employment_pattern.findall(pm_block)
            for workforce_add in list_workforce_add:
                match_workforce = pm_employment_type_pattern.search(workforce_add)
                if not match_workforce:
                    print(f"{pm}中的{workforce_add}格式异常，无法捕获人群名称")
                    continue
                workforce = match_workforce.group(1)
                if workforce not in df_workforce.index:
                    print(f"未找到{pm}中{workforce}的定义")
                    continue
                number = et.search_numeric_attribute("_add", workforce_add)
                if number is None:
                    print(f"未找到{pm}中{workforce}的数量")
                    continue
                # 劳动力数量应该是整数
                number = int(number)
                df_workforce.at[workforce, "number"] = number
            return df_workforce

        for io_type in ["input", "output"]:
            df_pm_goods = update_df_pm_goods(df_pm_goods, io_type)
        return {
            "df_pm_goods": df_pm_goods,
            "df_pm_workforce": create_dict_workforce(pop_types_info),
        }

    def test_df_to_excel(self):
        """
        测试方法
        """
        dict_pm = {
            pm: list(
                self.dict[pm]["df_pm_goods"]["output"]
                - self.dict[pm]["df_pm_goods"]["input"]
            )
            + list(self.dict[pm]["df_pm_workforce"]["number"])
            for pm in self.dict
        }
        columns = self.list_goods + self.list_pop_types
        df = pd.DataFrame.from_dict(dict_pm, orient="index", columns=columns)
        df.to_excel("test\\pm.xlsx")


class PMGInfo:
    """
    以字典类型储存生产方式组的信息，包含下一级生产方式的信息
    """

    def __init__(self, dict_pm: dict, path=PMG_PATH):
        """
        :param dict_pm: 生产方式的字典
        :param path: 生产方式组文件的路径
        """
        self.path = path
        self.dict = self._create_dict(dict_pm)
        self.list = list(self.dict.keys())
        self.nested_dict = self._create_nested_dict(dict_pm)  # 生产方式组的嵌套字典

    def _create_dict(self, dict_pm) -> dict:
        """
        创建pmg的字典
        :return : pmg的字典
        """
        dict_pmg_blocks = et.extract_blocks_to_dict(self.path)
        dict_pmg = {}
        for pmg, pmg_block in dict_pmg_blocks.items():
            pm_block = et.extract_one_block(str_pm_in_pmg, pmg_block)
            if pm_block is None:
                print(f"{pmg}格式异常，因此无法找到任何生产方式")
                continue
            list_pm = []
            for pm in content_pattern.findall(pm_block):
                if pm in dict_pm:
                    list_pm.append(pm)
                else:
                    print(f"未找到{pmg}中{pm}的定义")
            dict_pmg[pmg] = list_pm
        return dict_pmg

    def _create_nested_dict(self, dict_pm) -> dict:
        return {
            pmg: {pm: dict_pm[pm] for pm in list_pm}
            for pmg, list_pm in self.dict.items()
        }

    def test_dict_to_excel(self):
        """
        测试方法
        """
        new_dict = {}
        max_length = max(len(list_pm) for list_pm in self.dict.values())
        for pmg, list_pm in self.dict.items():
            new_list = list_pm.copy()
            while len(new_list) < max_length:
                new_list.append(None)
            new_dict[pmg] = list_pm
        df = pd.DataFrame.from_dict(new_dict, orient="index", columns=range(max_length))
        df.to_excel("test\\pmg.xlsx")


class BuildingsInfo:
    """
    以字典方式储存建筑的信息，包含下一级生产方式组的信息
    """

    def __init__(
        self,
        nested_dict_pmg: dict,
        dict_pm: dict,
        df_goods: pd.DataFrame,
        df_pop_types: pd.DataFrame,
        dict_construction_cost: dict,
        path=BUILDINGS_PATH,
    ):
        self.path = path
        self.dict, self.dict_bc = self._create_dict(
            nested_dict_pmg, dict_construction_cost
        )
        self.list = list(self.dict.keys())
        self.nested_dict = self._create_nested_dict(nested_dict_pmg)
        self.dict_pm_combination = self._create_dict_pm_combination(
            dict_pm, df_goods, df_pop_types
        )  # 建筑的所有生产方式组合的字典

    def _create_dict(self, nested_dict_pmg, dict_construction_cost) -> tuple:
        dict_building_blocks = et.extract_blocks_to_dict(self.path)
        dict_buildings = {}
        dict_bc = {}  # 建筑建造花费的dict
        for building, building_block in dict_building_blocks.items():
            pmg_block = et.extract_one_block(str_pmg_in_building, building_block)
            if pmg_block is None:
                print(f"{building}格式异常，未找到任何生产方式组")
                continue
            list_pmg = []
            for pmg in content_pattern.findall(pmg_block):
                if pmg in nested_dict_pmg:
                    list_pmg.append(pmg)
                else:
                    print(f"未找到{building}中{pmg}的定义")
            rc = et.search_non_numeric_attribute(
                "required_construction", building_block
            )
            dict_buildings[building] = list_pmg
            if rc is not None:
                dict_bc[building] = dict_construction_cost[rc]
            else:
                dict_bc[building] = 0
        return dict_buildings, dict_bc

    def _create_nested_dict(self, nested_dict_pmg) -> dict:
        return {
            building: {pmg: nested_dict_pmg[pmg] for pmg in list_pmg}
            for building, list_pmg in self.dict.items()
        }

    def _create_dict_pm_combination(self, dict_pm, df_goods, df_pop_types) -> dict:
        """
        构造出如下字典，得到一个建筑各个生产方式组合的利润信息
        嵌套关系：建筑<-生产方式组合<-利润信息
        dict_building_pm_combination = {
            "building1": {
                "combination1": dict_profit_of_combination
            }
        }
        :return : 构造出的字典
        """

        def create_list_pm_combination(building) -> list:
            """
            获取给定建筑的所有生产方式组合的列表
            :return : 给定建筑所有生产方式组合的列表
            """
            list_list_pm = [
                list(self.nested_dict[building][pmg].keys())
                for pmg in self.nested_dict[building]
            ]  # 这是一个列表的列表
            return [
                list(_combination) for _combination in itertools.product(*list_list_pm)
            ]  # 这里_combination的类型是元组

        def create_dict_profit_of_combination(combination, building) -> dict:
            """
            计算给定生产方式组合的利润信息，以字典类型输出
            :return : 给定生产方式组合的利润信息的字典
            """

            def create_df_result(df_name: str) -> pd.DataFrame:
                result = pd.DataFrame()
                for pm in combination:
                    df = dict_pm[pm][df_name].copy()
                    if result.empty:
                        result = df
                    else:
                        result = result.add(df)
                return result

            result_good = create_df_result("df_pm_goods")
            result_workforce = create_df_result("df_pm_workforce")

            for io in ["input", "output"]:
                result_good[f"{io}_cost"] = (
                    result_good[f"{io}_add"]
                    * (1 + result_good[f"{io}_mult"])
                    * df_goods["cost"]
                )

            input_cost = result_good["input_cost"].sum()
            output_cost = result_good["output_cost"].sum()

            workforce = result_workforce["number"].sum()
            wage_weight = (
                float((result_workforce["number"] * df_pop_types["wage_weight"]).sum())
                / float(workforce)
                if float(workforce)
                else "Null"
            )

            profit = output_cost - input_cost
            per_capital_profit = profit / workforce * 52 if workforce else "Null"
            per_cc_profit = (
                profit / float(self.dict_bc[building])
                if self.dict_bc[building]
                else "Null"
            )
            rate_of_return = output_cost / input_cost if input_cost > 0 else "Null"
            return {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "workforce": workforce,
                "profit": profit,
                "per_capital_profit": per_capital_profit,
                "per_cc_profit": per_cc_profit,
                "rate_of_return": rate_of_return,
                "wage_weight": wage_weight,
            }

        return {
            building: {
                tuple(combination): create_dict_profit_of_combination(
                    combination, building
                )
                for combination in create_list_pm_combination(building)
            }
            for building in self.nested_dict.keys()
        }

    def test_dict_to_excel(self):
        """
        测试方法
        """
        rows = []
        for building, dict_combination in self.dict_pm_combination.items():
            for combination, dict_profit_of_combination in dict_combination.items():
                row = [building, str(combination)] + list(
                    dict_profit_of_combination.values()
                )
                rows.append(row)
        df = pd.DataFrame(
            rows,
            columns=[
                "building",
                "combination",
                "input_cost",
                "output_cost",
                "workforce",
                "profit",
                "per_capital_profit",
                "rate_of_return",
            ],
        )
        df.to_excel("test\\buildings.xlsx")


class LocalizationInfo:
    def __init__(self, dict_list_loc: dict, dict_pmg: dict, path=LOCALIZATION_PATH):
        """
        :param dict_list_loc: 被使用的本地化键的列表的字典
        :param path: 本地化文件的路径
        """
        self.path = path
        self.loc = et.Localization(path)  # 这部分被放在了easytool中
        self.dict_all = self.loc.dict_all
        self.dict = self._calibrate_dict(dict_list_loc)  # 本地化的字典
        self.list_automation_pm = self._create_list_automation_pm(
            dict_pmg
        )  # 自动化生产方式的列表

    def _create_list_automation_pm(self, dict_pmg: dict) -> list:
        """
        给出属于自动化生产方式组的生产方式
        :return : 属于自动化生产方式组的生产方式的列表
        """
        return [
            pm
            for pmg, list_pm in dict_pmg.items()
            if self.dict[pmg] == "自动化"
            for pm in list_pm
        ]

    def _calibrate_dict(self, dict_list_loc) -> dict:
        loc_dict = self.loc.create_dict_used(dict_list_loc)
        for key, value in loc_dict.items():
            if (
                value
                == "#This is a dummy building that serve no gameplay mechanical purpose but still need to be reacted to by city hub graphics. It (and this text) should never show up in the UI#!"
            ):
                loc_dict[key] = "dummy_building"
        return loc_dict

    def test_dict_to_json(self):
        with open("test\\loc_dict.json", "w", encoding="utf-8-sig") as json_file:
            json.dump(self.dict, json_file, ensure_ascii=False, indent=4)


class BuildingProfitCalculator:
    """
    计算建筑的利润信息，并以excel格式输出
    """

    def __init__(self):
        self.script_values_info = ScripValuesInfo()
        self.goods_info = GoodsInfo()
        self.pop_types_info = POPTypesInfo()
        self.pm_info = PMInfo(self.goods_info, self.pop_types_info)
        self.pmg_info = PMGInfo(self.pm_info.dict)
        self.buildings_info = BuildingsInfo(
            self.pmg_info.nested_dict,
            self.pm_info.dict,
            self.goods_info.df,
            self.pop_types_info.df,
            self.script_values_info.dict_construction_cost,
        )
        dict_list_loc = {
            "building": self.buildings_info.list,
            "pmg": self.pmg_info.list,
            "pm": self.pm_info.list,
        }
        self.localization_info = LocalizationInfo(dict_list_loc, self.pmg_info.dict)

    def to_excel(self):
        """
        用中文将dict_building_pm_combination以excel形式输出
        """
        column_info = [
            "投入",
            "产出",
            "劳动力",
            "利润",
            "人均利润",
            "利润/建造力",
            "回报率",
            "工资倍率",
        ]
        # 按建筑输出
        for (building, dict_combination) in self.buildings_info.dict_pm_combination.items():
            rows = []
            for combination, combination_profits in dict_combination.items():
                row = [self.localization_info.dict[pm] for pm in list(combination)]
                row.extend(list(combination_profits.values()))
                rows.append(row)
            column = [self.localization_info.dict[pmg] for pmg in self.buildings_info.nested_dict[building].keys()]
            column.extend(column_info)
            df = pd.DataFrame(rows, columns=column)
            df.to_excel(
                f"output\\buildings\\{self.localization_info.dict[building]}-{building}.xlsx",
                index=False,
            )
            print(f"{self.localization_info.dict[building]}-{building}.xlsx 输出成功")
        # 判断以何种方式输出总表
        max_len_pmg = max(
            len(list_pmg) for list_pmg in self.buildings_info.dict.values()
        )
        is_pmg_count_leq_4 = bool(max_len_pmg <= 4)
        rows = []
        if is_pmg_count_leq_4:
            column_1 = ["基础", "次要", "自动化", "其他"]
        else:
            column_1 = list(range(max_len_pmg))
        column_0 = ["建筑"] + column_1 + column_info
        for (building, dict_combination) in self.buildings_info.dict_pm_combination.items():
            for combination, combination_profits in dict_combination.items():
                row = [self.localization_info.dict[building]]
                list_pm = list(combination)
                if is_pmg_count_leq_4:
                    # 确保list_pm的长度至少为4，不需要检测是否为负数
                    list_pm += [""] * (4 - len(list_pm))
                    # 检测有无生产方式属于自动化生产方式
                    automation_pm = next((pm for pm in list_pm if pm in self.localization_info.list_automation_pm), None)  # 这里使用了一个生成表达式
                    if automation_pm is not None:
                        list_pm.remove(automation_pm)
                        list_pm.insert(2, automation_pm)  # 通过insert方法重新排序
                else:
                    list_pm += [""] * (max_len_pmg - len(list_pm))
                list_pm_chinese = [
                    self.localization_info.dict[pm] if pm else "" for pm in list_pm
                ]
                row.extend(list_pm_chinese)
                row.extend(list(combination_profits.values()))
                rows.append(row)
        df_summary_table = pd.DataFrame(rows, columns=column_0)
        df_summary_table.to_excel(f"output\\buildings\\总表.xlsx", index=False)
        print("总表.xlsx 输出成功")


def test():
    """
    仅用于测试
    """
    script_values_info = ScripValuesInfo()
    goods_info = GoodsInfo()
    goods_info.df.to_excel("test\\goods.xlsx")
    pop_types_info = POPTypesInfo()
    pop_types_info.df_poptype_num.to_excel("test\\pop_types.xlsx")
    pm_info = PMInfo(goods_info, pop_types_info)
    pm_info.test_df_to_excel()
    pmg_info = PMGInfo(pm_info.dict)
    pmg_info.test_dict_to_excel()
    buildings_info = BuildingsInfo(
        pmg_info.nested_dict,
        pm_info.dict,
        goods_info.df,
        pop_types_info.df,
        script_values_info.dict_construction_cost,
    )
    buildings_info.test_dict_to_excel()
    dict_list = {
        "building": buildings_info.list,
        "pmg": pmg_info.list,
        "pm": pm_info.list,
    }
    localization_info = LocalizationInfo(dict_list, pmg_info.dict)
    localization_info.test_dict_to_json()
    print(localization_info.list_automation_pm)


def calculator():
    """
    主程序
    """
    building_profit_calculator = BuildingProfitCalculator()
    building_profit_calculator.to_excel()


if __name__ == "__main__":
    calculator()

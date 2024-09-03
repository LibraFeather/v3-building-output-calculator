import pandas as pd
import itertools
from collections import Counter

from tree import BuildingInfoTree
from constants.path import OUTPUT_PATH


class Calculator:
    def __init__(self):
        building_info_tree_complex = BuildingInfoTree()
        self.goods_info = building_info_tree_complex.goods_info
        self.pop_type_info = building_info_tree_complex.pop_types_info

        self.building_info_tree = building_info_tree_complex.tree
        self.building_output_info_list = self.__generate_building_output_info_list()

        self.COLUMN_HEADERS = {
            'input_cost': '商品投入总价值',
            'output_cost': '商品产出总价值',
            'workforce_population': '劳动力总人数',
            'profit': '利润',
            'per_capita_profit': '人均利润',
            'per_cc_profit': '利润/建造力',
            'rate_of_return': '回报率',
            'wage_weight': '工资倍率'
        }
        self.automation_pm_list = building_info_tree_complex.automation_pm_list

    # ------------------------------------------------------------------------------------------
    # __generate_one_line_data_list_for_single_building部分
    def __generate_one_line_data_list_for_single_building(self, building) -> list:
        one_line_data_list = []
        pmgs_list = [pmg.localization_key for pmg in building.children]  # 这里使用localization_key防止重复
        combinations = itertools.product(*(node.children for node in building.children))

        for combination in combinations:
            one_line_data = self.__generate_one_line_data(combination, pmgs_list)
            one_line_data_finished = self.__calculate_data(one_line_data, building)
            one_line_data_list.append(one_line_data_finished)
        return one_line_data_list

    @staticmethod
    def __generate_one_line_data(combination: tuple, pmgs_list: list) -> dict:
        def check_workforce_positive(workforce_dict: dict) -> dict:
            for _, v in workforce_dict.items():
                if v < 0:
                    workforce_dict[_] = 0
            return workforce_dict

        good_input = Counter()  # pycharm会记住嵌套字典的变量类型，所以这里把Counter单独拿出来处理
        good_output = Counter()
        workforce = Counter()
        one_line_data = {
            "raw_data": {'good_input': {}, 'good_output': {}, 'workforce': {}},
            "pm_data": {},
            "processed_data": {}
        }

        for i in range(len(pmgs_list)):
            good_input.update(combination[i].good_input)
            good_output.update(combination[i].good_output)
            workforce.update(combination[i].workforce)
            one_line_data["pm_data"][pmgs_list[i]] = combination[i].localization_value

        one_line_data["raw_data"]['good_input'] = dict(good_input)
        one_line_data["raw_data"]['good_output'] = dict(good_output)
        one_line_data["raw_data"]['workforce'] = check_workforce_positive(dict(workforce))  # 将负值变为0
        return one_line_data

    def __calculate_data(self, one_line_data: dict, building) -> dict:
        """
        #! 计算8项：商品总投入/商品总产出/劳动力总数/利润/人均利润/利润除以建造力/回报率/工资倍率
        利润 = 商品产出总产值 - 商品投入总产值
        人均利润 = 利润/劳动力人数总和 * 52
        利润/建造力 = 利润/建筑建造力
        回报率 = 商品产出总产值/商品投入总产值
        工资倍率 = 劳动力工资权重的加权平均
        """
        input_cost = sum(one_line_data["raw_data"]['good_input'][item] * self.goods_info[item]
                         for item in one_line_data["raw_data"]['good_input'])
        output_cost = sum(one_line_data["raw_data"]['good_output'][item] * self.goods_info[item]
                          for item in one_line_data["raw_data"]['good_output'])
        workforce_population = sum(one_line_data["raw_data"]['workforce'].values())
        profit = output_cost - input_cost
        per_capita_profit = profit / workforce_population * 52 if workforce_population else 'Null'
        per_cc_profit = profit / building.building_cost if building.building_cost else 'Null'
        rate_of_return = output_cost / input_cost if input_cost > 0 else 'Null'
        wage_weight = sum(one_line_data["raw_data"]['workforce'][item] * self.pop_type_info[item] for item in
                          one_line_data["raw_data"][
                              'workforce']) / workforce_population if workforce_population else 'Null'

        one_line_data["processed_data"]['input_cost'] = input_cost
        one_line_data["processed_data"]['output_cost'] = output_cost
        one_line_data["processed_data"]['workforce_population'] = workforce_population
        one_line_data["processed_data"]['profit'] = profit
        one_line_data["processed_data"]['per_capita_profit'] = per_capita_profit
        one_line_data["processed_data"]['per_cc_profit'] = per_cc_profit
        one_line_data["processed_data"]['rate_of_return'] = rate_of_return
        one_line_data["processed_data"]['wage_weight'] = wage_weight
        del one_line_data["raw_data"]
        return one_line_data

    # ------------------------------------------------------------------------------------------
    def __generate_building_output_info_list(self) -> list:
        return [(building, self.__generate_one_line_data_list_for_single_building(building)) for building in
                self.building_info_tree]

    def __transfer_dict_to_df(self, building_info_list, building):
        pmg_list = building.children
        column_pmg = {pmg.localization_key: pmg.localization_value for pmg in pmg_list}
        colum_rename = column_pmg | self.COLUMN_HEADERS
        rows = []
        for building_info in building_info_list:
            rows.append(building_info["pm_data"] | building_info["processed_data"])
        building_info_df = pd.DataFrame(building_info_list)
        building_info_df.rename(columns=colum_rename, inplace=True)
        building_info_df.to_excel(
            f'{OUTPUT_PATH}\\buildings\\{building.localization_value}_{building.localization_key}.xlsx', index=False)
        print(f'{building.localization_value}_{building.localization_key}输出成功！')

    def output_every_building(self):
        for building, one_line_data_list in self.building_output_info_list:
            self.__transfer_dict_to_df(one_line_data_list, building)

    def output_all_buildings(self):
        rows = []
        max_len_pmg = max(
            len(one_line_data["pm_data"]) for building_info in self.building_output_info_list for one_line_data in
            building_info[1])
        is_pmg_count_leq_4 = bool(max_len_pmg <= 4)
        if is_pmg_count_leq_4:
            column_4pm = ["基础", "次要", "自动化", "其他"]
        else:
            column_4pm = list(range(max_len_pmg))
        for building, building_info_list in self.building_output_info_list:
            for one_line_data in building_info_list:
                pm_list = list(one_line_data["pm_data"].values())
                pm_list += [""] * (max_len_pmg - len(pm_list))  # 确保list_pm等长
                if is_pmg_count_leq_4:
                    # 将自动化生产方式重新排序
                    automation_pm = next((pm for pm in pm_list if pm in self.automation_pm_list), None)
                    if automation_pm is not None:
                        pm_list.remove(automation_pm)
                        pm_list.insert(2, automation_pm)
                pm_data = {column_4pm[i]: pm_list[i] for i in range(len(column_4pm))}
                row = {"建筑": building.localization_value} | pm_data | one_line_data["processed_data"]
                rows.append(row)
        summary_table_df = pd.DataFrame(rows)
        summary_table_df.rename(columns=self.COLUMN_HEADERS, inplace=True)
        summary_table_df.to_excel(f"{OUTPUT_PATH}\\buildings\\00_总表.xlsx", index=False)
        print("总表.xlsx 输出成功")


if __name__ == '__main__':
    calculator = Calculator()
    calculator.output_every_building()
    calculator.output_all_buildings()

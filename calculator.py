import pandas as pd
import itertools
from collections import Counter

from tree import BuildingInfoTree


class Calculator:
    def __init__(self):
        building_info_tree_complex = BuildingInfoTree()
        self.goods_info = building_info_tree_complex.goods_info
        self.pop_type_info = building_info_tree_complex.pop_types_info
        self.building_info_tree = building_info_tree_complex.tree

    def generate_info_dict_for_single_building(self, building):
        building_info_list = []
        pmgs_localization_list = [pmg.localization_key for pmg in building.children]
        combinations = list(itertools.product(*(node.children for node in building.children)))

        for combination in combinations:
            one_line_data = self.generate_one_line_data(combination, pmgs_localization_list)
            one_line_data_finished = self.calculate_data(one_line_data, building)
            building_info_list.append(one_line_data_finished)
        return building_info_list

    def generate_one_line_data(self, combination, pmgs_localization_list):
        one_line_data = {'good_input': Counter(), 'good_output': Counter(), 'workforce': Counter()}
        for i in range(len(pmgs_localization_list)):
            one_line_data[pmgs_localization_list[i]] = combination[i].localization_key
            one_line_data['good_input'].update(combination[i].good_input)
            one_line_data['good_output'].update(combination[i].good_output)
            one_line_data['workforce'].update(combination[i].workforce)
        one_line_data['good_input'] = dict(one_line_data['good_input'])
        one_line_data['good_output'] = dict(one_line_data['good_output'])
        one_line_data['workforce'] = dict(one_line_data['workforce'])
        one_line_data['workforce'] = self.check_workforce_positive(one_line_data['workforce'])

        return one_line_data

    def calculate_data(self, one_line_data, building):
        """
        #! 计算8项：商品总投入/商品总产出/劳动力总数/利润/人均利润/利润除以建造力/回报率/工资倍率
        利润 = 商品产出总产值 - 商品投入总产值
        人均利润 = 利润/劳动力人数总和 * 52
        利润/建造力 = 利润/建筑建造力
        回报率 = 商品产出总产值/商品投入总产值
        工资倍率 = 劳动力工资权重的加权平均
        """
        input_cost = sum(one_line_data['good_input'].get(item, 0) * self.goods_info.get(item, 0)
                         for item in one_line_data['good_input'])
        output_cost = sum(one_line_data['good_output'].get(item, 0) * self.goods_info.get(item, 0)
                          for item in one_line_data['good_output'])
        workforce_population = sum(one_line_data['workforce'].values())
        profit = output_cost - input_cost
        per_capita_profit = profit / workforce_population * 52 if workforce_population else 'Null'
        per_cc_profit = profit / building.building_cost if building.building_cost else 'Null'
        rate_of_return = output_cost / input_cost if input_cost > 0 else 'Null'
        wage_weight = sum(one_line_data['workforce'].get(item, 0) * self.pop_type_info.get(item, 0)
                          for item in one_line_data['workforce']) / workforce_population \
            if workforce_population else 'Null'

        one_line_data['input_cost'] = input_cost
        one_line_data['output_cost'] = output_cost
        one_line_data['workforce_population'] = workforce_population
        one_line_data['profit'] = profit
        one_line_data['per_capita_profit'] = per_capita_profit
        one_line_data['per_cc_profit'] = per_cc_profit
        one_line_data['rate_of_return'] = rate_of_return
        one_line_data['wage_weight'] = wage_weight
        return one_line_data

    @staticmethod
    def transfer_dict_to_df(building_info_list, building):
        building_info_df = pd.DataFrame(building_info_list)
        column_headers = {
            'input_cost': '商品投入总价值',
            'output_cost': '商品产出总价值',
            'workforce_population': '劳动力总人数',
            'profit': '利润',
            'per_capita_profit': '人均利润',
            'per_cc_profit': '利润/建造力',
            'rate_of_return': '回报率',
            'wage_weight': '工资倍率'
        }
        building_info_df.rename(columns=column_headers, inplace=True)
        building_info_df.iloc[:, 3:].to_excel(f'output\\buildings\\{building.localization_key}.xlsx', index=False)
        print(f'{building.localization_key}输出成功！')

    @staticmethod
    def check_workforce_positive(workforce_dict: dict):
        for _, v in workforce_dict.items():
            if v < 0:
                workforce_dict[_] = 0
        return workforce_dict


if __name__ == '__main__':
    calculator = Calculator()
    test_dict = calculator.generate_info_dict_for_single_building(calculator.building_info_tree[0])
    calculator.transfer_dict_to_df(test_dict, calculator.building_info_tree[0])

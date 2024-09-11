"""
数据计算类
"""
import pandas as pd
import itertools
from collections import Counter

from models.tree import BuildingInfoTree
from constants.path import OUTPUT_PATH
import utils.error as error


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
            'wage_weight': '工资倍率',
            'era': '时代要求',
            'highest_tech': '最高科技要求',
            'techs_all': '全部科技要求',
            'unlocking_laws': '法律要求',
            'disallowing_laws': '法律限制',
            'unlocking_identity': '核心理念支柱要求',
            'unlocking_principles': '原则要求'
        }
        self.COLUMN_GOODS = {
            good: f"{good_info.loc_value}_{good_info.loc_key}"
            for good, good_info in self.goods_info.items()
        }
        self.automation_pm_list = building_info_tree_complex.automation_pm_list

    # ------------------------------------------------------------------------------------------
    def __generate_one_line_data_list_for_single_building(self, building) -> list:
        one_line_data_list = []
        combinations = itertools.product(*(node.children for node in building.children))

        for combination in combinations:
            pms_set = {pm.loc_key for pm in combination}
            # 检查每个 pm 的 unlocking_production_methods 是否与 pms_set 有交集，除非它是空集
            can_generate_data = all(
                pm.unlocking_production_methods == [] or set(pm.unlocking_production_methods) & pms_set
                for pm in combination
            )

            if can_generate_data:
                pmgs_list = [pmg.loc_key for pmg in building.children]  # 这里使用localization_key防止重复
                one_line_data = self.__generate_one_line_data(dict(zip(pmgs_list, combination)), building)
                one_line_data = self.__calculate_data(one_line_data, building)
                one_line_data_list.append(one_line_data)
        return one_line_data_list

    def __generate_one_line_data(self, pmg_to_combination_map: dict, building) -> dict:
        def check_workforce_positive(workforce_dict: dict) -> dict:
            for k, v in workforce_dict.items():
                if v < 0:
                    workforce_dict[k] = 0
            return workforce_dict

        def calculate_good(goods_add, goods_mult):
            for good in goods_add:
                if good in goods_mult:
                    mult = 1 + goods_mult[good]
                    goods_add[good] = goods_add[good] * mult if mult > 0 else 0
            return goods_add

        def add_object_to_list(objects_list: list, new_list: list) -> None:
            for _object in objects_list:
                if _object not in new_list:
                    new_list.append(_object)

        goods_input_add = Counter()  # pycharm会记住嵌套字典的变量类型，所以这里把Counter单独拿出来处理
        goods_output_add = Counter()
        goods_input_mult = Counter()
        goods_output_mult = Counter()
        workforce = Counter()
        one_line_data = {'raw_data': {}, 'pm_data': {}, 'processed_data': {}, 'other_data': {}, 'goods_data': {}}

        # 处理建筑本身的科技需求
        if building.unlocking_technologies:
            era = max(building.unlocking_technologies, key=lambda _tech: _tech.era).era
            highest_tech = []
            for tech in building.unlocking_technologies:
                if tech.era == era and tech not in highest_tech:
                    highest_tech.append(tech)
        else:
            era = 0
            highest_tech = []

        subsistence_output = 0

        techs_all = building.unlocking_technologies.copy()
        unlocking_principles = []
        unlocking_identity = []
        unlocking_laws = []
        disallowing_laws = []

        for pmg, pm in pmg_to_combination_map.items():
            goods_input_add.update(pm.goods_add['input'])
            goods_output_add.update(pm.goods_add['output'])
            goods_input_mult.update(pm.goods_mult['input'])
            goods_output_mult.update(pm.goods_mult['output'])
            workforce.update(pm.workforce)
            subsistence_output += pm.subsistence_output

            one_line_data['pm_data'][pmg] = pm.loc_value
            for tech in pm.unlocking_technologies:
                if tech.era > era:
                    era = tech.era
                    highest_tech = [tech]
                elif tech.era == era and tech not in highest_tech:
                    highest_tech.append(tech)
                if tech not in techs_all:
                    techs_all.append(tech)
            add_object_to_list(pm.unlocking_principles, unlocking_principles)
            if pm.unlocking_identity is not None:
                unlocking_identity.append(pm.unlocking_identity)
            add_object_to_list(pm.unlocking_laws, unlocking_laws)
            add_object_to_list(pm.disallowing_laws, disallowing_laws)

        one_line_data['raw_data'] = {
            'goods_input': calculate_good(dict(goods_input_add), dict(goods_input_mult)),
            'goods_output': calculate_good(dict(goods_output_add), dict(goods_output_mult)),
            'workforce': check_workforce_positive(dict(workforce)),  # 将负值变为0
            'subsistence_output': subsistence_output
        }

        one_line_data['other_data'] = {
            'era': era,
            'highest_tech': ' '.join([tech.loc_value for tech in highest_tech]),
            'techs_all': ' '.join([tech.loc_value for tech in techs_all]),
            'unlocking_principles': ' '.join([principle.loc_value for principle in unlocking_principles]),
            'unlocking_identity': ' '.join([identity.loc_value for identity in unlocking_identity]),
            'unlocking_laws': ' '.join([law.loc_value for law in unlocking_laws]),
            'disallowing_laws': ' '.join([law.loc_value for law in disallowing_laws])
        }

        one_line_data['goods_data'] = {
            good_info.loc_key:
                one_line_data['raw_data']['goods_output'].get(good, 0)
                - one_line_data['raw_data']['goods_input'].get(good, 0)
            for good, good_info in self.goods_info.items()
        }
        return one_line_data

    def __calculate_data(self, one_line_data: dict, building) -> dict:
        goods_input = one_line_data['raw_data']['goods_input']
        goods_output = one_line_data['raw_data']['goods_output']
        workforce = one_line_data['raw_data']['workforce']
        subsistence_output = one_line_data['raw_data']['subsistence_output']

        input_cost = sum(goods_input[good] * self.goods_info[good].cost for good in goods_input)
        output_cost = sum(goods_output[good] * self.goods_info[good].cost for good in goods_output)
        workforce_population = sum(workforce.values())
        profit = (output_cost - input_cost
                  + sum(subsistence_output * workforce[pop_type] * self.pop_type_info[pop_type].subsistence_income
                        for pop_type in workforce) / 52)
        per_capita_profit = profit / workforce_population * 52 if workforce_population else 'Null'
        per_cc_profit = profit / building.required_construction if building.required_construction else 'Null'
        rate_of_return = output_cost / input_cost if input_cost > 0 else 'Null'
        wage_weight = (sum(workforce[pop_type] * self.pop_type_info[pop_type].wage_weight for pop_type in workforce)
                       / workforce_population) if workforce_population else 'Null'

        one_line_data['processed_data'] = {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'workforce_population': workforce_population,
            'profit': profit,
            'per_capita_profit': per_capita_profit,
            'per_cc_profit': per_cc_profit,
            'rate_of_return': rate_of_return,
            'wage_weight': wage_weight
        }
        del one_line_data['raw_data']
        return one_line_data

    # ------------------------------------------------------------------------------------------
    def __generate_building_output_info_list(self) -> list:
        return [(building, self.__generate_one_line_data_list_for_single_building(building)) for building in
                self.building_info_tree]

    def __transfer_dict_to_df(self, one_line_data_list, building):
        name = (f"{building.building_group_display.loc_value}"
                f"_{building.loc_value}_{building.loc_key}.xlsx")
        name = error.check_filename(name)
        column_pmg = {pmg.loc_key: f"{pmg.loc_value}_{pmg.loc_key}"
                      for pmg in building.children}
        colum_rename = column_pmg | self.COLUMN_HEADERS | self.COLUMN_GOODS
        rows = []
        for one_line_data in one_line_data_list:
            row = one_line_data['pm_data'] | one_line_data['processed_data'] | one_line_data['other_data'] | \
                  one_line_data['goods_data']
            rows.append(row)

        if not rows:
            error.can_not_output(name)
            return None

        building_info_df = pd.DataFrame(rows)

        for good_info in self.goods_info.values():
            if (building_info_df[good_info.loc_key] == 0).all():
                building_info_df.drop(good_info.loc_key, axis=1, inplace=True)
        for key in list(self.COLUMN_HEADERS.keys())[9:]:
            if (building_info_df[key] == '').all():
                building_info_df.drop(key, axis=1, inplace=True)

        building_info_df.rename(columns=colum_rename, inplace=True)
        building_info_df.to_excel(
            f"{OUTPUT_PATH}\\buildings\\{name}", index=False)
        print(f'{name}输出成功')

    def output_every_building(self):
        for building, one_line_data_list in self.building_output_info_list:
            self.__transfer_dict_to_df(one_line_data_list, building)

    def output_all_buildings(self):
        name = "00_总表.xlsx"
        rows = []
        try:
            max_len_pmg = max(
                len(one_line_data['pm_data']) for building_info in self.building_output_info_list for one_line_data in
                building_info[1])
        except ValueError:
            error.can_not_output(name)
            return None

        is_pmg_count_leq_4 = bool(max_len_pmg <= 4)
        if is_pmg_count_leq_4:
            column_4pm = ['基础', '次要', '自动化', '其他']
            max_len_pmg = 4
        else:
            column_4pm = list(range(max_len_pmg))
        for building, building_info_list in self.building_output_info_list:
            for one_line_data in building_info_list:
                pm_list = list(one_line_data['pm_data'].values())
                pm_list += [''] * (max_len_pmg - len(pm_list))  # 确保list_pm等长
                if is_pmg_count_leq_4:
                    # 将自动化生产方式重新排序
                    automation_pm = next((pm for pm in pm_list if pm in self.automation_pm_list), None)
                    if automation_pm is not None:
                        pm_list.remove(automation_pm)
                        pm_list.insert(2, automation_pm)
                pm_data = {column_4pm[i]: pm_list[i] for i in range(len(column_4pm))}
                row = {'建筑组': building.building_group_display.loc_value} | {
                    '建筑': building.loc_value} | pm_data | one_line_data['processed_data'] | one_line_data[
                          'other_data'] | one_line_data['goods_data']
                rows.append(row)
        summary_table_df = pd.DataFrame(rows)
        summary_table_df.rename(columns=self.COLUMN_HEADERS | self.COLUMN_GOODS, inplace=True)
        summary_table_df.to_excel(f"{OUTPUT_PATH}\\buildings\\{name}", index=False)
        print(f"{name}输出成功")

    def output(self):
        self.output_every_building()
        self.output_all_buildings()

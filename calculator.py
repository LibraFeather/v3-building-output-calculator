import pandas as pd
import itertools

from tree import BuildingInfoTree

class Calculator:
    def __init__(self):
        building_info_tree_complex = BuildingInfoTree()
        self.goods_info = building_info_tree_complex.goods_info
        self.pop_type_info = building_info_tree_complex.pop_types_info
        self.building_info_tree = building_info_tree_complex.tree

    def generate_info_dict_for_singal_building(self):
        return 1

    def pm_permutation_combination(self):
        return 1
    
    def calculate_data(self):
        return 1
    
    def transfer_dict_to_df(self):
        return 1



if __name__ == '__main__':
    calculator = Calculator()
    print(calculator)
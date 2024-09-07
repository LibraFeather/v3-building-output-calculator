import re
from collections import Counter

import utils.textproc as tp
import utils.path_to_dict as ptd

# TODO 按照类型排列
import constants.str as s
import models.model as mm
from config.goods_cost import GOODS_COST_OFFSET


class BuildingInfoTree:
    def __init__(self):
        game_objet_need = ["buildings", "goods", "laws", "pop_types", "power_bloc_identities", "power_bloc_principles",
                           "production_method_groups", "production_methods", "script_values", "technologies"]
        game_object_dict = ptd.get_game_object_dict(game_objet_need)

        self.localization_info = self.__get_localization_info(game_object_dict)

        self.scrit_values_info = game_object_dict["script_values"]
        self.buildings_info = self.__get_buildings_info(game_object_dict["buildings"])
        self.goods_info = self.__get_goods_info(game_object_dict["goods"])
        self.laws_info = game_object_dict["laws"]
        self.pop_types_info = self.__get_pops_info(game_object_dict["pop_types"])
        self.identities_info = game_object_dict["power_bloc_identities"]
        self.principles_info = game_object_dict["power_bloc_principles"]
        self.pmgs_info = self.__get_pmgs_info(game_object_dict["production_method_groups"])
        self.pms_info = self.__get_pms_info(game_object_dict["production_methods"])
        self.technologies_info = self.__get_technologies_info(game_object_dict["technologies"])

        self.automation_pm_list = self.__get_automation_pm_list()

        self.tree = self.generate_tree()

    @staticmethod
    def __get_technologies_info(technology_blocks_dict) -> dict:
        technologies_dict = {}
        for technology in technology_blocks_dict:
            if s.ERA in technology_blocks_dict[technology]:
                era = technology_blocks_dict[technology][s.ERA]
                technologies_dict[technology] = tp.get_era_num(technology, era)
            else:
                print(f"{technology}不存在{s.ERA}，因此假定为0")
                technologies_dict[technology] = 0
        return technologies_dict

    # ! 预备部分，创建各项存储字典
    @staticmethod
    def __get_goods_info(good_blocks_dict) -> dict:
        """
        商品名称: 基础价格
        """
        goods_dict = {}
        for good in good_blocks_dict:
            if s.COST in good_blocks_dict[good]:
                goods_dict[good] = good_blocks_dict[good][s.COST] * GOODS_COST_OFFSET.get(good, 1.0)
            else:
                goods_dict[good] = 0
                print(f"未找到{good}的{s.COST}，因此假定其为0")
        return goods_dict

    def __get_pops_info(self, pop_blocks_dict) -> dict:
        pops_dict = {}
        for pop_type in pop_blocks_dict:
            if s.WAGE_WEIGHT in pop_blocks_dict[pop_type]:
                wage_weight = pop_blocks_dict[pop_type][s.WAGE_WEIGHT]
            else:
                wage_weight = 0
                print(f"未找到{pop_type}的{s.WAGE_WEIGHT}，因此假定其为0")
            if s.SUBSISTENCE_INCOME in pop_blocks_dict[pop_type]:
                subsistence_income = True
            else:
                subsistence_income = False
            pops_dict[pop_type] = mm.POPTypeNode(
                localization_key=pop_type,
                localization_value=self.localization_info[pop_type],
                wage_weight=wage_weight,
                subsistence_income=subsistence_income
            )
        return pops_dict

    def __get_buildings_info(self, building_blocks_dict) -> dict:
        """
        建筑: 建造花费， 生产方式组
        """

        # TODO 这里看起来需要重构
        def building_cost_converter(building_cost_str):
            if isinstance(building_cost_str, str):
                if building_cost_str not in self.scrit_values_info:
                    print(f"{building_cost_str}无定义，假定为0")
                    return 0
                if not isinstance(self.scrit_values_info[building_cost_str], (int, float)):
                    print(f"{building_cost_str}的值{self.scrit_values_info[building_cost_str]}不是数值，假定为0")
                    return 0
                return self.scrit_values_info[building_cost_str]
            if isinstance(building_cost_str, (int, float)):
                return building_cost_str
            print(f"{building_cost_str}格式异常，假定为0")
            return 0

        buildings_dict = {}
        for building in building_blocks_dict:
            if s.REQUIRED_CONSTRUCTION in building_blocks_dict[building]:
                building_cost = building_cost_converter(
                    building_blocks_dict[building][s.REQUIRED_CONSTRUCTION])
            else:
                building_cost = 0.0
                # print(f"未找到{building}的{REQUIRED_CONSTRUCTION_STR}，因此假定其为0.0")
            if s.PRODUCTION_METHOD_GROUPS in building_blocks_dict[building]:
                pmgs_list = building_blocks_dict[building][s.PRODUCTION_METHOD_GROUPS]
            else:
                pmgs_list = []
                print(f"{building}格式异常，未找到任何生产方式组")
            buildings_dict[building] = {'cost': building_cost, 'pmgs': pmgs_list}
        return buildings_dict

    @staticmethod
    def __get_pmgs_info(pmg_blocks_dict) -> dict:
        """
        生产方式组: 生产方式
        """
        pmgs_dict = {}
        for pmg in pmg_blocks_dict:
            if s.PRODUCTION_METHODS in pmg_blocks_dict[pmg]:
                pms_list = pmg_blocks_dict[pmg][s.PRODUCTION_METHODS]
            else:
                pms_list = []
                print(f"{pmg}格式异常，未找到任何生产方式")
            pmgs_dict[pmg] = pms_list
        return pmgs_dict

    def __get_pms_info(self, pm_blocks_dict) -> dict:
        pms_dict = {}
        for pm in pm_blocks_dict:

            pms_dict[pm] = {
                "add": {"input": {}, "output": {}},
                "mult": {"input": {}, "output": {}},
                "employment": {},
                "subsistence_output": 0
            }

            pms_dict[pm][s.UNLOCKING_TECHNOLOGIES] = pm_blocks_dict[pm].get(s.UNLOCKING_TECHNOLOGIES, [])
            pms_dict[pm][s.UNLOCKING_PRODUCTION_METHODS] = pm_blocks_dict[pm].get(s.UNLOCKING_PRODUCTION_METHODS, [])
            pms_dict[pm][s.UNLOCKING_PRINCIPLES] = pm_blocks_dict[pm].get(s.UNLOCKING_PRINCIPLES, [])
            pms_dict[pm][s.UNLOCKING_LAWS] = pm_blocks_dict[pm].get(s.UNLOCKING_LAWS, [])
            pms_dict[pm][s.DISALLOWING_LAWS] = pm_blocks_dict[pm].get(s.DISALLOWING_LAWS, [])
            identity = pm_blocks_dict[pm].get(s.UNLOCKING_IDENTITY)
            pms_dict[pm][s.UNLOCKING_IDENTITY] = [identity] if identity is not None else []

            if s.BUILDING_MODIFIERS not in pm_blocks_dict[pm]:
                # print(f"{pm}中缺少{BUILDING_MODIFIERS_STR}")
                continue

            # TODO 这一段对modifier的处理需要重构
            modifier_dict = Counter()
            if s.WORKFORCE_SCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                modifier_dict.update(tp.calibrate_modifier_dict(
                    dict(pm_blocks_dict[pm][s.BUILDING_MODIFIERS][s.WORKFORCE_SCALED])))  # 防止空值
            if s.LEVEL_SCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                modifier_dict.update(
                    tp.calibrate_modifier_dict(dict(pm_blocks_dict[pm][s.BUILDING_MODIFIERS][s.LEVEL_SCALED])))
            modifier_dict = tp.parse_modifier_dict(dict(modifier_dict))
            for modifier, modifier_info in modifier_dict.items():
                if modifier_info["am_type"] != "add":  # 只允许add类modifier
                    print(f"{pm}的{s.WORKFORCE_SCALED}或{s.LEVEL_SCALED}的{modifier}不是add类，因此被忽略")
                    continue
                match modifier_info["category"]:
                    case "goods":
                        if modifier_info["key_word"] not in self.goods_info:
                            print(f"未找到{pm}中{modifier_info["key_word"]}的定义")
                            continue
                        pms_dict[pm]["add"][modifier_info["io_type"]][modifier_info["key_word"]] = modifier_info[
                            "value"]
                    case ("building", "employment"):
                        if modifier_info["key_word"] not in self.pop_types_info:
                            print(f"未找到{pm}中{modifier_info["key_word"]}的定义")
                            continue
                        pms_dict[pm]["employment"][modifier_info["key_word"]] = modifier_info["value"]
            if s.UNSCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                modifier_dict = tp.parse_modifier_dict(
                    tp.calibrate_modifier_dict(dict(pm_blocks_dict[pm][s.BUILDING_MODIFIERS][s.UNSCALED])))
                for modifier, modifier_info in modifier_dict.items():
                    match modifier_info["category"]:
                        case "goods":
                            if modifier_info["key_word"] not in self.goods_info:
                                print(f"未找到{pm}中{modifier_info["key_word"]}的定义")
                                continue
                            match modifier_info["am_type"]:
                                case "add":
                                    if modifier_info["key_word"] in pms_dict[pm]["add"][modifier_info["io_type"]]:
                                        pms_dict[pm]["add"][modifier_info["io_type"]][modifier_info["key_word"]] \
                                            += modifier_info["value"]
                                    else:
                                        pms_dict[pm]["add"][modifier_info["io_type"]][modifier_info["key_word"]] \
                                            = modifier_info["value"]
                                case "mult":
                                    pms_dict[pm]["mult"][modifier_info["io_type"]][modifier_info["key_word"]] \
                                        = modifier_info["value"]
                        case ("building", "subsistence_output"):
                            if modifier_info["am_type"] == "add":
                                pms_dict[pm]["subsistence_output"] = modifier_info["value"]
                            else:
                                print(f"{pm}的{s.UNSCALED}的{modifier}不应该为{modifier_info["am_type"]}")
                        case _:
                            print(f"{pm}的{s.UNSCALED}的{modifier}无法被解析")
        return pms_dict

    @staticmethod
    def __get_localization_info(game_object_dict) -> dict:
        localization_dict_all = tp.get_localization_dict()

        game_object_list_dict = {game_object: list(game_object_dict[game_object].keys()) for game_object in
                                 game_object_dict}

        localization_keys_used = [
            key for game_object in game_object_list_dict
            if game_object not in ["script_values", "power_bloc_principles"]
            for key in game_object_list_dict[game_object]
            ]

        principle_keys = game_object_list_dict["power_bloc_principles"]  # 原则特殊，需要单独处理

        localization_dict_used = {}
        for principle_key in principle_keys:
            principle_match = re.search(r"principle_(?P<name>[\w\-]+?)_(?P<value>\d+)", principle_key)
            if principle_match is None:
                localization_dict_used[principle_keys] = principle_key
                continue
            principle_group_key = "principle_group_" + principle_match.group("name")
            if principle_group_key in localization_dict_all:
                localization_dict_used[principle_key] = localization_dict_all[
                                                            principle_group_key] + principle_match.group("value")
            else:
                print(f"找不到{principle_group_key}的本地化")
                localization_dict_used[principle_key] = principle_key

        for key in localization_keys_used:
            if key in localization_dict_all:  # 一些键没有对应的值
                localization_dict_used[key] = localization_dict_all[key]
            else:
                print(f"找不到{key}的本地化")
                localization_dict_used[key] = key

        tp.calibrate_localization_dict(localization_dict_used, localization_dict_all)

        # dummy building的本地化值过长，需要被替换，这里用本地化值的长度作为依据
        for building in game_object_list_dict["buildings"]:
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
            buildings_list.append(mm.BuildingNode(
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
                pmgs_list.append(mm.NormalNode(
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
                pms_list.append(mm.PMNode(
                    localization_key=pm,
                    localization_value=self.localization_info[pm],
                    unlocking_technologies=self.parse_tech(self.pms_info[pm][s.UNLOCKING_TECHNOLOGIES]),
                    unlocking_production_methods=self.pms_info[pm][s.UNLOCKING_PRODUCTION_METHODS],
                    unlocking_principles=self.parse_name(self.pms_info[pm][s.UNLOCKING_PRINCIPLES],
                                                         self.principles_info),
                    unlocking_laws=self.parse_name(self.pms_info[pm][s.UNLOCKING_LAWS], self.laws_info),
                    disallowing_laws=self.parse_name(self.pms_info[pm][s.DISALLOWING_LAWS], self.laws_info),
                    unlocking_identity=self.parse_name(self.pms_info[pm][s.UNLOCKING_IDENTITY], self.identities_info),
                    goods_add=self.pms_info[pm]["add"],
                    goods_mult=self.pms_info[pm]["mult"],
                    workforce=self.pms_info[pm]['employment'],
                    subsistence_output=self.pms_info[pm]["subsistence_output"]
                ))
            else:
                print(f"{pm}无定义")
        return pms_list

    def parse_tech(self, techs) -> list:
        techs_list = []
        for tech in techs:
            if tech in self.technologies_info:
                techs_list.append(mm.TechNode(
                    localization_key=tech,
                    localization_value=self.localization_info[tech],
                    era=self.technologies_info[tech],
                ))
            else:
                print(f"{tech}无定义")
        return techs_list

    def parse_name(self, objects: list, info: dict) -> list:
        objects_list = []
        for _object in objects:
            if _object in info:
                objects_list.append(mm.Name(
                    localization_key=_object,
                    localization_value=self.localization_info[_object]
                ))
            else:
                print(f"{_object}无定义")
        return objects_list

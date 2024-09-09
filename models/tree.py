"""
树生成类
"""
import utils.textproc as tp
import utils.path_to_dict as ptd
import utils.error as error
from utils.config import GOODS_COST_OFFSET
import constants.str as s
import models.model as mm

NULL_BUILDING_GROUP = mm.BuildingGroupNode(  # 用于处理缺失建筑组的建筑
    localization_key='Null',
    localization_value='Null',
    parent_group=[]
)


class BuildingInfoTree:
    def __init__(self):
        game_objet_need = ['buildings', 'building_groups', 'goods', 'laws', 'pop_types', 'power_bloc_identities',
                           'power_bloc_principles',
                           'production_method_groups', 'production_methods', 'script_values', 'technologies']
        game_object_dict = ptd.get_game_object_dict(game_objet_need)

        self.localization_info = self.__get_localization_info(game_object_dict)

        self.scrit_values_info = game_object_dict['script_values']
        self.building_groups_info = self.__get_building_groups_info(game_object_dict['building_groups'])
        self.buildings_info = self.__get_buildings_info(game_object_dict['buildings'])
        self.goods_info = self.__get_goods_info(game_object_dict['goods'])
        self.laws_info = game_object_dict['laws']
        self.pop_types_info = self.__get_pops_info(game_object_dict['pop_types'])
        self.identities_info = game_object_dict['power_bloc_identities']
        self.principles_info = game_object_dict['power_bloc_principles']
        self.pmgs_info = self.__get_pmgs_info(game_object_dict['production_method_groups'])
        self.pms_info = self.__get_pms_info(game_object_dict['production_methods'])
        self.technologies_info = self.__get_technologies_info(game_object_dict['technologies'])

        self.automation_pm_list = self.__get_automation_pm_list()

        self.tree = self.generate_tree()

    def __get_building_groups_info(self, building_groups_blocks_dict) -> dict:
        def get_parent_groups_list(_building_group: str, _building_groups_blocks_dict: dict) -> list:
            _parent_group = _building_groups_blocks_dict[_building_group]
            parent_groups_list = [_building_group]
            while _parent_group:
                parent_groups_list.append(_parent_group)
                _parent_group = _building_groups_blocks_dict[_parent_group]
            return parent_groups_list

        building_groups_dict = {
            building_group: error.get_attribute(building_group, building_groups_blocks_dict, s.PARENT_GROUP, '',
                                                False)
            for building_group in building_groups_blocks_dict
        }

        extend_building_groups_dict = building_groups_dict.copy()
        for parent_group in building_groups_dict.values():  # 把不存在的父建筑组加上
            if parent_group not in extend_building_groups_dict and parent_group:
                error.lack_definition(parent_group)
                extend_building_groups_dict[parent_group] = ''

        return {
            building_group: mm.BuildingGroupNode(
                localization_key=building_group,
                localization_value=self.localization_info.get(building_group, building_group),
                parent_group=get_parent_groups_list(building_group, extend_building_groups_dict)
            )
            for building_group in extend_building_groups_dict
        }

    @staticmethod
    def __get_technologies_info(technology_blocks_dict) -> dict:
        return {
            technology: error.get_era_num(error.get_attribute(technology, technology_blocks_dict, s.ERA, 0),
                                          technology)
            for technology in technology_blocks_dict
        }

    # ! 预备部分，创建各项存储字典
    def __get_goods_info(self, good_blocks_dict) -> dict:
        return {
            good: mm.GoodNode(
                localization_key=good,
                localization_value=self.localization_info[good],
                cost=error.get_attribute(good, good_blocks_dict, s.COST, 0) * GOODS_COST_OFFSET.get(good, 1.0)
            )
            for good in good_blocks_dict
        }

    def __get_pops_info(self, pop_blocks_dict) -> dict:
        return {
            pop_type: mm.POPTypeNode(
                localization_key=pop_type,
                localization_value=self.localization_info[pop_type],
                wage_weight=error.get_attribute(pop_type, pop_blocks_dict, s.WAGE_WEIGHT, 0),
                subsistence_income=error.has_attribute(pop_type, pop_blocks_dict, s.SUBSISTENCE_INCOME, False)
            )
            for pop_type in pop_blocks_dict
        }

    def __get_buildings_info(self, building_blocks_dict) -> dict:
        return {
            building: {
                'cost': error.find_numeric_value(building_blocks_dict[building].get(s.REQUIRED_CONSTRUCTION, 0),
                                                 self.scrit_values_info),
                'pmgs': error.get_attribute(building, building_blocks_dict, s.PRODUCTION_METHOD_GROUPS, []),
                'bg': error.get_attribute(building, building_blocks_dict, s.BUILDING_GROUP, ''),
                'unlocking_technologies': building_blocks_dict[building].get(s.UNLOCKING_TECHNOLOGIES, [])
            }
            for building in building_blocks_dict
        }

    @staticmethod
    def __get_pmgs_info(pmg_blocks_dict) -> dict:
        return {
            pmg: error.get_attribute(pmg, pmg_blocks_dict, s.PRODUCTION_METHODS, [], True)
            for pmg in pmg_blocks_dict
        }

    def __get_pms_info(self, pm_blocks_dict) -> dict:
        def update_pms_dict(_pm: str, attribute: str):
            modifier_dict = tp.parse_modifier_dict(
                tp.calibrate_modifier_dict(pm_blocks_dict[_pm][s.BUILDING_MODIFIERS][attribute]))
            for modifier, modifier_info in modifier_dict.items():
                category = modifier_info['category']
                keyword = modifier_info.get('keyword', '')
                am_type = modifier_info['am_type']
                io_type = modifier_info.get('io_type', '')
                value = modifier_info['value']

                match category:
                    case 'goods':
                        if keyword not in self.goods_info:
                            error.lack_definition(_pm, keyword)
                            continue
                        match am_type:
                            case 'add':
                                pms_dict[_pm][am_type][io_type][keyword] \
                                    = pms_dict[_pm][am_type][io_type].get(keyword, 0) + value
                            case 'mult':
                                if attribute != s.UNSCALED:
                                    error.wrong_type(_pm, attribute, modifier, object_type='add')
                                    continue
                                pms_dict[pm][am_type][io_type][keyword] = value
                    case ('building', 'employment'):
                        if keyword not in self.pop_types_info:
                            error.lack_definition(_pm, keyword)
                            continue
                        match am_type:
                            case 'add':
                                if attribute == s.UNSCALED:
                                    error.can_not_parse(_pm, attribute, modifier)
                                    continue
                                pms_dict[_pm]['employment'][keyword] = (pms_dict[_pm]['employment'].get(keyword, 0)
                                                                        + value)
                            case 'mult':
                                error.wrong_type(_pm, attribute, modifier, object_type='add')
                    case ('building', 'subsistence_output'):
                        if attribute != s.UNSCALED:
                            error.can_not_parse(_pm, attribute, modifier)
                            continue
                        match am_type:
                            case 'add':
                                pms_dict[pm]['subsistence_output'] = value
                            case 'mult':
                                error.wrong_type(_pm, attribute, modifier, object_type='add')
                    case _:
                        error.can_not_parse(_pm, attribute, modifier)

        pms_dict = {}
        for pm in pm_blocks_dict:

            pms_dict[pm] = {
                'add': {'input': {}, 'output': {}},
                'mult': {'input': {}, 'output': {}},
                'employment': {},
                'subsistence_output': 0,
                s.UNLOCKING_TECHNOLOGIES: pm_blocks_dict[pm].get(s.UNLOCKING_TECHNOLOGIES, []),
                s.UNLOCKING_PRODUCTION_METHODS: pm_blocks_dict[pm].get(s.UNLOCKING_PRODUCTION_METHODS, []),
                s.UNLOCKING_PRINCIPLES: pm_blocks_dict[pm].get(s.UNLOCKING_PRINCIPLES, []),
                s.UNLOCKING_LAWS: pm_blocks_dict[pm].get(s.UNLOCKING_LAWS, []),
                s.DISALLOWING_LAWS: pm_blocks_dict[pm].get(s.DISALLOWING_LAWS, []),
                s.UNLOCKING_IDENTITY: pm_blocks_dict[pm].get(s.UNLOCKING_IDENTITY, '')
            }

            if s.BUILDING_MODIFIERS not in pm_blocks_dict[pm]:
                continue

            if s.WORKFORCE_SCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                update_pms_dict(pm, s.WORKFORCE_SCALED)
            if s.LEVEL_SCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                update_pms_dict(pm, s.LEVEL_SCALED)
            if s.UNSCALED in pm_blocks_dict[pm][s.BUILDING_MODIFIERS]:
                update_pms_dict(pm, s.UNSCALED)

        return pms_dict

    @staticmethod
    def __get_localization_info(game_object_dict) -> dict:
        localization_dict_all = tp.get_localization_dict()
        localization_dict_used = {}

        game_object_list_dict = {game_object: list(game_object_dict[game_object].keys()) for game_object in
                                 game_object_dict}

        localization_keys_used = [
            key for game_object in game_object_list_dict
            if game_object not in ['script_values', 'power_bloc_principles']
            for key in game_object_list_dict[game_object]
        ]

        error.process_principle(game_object_list_dict['power_bloc_principles'],
                                localization_dict_used, localization_dict_all)  # 单独处理原则

        for key in localization_keys_used:
            localization_dict_used[key] = error.get_localization(key, localization_dict_all)

        tp.calibrate_localization_dict(localization_dict_used, localization_dict_all)  # 替换字典中的$<字符>$

        error.process_long_building_name(game_object_list_dict['buildings'], localization_dict_used)  # 处理过长的建筑名称

        return localization_dict_used

    def __get_automation_pm_list(self):
        return [pm for pmg, pm_list in self.pmgs_info.items() if self.localization_info[pmg] == '自动化' for pm in
                pm_list]

    # ------------------------------------------------------------------------------------------
    # ! 按建筑-生产方式群-生产方式创建信息树
    def generate_tree(self) -> list:
        tree_list = self.parse_buildings()
        return tree_list

    def parse_buildings(self) -> list:
        buildings_list = []
        for building, building_info in self.buildings_info.items():
            building_group, building_group_display = self.parse_building_group(self.buildings_info[building]['bg'])
            buildings_list.append(mm.BuildingNode(
                localization_key=building,
                localization_value=self.localization_info[building],
                children=self.parse_pmgs(building_info['pmgs']),
                required_construction=building_info['cost'],
                building_group=building_group,
                building_group_display=building_group_display,
                unlocking_technologies=self.parse_tech(self.buildings_info[building][s.UNLOCKING_TECHNOLOGIES])
            ))

        return buildings_list

    def parse_building_group(self, building_group: str) -> tuple:
        if building_group in self.building_groups_info:
            building_group_info = self.building_groups_info[building_group]
            if len(building_group_info.parent_group) > 1 and building_group_info.parent_group[-1] == 'bg_manufacturing':
                return building_group_info, self.building_groups_info[building_group_info.parent_group[-2]]
            else:
                return building_group_info, self.building_groups_info[building_group_info.parent_group[-1]]
        else:
            error.lack_definition(building_group)
            return NULL_BUILDING_GROUP, NULL_BUILDING_GROUP

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
                error.lack_definition(pmg)

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
                    unlocking_principles=self.parse_names_list(self.pms_info[pm][s.UNLOCKING_PRINCIPLES],
                                                               self.principles_info),
                    unlocking_laws=self.parse_names_list(self.pms_info[pm][s.UNLOCKING_LAWS], self.laws_info),
                    disallowing_laws=self.parse_names_list(self.pms_info[pm][s.DISALLOWING_LAWS], self.laws_info),
                    unlocking_identity=self.parse_name(self.pms_info[pm][s.UNLOCKING_IDENTITY], self.identities_info),
                    goods_add=self.pms_info[pm]['add'],
                    goods_mult=self.pms_info[pm]['mult'],
                    workforce=self.pms_info[pm]['employment'],
                    subsistence_output=self.pms_info[pm]['subsistence_output']
                ))
            else:
                error.lack_definition(pm)
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
                error.lack_definition(tech)
        return techs_list

    def parse_names_list(self, objects: list, info: dict) -> list:
        objects_list = []
        for _object in objects:
            if _object in info:
                objects_list.append(mm.Name(
                    localization_key=_object,
                    localization_value=self.localization_info[_object]
                ))
            else:
                error.lack_definition(_object)
        return objects_list

    def parse_name(self, game_object: str, info: dict):
        if not game_object:
            return None
        if game_object in info:
            return mm.Name(
                localization_key=game_object,
                localization_value=self.localization_info[game_object]
            )
        else:
            error.lack_definition(game_object)
            return None

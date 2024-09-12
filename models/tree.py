"""
树生成类
"""
import utils.textproc as tp
import utils.game_data_mapper as gdm
import utils.error as error
from utils.config import GOODS_COST_OFFSET
import constants.str as s
import models.model as mm
import utils.obj as obj

NULL_BUILDING_GROUP = mm.BuildingGroup(  # 用于处理缺失建筑组的建筑
    loc_key='Null',
    loc_value='Null',
    parent_group='',
    path='',
    obj_type=''
)


class GameObjectBuilder:
    def __init__(self):
        local_obj_types = ['buildings', 'building_groups', 'goods', 'laws', 'pop_types', 'power_bloc_identities',
                           'power_bloc_principles', 'production_method_groups', 'production_methods', 'script_values',
                           'technologies']
        obj_types_dict = gdm.get_obj_types_dict(local_obj_types)
        for obj_types in obj_types_dict:
            if obj_types != 'script_values':
                obj_types_dict[obj_types] = error.check_objects_dict(obj_types_dict[obj_types], obj_types)

        self.loc = obj.get_loc(obj_types_dict)

        self.scrit_values = obj.get_scrit_values(obj_types_dict['script_values'])
        self.building_groups = obj.get_building_groups(obj_types_dict['building_groups'], self.loc)
        self.buildings = obj.get_buildings(obj_types_dict['buildings'], self.loc)
        self.goods = obj.get_goods(obj_types_dict['goods'], self.loc)
        self.laws = obj.get_obj(obj_types_dict['laws'], self.loc)
        self.pop_types = obj.get_pops(obj_types_dict['pop_types'], self.loc)
        self.identities = obj.get_obj(obj_types_dict['power_bloc_identities'], self.loc)
        self.principles = obj.get_obj(obj_types_dict['power_bloc_principles'], self.loc)
        self.pmgs = obj.get_pmgs(obj_types_dict['production_method_groups'], self.loc)
        self.pms = obj.get_pms(obj_types_dict['production_methods'], self.loc)
        self.technologies = obj.get_technologies(obj_types_dict['technologies'], self.loc)

    def get_building_groups_chain(self, bg: str):
        bg_chain = [bg]
        if bg not in self.building_groups:
            return error.lack_definition('building_groups', bg, value=bg_chain)
        while self.building_groups[bg].parent_group:
            bg = self.building_groups[bg].parent_group
            if bg in bg_chain:
                error.check_parent_group(self.building_groups[bg])
                return bg_chain
            bg_chain.append(bg)
        return bg_chain


class BuildingInfoTree:
    def __init__(self):
        gob = GameObjectBuilder()
        self.scrit_values_info = gob.scrit_values
        self.building_groups_info = gob.building_groups
        self.buildings_info = gob.buildings
        self.goods_info = gob.goods
        self.laws_info = gob.laws
        self.pop_types_info = gob.pop_types
        self.identities_info = gob.identities
        self.principles_info = gob.principles
        self.pmgs_info = gob.pmgs
        self.pms_info = gob.pms
        self.technologies_info = gob.technologies

        self.automation_pm_list = self.__get_automation_pm_list()

        self.tree = self.generate_tree()

    def __get_building_groups_chain(self, bg: str):
        bg_chain = [bg]
        if bg not in self.building_groups_info:
            return error.lack_definition('building_groups', bg, value=bg_chain)
        while self.building_groups_info[bg].parent_group:
            bg = self.building_groups_info[bg].parent_group
            if bg in bg_chain:
                error.check_parent_group(self.building_groups_info[bg])
                return bg_chain
            bg_chain.append(bg)
        return bg_chain

    def __get_pms_info(self, pm_blocks_dict) -> dict:
        def update_pms_dict(_pm: str, attribute: str):
            modifier_dict = tp.parse_modifier_dict(
                _pm, attribute,
                modifier_dict=tp.calibrate_modifier_dict(pm_blocks_dict[_pm][s.BUILDING_MODIFIERS][attribute])
            )
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
                loc_key=building,
                loc_value=self.localization_info[building],
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
                    loc_key=pmg,
                    loc_value=self.localization_info[pmg],
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
                    loc_key=pm,
                    loc_value=self.localization_info[pm],
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
                    loc_key=tech,
                    loc_value=self.localization_info[tech],
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
                    loc_key=_object,
                    loc_value=self.localization_info[_object]
                ))
            else:
                error.lack_definition(_object)
        return objects_list

    def parse_name(self, game_object: str, info: dict):
        if not game_object:
            return None
        if game_object in info:
            return mm.Name(
                loc_key=game_object,
                loc_value=self.localization_info[game_object]
            )
        else:
            error.lack_definition(game_object)
            return None

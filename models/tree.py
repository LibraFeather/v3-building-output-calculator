"""
树生成类
"""
from utils.textproc import parse_modifiers_dict
from utils.game_data_mapper import get_obj_types_dict
from utils.config import GOODS_COST_OFFSET

import utils.error as error
import utils.obj as obj
import constants.str as s
import models.model as mm


class GameObjectBuilder:
    def __init__(self):
        local_obj_types = ['buildings', 'building_groups', 'goods', 'laws', 'pop_types', 'power_bloc_identities',
                           'power_bloc_principles', 'production_method_groups', 'production_methods', 'script_values',
                           'technologies']
        obj_types_dict = get_obj_types_dict(local_obj_types)
        for obj_types in obj_types_dict:
            if obj_types != 'script_values':
                obj_types_dict[obj_types] = error.check_objects_dict(obj_types_dict[obj_types], obj_types)

        self.loc = obj.get_loc(obj_types_dict)

        self.scrit_values = obj.get_scrit_values(obj_types_dict['script_values'])
        self.building_groups = obj.get_building_groups(obj_types_dict['building_groups'], self.loc)
        self.buildings = obj.get_buildings(obj_types_dict['buildings'], self.loc)
        self.goods = obj.get_goods(obj_types_dict['goods'], self.loc)
        self.laws = obj.get_objs(obj_types_dict['laws'], self.loc)
        self.pop_types = obj.get_pop_types(obj_types_dict['pop_types'], self.loc)
        self.identities = obj.get_objs(obj_types_dict['power_bloc_identities'], self.loc)
        self.principles = obj.get_objs(obj_types_dict['power_bloc_principles'], self.loc)
        self.pmgs = obj.get_pmgs(obj_types_dict['production_method_groups'], self.loc)
        self.pms = obj.get_pms(obj_types_dict['production_methods'], self.loc)
        self.technologies = obj.get_technologies(obj_types_dict['technologies'], self.loc)


class BuildingInfoTree:
    def __init__(self):
        self.obj = GameObjectBuilder()

        self.goods_info = self.__get_goods_info()
        self.techs_info = self.__get_techs_info()

        self.bgs_info = self.__get_bgs_info()
        self.pms_info = self.__get_pms_info()
        self.pmgs_info = self.__get_pmgs_info()
        self.buildings_info = self.__get_buildings_info()

        self.automation_pm_list = self.__get_automation_pm_list()

    def __get_goods_info(self):
        return {
            good.loc_key: mm.GoodInfo(
                loc_key=good.loc_key,
                loc_value=good.loc_value,
                cost=good.cost * GOODS_COST_OFFSET.get(good.loc_key, 1)
            )
            for good in self.obj.goods.values()
        }

    def __get_techs_info(self):
        return {
            tech.loc_key: mm.TechInfo(
                loc_key=tech.loc_key,
                loc_value=tech.loc_value,
                era=error.get_era_num(tech.era, tech)
            )
            for tech in self.obj.technologies.values()
        }

    def __get_bgs_info(self):
        bgs_info = self.obj.building_groups.copy()
        for bg in self.obj.building_groups.values():
            if bg.parent_group and bg.parent_group not in bgs_info:
                error.lack_definition('building_groups', bg.parent_group)
                bgs_info[bg.parent_group] = mm.BuildingGroup(
                    path='',
                    obj_type='building_groups',
                    loc_key='bg.parent',
                    loc_value='bg.parent',
                    parent_group=''
                )
        return bgs_info

    def __get_buildings_info(self):
        buildings_info = {}
        for building in self.obj.buildings.values():
            bg = error.check_existence(building, building.bg, self.obj.building_groups)
            display_bg = self.__gat_display_bg(bg)
            buildings_info[building.loc_key] = mm.BuildingInfo(
                loc_key=building.loc_key,
                loc_value=building.loc_value,
                bg=bg,
                display_bg=display_bg,
                pmgs=[self.pmgs_info[pmg]
                      for pmg in error.check_existence(building, building.pmgs, self.obj.pmgs)
                      ],
                unlocking_techs=[self.techs_info[tech]
                                 for tech in
                                 error.check_existence(building, building.unlocking_techs, self.obj.technologies)
                                 ],
                required_construction=error.find_numeric_value(building, s.REQUIRED_CONSTRUCTION, self.obj.scrit_values)
            )
        return buildings_info

    def __get_building_groups_chain(self, bg: str):
        bg_chain = [bg]
        while self.bgs_info[bg].parent_group:
            bg = self.bgs_info[bg].parent_group
            if bg in bg_chain:
                return error.check_bg_loop(self.bgs_info[bg])
            bg_chain.append(bg)
        return bg_chain

    def __gat_display_bg(self, bg: str) -> mm.BuildingGroup:
        if not bg:
            return mm.BuildingGroup(
                path='',
                obj_type='building_groups',
                loc_key='Null',
                loc_value='Null',
                parent_group=''
            )
        bg_chain = self.__get_building_groups_chain(bg)
        if len(bg_chain) > 1 and bg_chain[-1] == 'bg_manufacturing':
            return self.bgs_info[bg_chain[-2]]
        else:
            return self.bgs_info[bg_chain[-1]]

    def __get_pmgs_info(self) -> dict:
        return {
            pmg.loc_key: mm.PMG(
                path=pmg.path,
                obj_type=pmg.obj_type,
                loc_key=pmg.loc_key,
                loc_value=pmg.loc_value,
                pms=[self.pms_info[pm]
                     for pm in error.check_existence(pmg, pmg.pms, self.obj.pms)
                     ]
            )
            for pmg in self.obj.pmgs.values()
        }

    def __get_pms_info(self) -> dict:
        def update_pm_modifiers_dict(attribute: str):
            modifiers_dict = getattr(pm.building_modifiers, attribute).value
            names = (pm.obj_type, pm.loc_key, 'building_modifiers', attribute)
            modifiers_dict = parse_modifiers_dict(
                *names, modifiers_dict=modifiers_dict
            )
            for modifier, modifier_info in modifiers_dict.items():
                category = modifier_info['category']
                keyword = modifier_info.get('keyword', '')
                am_type = modifier_info['am_type']
                io_type = modifier_info.get('io_type', '')
                value = modifier_info['value']

                match category:
                    case 'goods':
                        if keyword not in self.goods_info:
                            error.lack_definition(*names, modifier, keyword)
                            continue
                        match am_type:
                            case 'add':
                                pm_modifiers_dict[am_type][io_type][keyword] \
                                    = pm_modifiers_dict[am_type][io_type].get(keyword, 0) + value
                            case 'mult':
                                if attribute != s.UNSCALED:
                                    error.wrong_type(*names, modifier, obj_type='add')
                                    continue
                                pm_modifiers_dict[am_type][io_type][keyword] = value
                    case ('building', 'employment'):
                        if keyword not in self.obj.pop_types:
                            error.lack_definition(*names, modifier, keyword)
                            continue
                        match am_type:
                            case 'add':
                                if attribute == s.UNSCALED:
                                    error.can_not_parse(*names, modifier)
                                    continue
                                pm_modifiers_dict['employment'][keyword] = (
                                        pm_modifiers_dict['employment'].get(keyword, 0) + value)
                            case 'mult':
                                error.wrong_type(*names, modifier, obj_type='add')
                    case ('building', 'subsistence_output'):
                        if attribute != s.UNSCALED:
                            error.can_not_parse(*names, modifier)
                            continue
                        match am_type:
                            case 'add':
                                pm_modifiers_dict['subsistence_output'] = value
                            case 'mult':
                                error.wrong_type(*names, modifier, obj_type='add')
                    case _:
                        error.can_not_parse(*names, modifier)

        pms_info_dict = {}

        for pm in self.obj.pms.values():
            pm_modifiers_dict = {
                'add': {'input': {}, 'output': {}},
                'mult': {'input': {}, 'output': {}},
                'employment': {},
                'subsistence_output': 0
            }

            update_pm_modifiers_dict(s.WORKFORCE_SCALED)
            update_pm_modifiers_dict(s.LEVEL_SCALED)
            update_pm_modifiers_dict(s.UNSCALED)

            pms_info_dict[pm.loc_key] = mm.PMInfo(
                loc_key=pm.loc_key,
                loc_value=pm.loc_value,
                goods_add=pm_modifiers_dict['add'],
                goods_mult=pm_modifiers_dict['mult'],
                workforce=pm_modifiers_dict['employment'],
                subsistence_output=pm_modifiers_dict['subsistence_output'],
                unlocking_technologies=[self.techs_info[tech]
                                        for tech in error.check_existence(pm, pm.unlocking_technologies,
                                                                          self.obj.technologies)],
                unlocking_production_methods=error.check_existence(pm, pm.unlocking_production_methods,
                                                                   self.obj.pms),
                unlocking_principles=[self.obj.principles[principle]
                                      for principle in error.check_existence(pm, pm.unlocking_principles,
                                                                             self.obj.principles)],
                unlocking_laws=[self.obj.laws[law]
                                for law in error.check_existence(pm, pm.unlocking_laws,
                                                                 self.obj.laws)],
                disallowing_laws=[self.obj.laws[law]
                                  for law in error.check_existence(pm, pm.disallowing_laws,
                                                                   self.obj.laws)],
                unlocking_identity=self.obj.identities.get(error.check_existence(pm, pm.unlocking_identity,
                                                                                 self.obj.identities), '')
            )
        return pms_info_dict

    def __get_automation_pm_list(self):
        return [pm for pmg in self.obj.pmgs.values() if pmg.loc_value == '自动化' for pm in
                pmg.pms]

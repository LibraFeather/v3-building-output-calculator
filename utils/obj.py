"""
游戏对象生成函数
"""
import utils.textproc as tp
import utils.error as error
import models.model as mm
import constants.str as s


def get_loc(objs_dict: dict) -> dict:
    global_loc_dict = tp.get_localization_dict()
    local_loc_dict = {}

    keys_by_type = {obj_type: list(objs_dict[obj_type].keys()) for obj_type in
                    objs_dict}

    keys = [
        key for obj_type in keys_by_type
        if obj_type not in ['script_values', 'power_bloc_principles']
        for key in keys_by_type[obj_type]
    ]

    error.localize_principle(local_loc_dict, keys_by_type['power_bloc_principles'], global_loc_dict)  # 单独处理原则

    for key in keys:
        local_loc_dict[key] = error.get_localization(key, global_loc_dict)

    tp.calibrate_loc_dict(local_loc_dict, global_loc_dict)  # 替换字典中的$<字符>$

    error.check_long_building_name(local_loc_dict, keys_by_type['buildings'])  # 处理过长的建筑名称

    return local_loc_dict


def get_scrit_values(scrit_values_blocks_dict: dict) -> dict:
    return {
        scrit_value: mm.ScritValues(
            loc_key=scrit_value,
            loc_value=scrit_value,
            value=scrit_values_blocks_dict[scrit_value].block,
            path=scrit_values_blocks_dict[scrit_value].path,
            obj_type=scrit_values_blocks_dict[scrit_value].obj_type
        )
        for scrit_value in scrit_values_blocks_dict
    }


def get_building_groups(bg_blocks_dict: dict, loc_dict: dict) -> dict:
    bgs_dict = {
        bg: mm.BuildingGroup(
            loc_key=bg,
            loc_value=loc_dict[bg],
            path=bg_blocks_dict[bg].path,
            obj_type=bg_blocks_dict[bg].obj_type,
            parent_group=error.get_attribute(bg_blocks_dict[bg], s.PARENT_GROUP, '', str, False)
        )
        for bg in bg_blocks_dict
    }

    no_def_bgs_info_dict = {}
    for bg in bgs_dict.values():  # 把不存在的父建筑组加上
        bg_key = bg.parent_group
        if bg_key not in bg_blocks_dict and bg_key:
            no_def_bgs_info_dict[bg_key] = mm.BuildingGroup(
                loc_key=bg_key,
                loc_value=bg_key,
                path='',
                obj_type='building_groups',
                parent_group=''
            )

    return bgs_dict


def get_technologies(technology_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        tech: mm.Technology(
            loc_key=tech,
            loc_value=loc_dict[tech],
            path=technology_blocks_dict[tech].path,
            obj_type=technology_blocks_dict[tech].obj_type,
            era=error.get_attribute(technology_blocks_dict[tech], s.ERA, 0, str)
        )
        for tech in technology_blocks_dict
    }


def get_goods(good_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        good: mm.Good(
            loc_key=good,
            loc_value=loc_dict[good],
            path=good_blocks_dict[good].path,
            obj_type=good_blocks_dict[good].obj_type,
            cost=error.get_attribute(good_blocks_dict[good], s.COST, 0, (int, float))
        )
        for good in good_blocks_dict
    }


def get_pops(pop_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        pop_type: mm.POPType(
            loc_key=pop_type,
            loc_value=loc_dict[pop_type],
            path=pop_blocks_dict[pop_type].path,
            obj_type=pop_blocks_dict[pop_type].obj_type,
            wage_weight=error.get_attribute(pop_blocks_dict[pop_type], s.WAGE_WEIGHT, 0, (int, float)),
            subsistence_income=error.has_attribute(pop_blocks_dict[pop_type], s.SUBSISTENCE_INCOME, False)
        )
        for pop_type in pop_blocks_dict
    }


def get_buildings(building_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        building: mm.Building(
            loc_key=building,
            loc_value=loc_dict[building],
            path=building_blocks_dict[building].path,
            obj_type=building_blocks_dict[building].obj_type,
            required_construction=error.get_attribute(building_blocks_dict[building], s.REQUIRED_CONSTRUCTION, 0,
                                                      (int, float, str), False),
            pmgs=error.get_attribute(building_blocks_dict[building], s.PRODUCTION_METHOD_GROUPS, [], list),
            bg=error.get_attribute(building_blocks_dict[building], s.BUILDING_GROUP, '', str),
            unlocking_technologies=error.get_attribute(building_blocks_dict[building], s.UNLOCKING_TECHNOLOGIES, [],
                                                       list)
        )
        for building in building_blocks_dict
    }


def get_pmgs(pmg_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        pmg: mm.PMG(
            loc_key=pmg,
            loc_value=loc_dict[pmg],
            path=pmg_blocks_dict[pmg].path,
            obj_type=pmg_blocks_dict[pmg].obj_type,
            pms=error.get_attribute(pmg_blocks_dict[pmg], s.PRODUCTION_METHODS, [], list, True)
        )
        for pmg in pmg_blocks_dict
    }


def get_pms(pm_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        pm: mm.PM(
            loc_key=pm,
            loc_value=loc_dict[pm],
            path=pm_blocks_dict[pm].path,
            obj_type=pm_blocks_dict[pm].obj_type,
            unlocking_technologies=error.get_attribute(pm_blocks_dict[pm], s.UNLOCKING_TECHNOLOGIES, [], list, False),
            unlocking_production_methods=error.get_attribute(pm_blocks_dict[pm], s.UNLOCKING_PRODUCTION_METHODS, [],
                                                             list, False),
            unlocking_principles=error.get_attribute(pm_blocks_dict[pm], s.UNLOCKING_PRINCIPLES, [], list, False),
            unlocking_laws=error.get_attribute(pm_blocks_dict[pm], s.UNLOCKING_LAWS, [], list, False),
            disallowing_laws=error.get_attribute(pm_blocks_dict[pm], s.DISALLOWING_LAWS, [], list, False),
            unlocking_identity=error.get_attribute(pm_blocks_dict[pm], s.UNLOCKING_IDENTITY, '', str, False),
            building_modifiers=get_building_modifiers(pm_blocks_dict[pm]),
        )
        for pm in pm_blocks_dict
    }


def get_building_modifiers(pm_info: mm.RawGameObject) -> mm.BuildingModifier:
    building_modifier_info = create_sub_raw_game_object(
        'building_modifiers',
        error.get_attribute(pm_info, attribute=s.BUILDING_MODIFIERS, value={}, value_type=dict, show_error=False),
        pm_info
    )
    workforce_scaled = create_sub_raw_game_object(
        'workforce_scaled',
        error.get_attribute(building_modifier_info, attribute=s.WORKFORCE_SCALED, value={}, value_type=dict,
                            show_error=False),
        building_modifier_info
    )
    level_scaled = create_sub_raw_game_object(
        'level_scaled',
        error.get_attribute(building_modifier_info, attribute=s.LEVEL_SCALED, value={}, value_type=dict,
                            show_error=False),
        building_modifier_info
    )
    unscaled = create_sub_raw_game_object(
        'unscaled',
        error.get_attribute(building_modifier_info, attribute=s.UNSCALED, value={}, value_type=dict,
                            show_error=False),
        building_modifier_info
    )
    return mm.BuildingModifier(
        workforce_scaled=error.check_modifier_dict_value(workforce_scaled),
        level_scaled=error.check_modifier_dict_value(level_scaled),
        unscaled=error.check_modifier_dict_value(unscaled)
    )


def get_obj(obj_blocks_dict: dict, loc_dict: dict) -> dict:
    return {
        obj: mm.GameObject(
            loc_key=obj,
            loc_value=loc_dict[obj],
            path=obj_blocks_dict[obj].path,
            obj_type=obj_blocks_dict[obj].obj_type
        )
        for obj in obj_blocks_dict
    }


def create_sub_raw_game_object(loc_key: str, block, father_info: mm.RawGameObject) -> mm.RawGameObject:
    return mm.RawGameObject(
        loc_key=loc_key,
        block=block,
        path=father_info.path,
        obj_type=f"{father_info.obj_type}.{father_info.loc_key}"
    )

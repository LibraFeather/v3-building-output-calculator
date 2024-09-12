"""
数据储存类
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class RawGameObject:
    loc_key: str
    block: Any
    path: str
    obj_type: str


@dataclass
class GameObject:
    loc_key: str
    loc_value: str
    path: str
    obj_type: str


@dataclass
class BuildingModifier:
    workforce_scaled: dict
    level_scaled: dict
    unscaled: dict


@dataclass
class PM(GameObject):
    unlocking_technologies: list
    unlocking_production_methods: list
    unlocking_principles: list
    unlocking_laws: list
    disallowing_laws: list
    unlocking_identity: str
    building_modifiers: BuildingModifier


@dataclass
class Technology(GameObject):
    era: str | int


@dataclass
class ScritValues(GameObject):
    value: Any


@dataclass
class BuildingGroup(GameObject):
    parent_group: str


@dataclass
class Building(GameObject):
    required_construction: int | float | str
    pmgs: list
    bg: str
    unlocking_technologies: list


@dataclass
class PMG(GameObject):
    pms: list


@dataclass
class Name:
    loc_key: str
    loc_value: str


@dataclass
class POPType(GameObject):
    wage_weight: int | float
    subsistence_income: bool


@dataclass
class Good(GameObject):
    cost: int | float


# 生产方式应用此类节点
@dataclass
class PMNode(Name):
    goods_add: dict
    goods_mult: dict
    workforce: dict
    subsistence_output: int | float
    unlocking_technologies: list
    unlocking_production_methods: list
    unlocking_principles: list
    unlocking_laws: list
    disallowing_laws: list
    unlocking_identity: Name


@dataclass
class TechNode(Name):
    era: str


# 生产方式群应用此类节点
@dataclass
class NormalNode(Name):
    children: list


# 建筑应用此类节点
@dataclass
class BuildingNode(NormalNode):
    building_group: BuildingGroup
    building_group_display: BuildingGroup
    unlocking_technologies: list
    required_construction: int | float

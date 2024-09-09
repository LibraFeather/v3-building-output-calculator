"""
数据储存类
"""
from dataclasses import dataclass


@dataclass
class Name:
    localization_key: str
    localization_value: str


@dataclass
class BuildingGroupNode(Name):
    parent_group: list


@dataclass
class POPTypeNode(Name):
    wage_weight: int | float
    subsistence_income: bool


@dataclass
class GoodNode(Name):
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
    building_group: BuildingGroupNode
    building_group_display: BuildingGroupNode
    unlocking_technologies: list
    required_construction: int | float

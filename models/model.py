from dataclasses import dataclass


@dataclass
class Name:
    localization_key: str
    localization_value: str


# 生产方式群应用此类节点
@dataclass
class NormalNode(Name):
    children: list


# 建筑应用此类节点
@dataclass
class BuildingNode(NormalNode):
    building_cost: float


# 生产方式应用此类节点
@dataclass
class PMNode(Name):
    unlocking_technologies: list
    unlocking_production_methods: list
    unlocking_principles: list
    unlocking_laws: list
    goods_add: dict
    goods_mult: dict
    workforce: dict


@dataclass
class TechNode(Name):
    era: str

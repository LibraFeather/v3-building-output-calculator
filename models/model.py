"""
数据储存类
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseGameObject:
    path: str
    obj_type: str
    loc_key: str


@dataclass
class RawGameObject(BaseGameObject):
    block: Any


@dataclass
class GameObject(BaseGameObject):
    loc_value: str


@dataclass
class Attribute:
    name: str
    location: tuple


@dataclass
class ModifierBlock(Attribute):
    value: dict


@dataclass
class BuildingModifier(Attribute):
    workforce_scaled: ModifierBlock
    level_scaled: ModifierBlock
    unscaled: ModifierBlock


@dataclass
class Modifier(Attribute):
    value: int | float


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
class ScritValue(GameObject):
    value: Any


@dataclass
class BuildingGroup(GameObject):
    parent_group: str


@dataclass
class Building(GameObject):
    required_construction: int | float | str
    pmgs: list
    bg: str
    unlocking_techs: list


@dataclass
class PMG(GameObject):
    pms: list


@dataclass
class Good(GameObject):
    cost: int | float


@dataclass
class POPType(GameObject):
    wage_weight: int | float
    subsistence_income: bool


@dataclass
class Info:
    loc_key: str
    loc_value: str


@dataclass
class GoodInfo(Info):
    cost: int | float


@dataclass
class TechInfo(Info):
    era: int


@dataclass
class BuildingInfo(Info):
    bg: BuildingGroup
    display_bg: BuildingGroup
    pmgs: list
    unlocking_techs: list
    required_construction: int | float


@dataclass
class PMInfo(Info):
    goods_add: dict
    goods_mult: dict
    workforce: dict
    subsistence_output: int | float
    unlocking_technologies: list
    unlocking_production_methods: list
    unlocking_principles: list
    unlocking_laws: list
    disallowing_laws: list
    unlocking_identity: str


# 生产方式群应用此类节点
@dataclass
class NormalNode(Info):
    children: list

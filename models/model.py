from dataclasses import dataclass


# 生产方式群应用此类节点
@dataclass
class NormalNode:
    localization_key: str
    localization_value: str
    children: list


# 建筑应用此类节点
@dataclass
class BuildingNode(NormalNode):
    building_cost: float


# 生产方式应用此类节点
@dataclass
class PMNode(NormalNode):
    goods_add: dict
    goods_mult: dict
    workforce: dict

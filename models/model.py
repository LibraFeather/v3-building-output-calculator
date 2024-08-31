from dataclasses import dataclass


# 生产方式群应用此类节点
@dataclass
class NormalNode:
    name: str
    localization_key: str
    children: list


# 建筑应用此类节点
@dataclass
class BuildingNode(NormalNode):
    building_cost: float


# 生产方式应用此类节点
@dataclass
class PMNode(NormalNode):
    good_input: dict
    good_output: dict
    workforce: dict

from dataclasses import dataclass

# 建筑，生产方式群应用此类节点
#TODO 除了models.py以外都是废的，到时候再安排
@dataclass
class NormalNode:
    name: str
    localization_key: str
    children: list

@dataclass
class BuildingNode(NormalNode):
    building_cost: float

# 生产方式应用此类节点
@dataclass
class PMNode(NormalNode):
    good_input: dict
    good_output: dict
    workforce: dict

# 商品信息应用此数据类
@dataclass
class GoodsInfo:
    name: str
    price: float

# 人群类型应用此数据类
@dataclass
class PopTypesInfo:
    job: str
    wage_weight: float
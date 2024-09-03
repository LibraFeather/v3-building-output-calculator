# TODO

## 功能开发
### 已完成
- [x] scrip_values的自动识别
- [x] 建筑总表输出功能
- [x] 支持mult修正
- [x] 显示科技要求
- [x] 剔除不满足生产方式解锁条件的生产方式组合
### 高优先级
- [ ] 改进本地化文件的读取方式，以应对replace文件夹
- [ ] 利润考虑自给产出
- [ ] 确认`building_employment_<pop_type>_add`能否在`unscaled`中起效
### 中优先级
### 低优先级
- [ ] 更好的游戏对象重复功能识别，现版本无法区分mod内重复和mod和原版文件的重复(纠错功能是否应该分离？)
- [ ] utils.textproc.parse_building_modifier支持所有类型的building modifier

## 代码优化
- [x] utils.textproc.parse_text_block过于复杂，需要重构
- [ ] tree.BuildingInfoTree.__get_pms_info对modifier的处理过于复杂，需要重构

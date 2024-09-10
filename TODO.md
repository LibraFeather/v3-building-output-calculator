# TODO

## 功能开发
### 已完成
- [x] `scrip_values`的自动识别
- [x] 建筑总表输出功能
- [x] 支持mult修正
- [x] 显示科技要求
- [x] 剔除不满足生产方式解锁条件的生产方式组合
- [x] 显示原则、法律等要求
- [x] 新增了一个配置文件，以在非标准价格下进行计算
- [x] 利润考虑自给产出
- [x] `unscaled`中的`building_employment_<pop_type>_add`确实不受等级和劳动力修正
- [x] 显示具体商品的增减
- [x] 显示建筑所在的建筑组
- [x] 研究如何将程序转化为exe文件，以在无Python环境下运行
- [x] 建筑本身也有科技要求
### 高优先级
- [ ] 改进本地化文件的读取方式，以应对`replace`文件夹
- [ ] 改进建筑组显示方式
- [ ] 字典有效性检查
- [ ] 属性类型检查
### 中优先级
- [ ] 价格配置文件似乎不方便用户使用，需要改进
### 低优先级
- [ ] 法律要求的显示有点令人困惑，需要优化
- [ ] 更好的游戏对象重复功能识别，现版本无法区分mod内重复和mod和原版文件的重复(纠错功能是否应该分离？)
- [ ] `utils.textproc.parse_building_modifier`支持所有类型的`building modifier`
## 代码优化
- [x] `utils.textproc.parse_text_block`过于复杂，需要重构
- [x] `tree.BuildingInfoTree.__get_pms_info`对`modifier`的处理过于复杂，需要重构
- [x] `calculator.__generate_one_line_data`过于复杂，需要重构

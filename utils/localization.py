# 处理本地化的类
# TODO 待更新，暂时未使用

class Localization:
    """
    用于处理本地化
    """

    def __init__(self, path):
        """
        :param path: 本地化文件的路径
        """
        self.path = path
        self.dict_all = self._create_dict_all()

    def _create_dict_all(self) -> dict:
        """
        创建一个包含所有本地化键的字典
        """
        content = txt_combiner(self.path)
        dict_loc = extract_all_blocks(localization_pattern, content, "\"")
        for key, value in dict_loc.items():
            replace_list = loc_replace_pattern.findall(value)
            for replace in replace_list:
                if replace in dict_loc.keys():
                    value = value.replace(f"${replace}$", dict_loc[replace])
                    # print(f"{key}中的{replace}被替换为{dict_loc[replace]}")
            dict_loc[key] = value
        return dict_loc

    def create_dict_used(self, dict_list_loc: dict) -> dict:
        """
        这部字典仅包含使用的本地化键
        :param dict_list_loc: 使用的本地化键的列表的字典
        """
        dict_used = {}
        list_used = []
        for value in dict_list_loc.values():
            list_used.extend(value)
        for key in list_used:
            if key in self.dict_all:
                dict_used[key] = self.dict_all[key]
            else:
                print(f"找不到{key}的本地化")
                dict_used[key] = key
        return dict_used
import utils.textproc as tp
import utils.pathproc as pp
import utils.test as t

from constants.constant import LOCALIZATION_PATH
from constants.pattern import LOCALIZATION_PATTERN

content = tp.txt_combiner(LOCALIZATION_PATH)
t.output_to_test_txt(content)
localization_dict_all = tp.extract_all_blocks(LOCALIZATION_PATTERN, content, "\"")
t.output_to_test_json(localization_dict_all)

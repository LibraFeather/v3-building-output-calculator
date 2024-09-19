# 建筑产值简易计算工具v0.8.2

Calista C.Manstainne，Recognized User L，19/09/2024

本工具可实现如下功能：

- 通过读取游戏文件，自动计算建筑的产出信息，结果以excel文件形式输出，以方便使用者在excel中处理数据。

适配游戏版本：1.7.6，在更高或更低版本下运行可能发生意料之外的错误。

## 版本说明

此工具分为py版和exe版，后者通过pyinstaller生成，以在无Python的环境下使用。

## 使用前操作(仅限py版)

### 安装Python

本工具基于Python 3.12开发，因此需要安装Python解释器来运作。

[Python官网](https://www.python.org/)

### 安装Pandas库和openpyxl库

1. 安装好Python后，按`win+r`键打开运行后，输入`cmd`，回车，打开命令提示符窗口。
2. 在命令提示符窗口输入如下代码后回车，以安装pandas库：
    ```cmd
    pip install pandas
    ```
3. 在命令提示符窗口输入如下代码后回车，以安装openpyxl库：
    ```cmd
    pip install openpyxl
    ```
4. 建议安装时关闭科学上网，否则有可能报错。

## 使用方法

1. **配置游戏文件路径**：打开`config\path.json`文件，将`VANILLA_PATH`修改为`Victoria 3\game`的路径。  
   示例：
   ```json
   {
      "VANILLA_PATH": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game"
   }
   ```
2. **运行程序**：运行`main.py`(py版)或`main.exe`(exe版)。
3. **查看结果**：结果会被输出至`_output\buildings`文件夹。

## 配置文件说明

### `config.json`
`MOD_PATH`：模组文件夹路径，默认为`_input`。  
`VANILLA_PATH`：原版游戏路径，路径结尾应为`game`。  
`LOCALIZATION`：输出excel的语言。（为了防止相同本地化值造成的报错，位于excel文件首行的本地化值都会加上本地化键作为区分）  
`GOODS_COST_OFFSET`：商品价格相对于基础价格的偏离倍数，原版为0.25~1.75。

### `warning_settings.json`
`SHOW_DUPLICATE_KEY_WARNING`：是否显示重复游戏对象错误，默认为`True`，比如原版的`building_vineyard_plantation`被定义了两次，此时就会提示错误。（mod和原版出现重复时不会报错）  
`SHOW_LOCALIZATION_WARNING`：是否显示本地化文件格式错误，仅检测引号是否封闭，默认为`True`。  
`SHOW_LACK_LOCALIZATION_WARNING`：是否显示本地化值缺失错误，默认为`False`。

## 注意事项

本程序计算的利润基于建筑生产/消耗的商品和自给产出，默认基于基础价格，如果建筑存在其他效果，或者建筑受到其他修正影响，本工具不会考虑，因此计算结果和真实值可能存在偏差。

### mod相关

1. 本工具可以计算mod建筑的产值，但是可能因为代码格式导致程序出错。
2. 在运行过程中，如果遇到异常，本工具会尝试显示异常原因。
3. 计算mod建筑时，可以选择：
   1. 在`config\path.json`文件里将`MOD_PATH`修改为mod的路径，程序会自动读取`metadata.json`，以确定哪些文件夹需要覆盖原版文件。  
      示例：
      ```json
      {
         "MOD_PATH": "C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\529340\\2935989855"
      }
      ```
   2. 将mod文件复制进`_input`文件夹（不是整个mod文件夹，而是mod文件夹内的文件）。
4. mod建筑的本地化名称不能超过50个字符，否则会被替换为dummy，以避免因为文件路径过长而无法输出。
5. 在显示建筑组时，如果建筑组的根建筑组是`bg_manufacturing`，那么显示的建筑组将会是`bg_manufacturing`的下一级子建筑组（如果存在）。
其他建筑组均只会显示根建筑组。
6. 在生成总表时，如果所有建筑的生产方式都小于五个，那么本工具会试图把所有的自动化生产方式都归类到一列（需要生产方式组的中文本地化为“自动化”）。
如果四个生产方式都不满足条件，第三个生产方式组的生产方式会出现在“自动化”列下。
7. 程序只会识别`<pm>.building_modifiers`中的一部分`modifier`：
   1. `workforce_scaled`和`level_scaled`中的
      1. `goods_input/output_<good>_add`
      2. `building_employment_<pop_type>_add`
   2. `unscaled`中的
      1. `goods_input/output_<good>_add/mult`
8. 程序会将`technology`的`era`转化为`int`变量，解析方式是通过正则表达式捕获`era`变量中的第一段连续数字，这可能无法处理某些命名。
9. 由于原则组下的原则在原版中不存在对应的本地化文本，因此本工具会先通过正则表达式捕获`principle_(?P<name>[\w\-]+?)_(?P<value>\d+)`，然后寻找
`principle_group_<name>`的本地化文本，这可能无法处理某些命名。
10. 本程序可能无法正确处理本地化中的`replace`文件夹。

### 程序逻辑简述
1. 读取`config`文件内的配置文件。
2. 处理特定文件夹下的文件，将代码转化为嵌套字典，用`RawGameObject`类储存这些信息。这一步会粗略检测格式问题，比如括号相关的错误。
3. 处理本地化内容，这里会读取所有的本地化文件，以字典形式储存。这一步会检测所有本地化值的引号是否闭合，默认所有本地化值只有一行。
4. 处理嵌套字典，将`RawGameObject`类变为有各自独特属性的`GameObject`类。这一步会检测游戏对象是否有特定的属性，和属性的类型是否正确，
比如检测某个商品的基础价格是否存在，以及是否是整数或浮点数。
5. 将`GameObject`类转变为`Info`类，使其能够被`Calculator`类处理。这一步会检测游戏对象的某些属性是否有定义，比如建筑的建筑组是否存在。
6. 由`Calculator`类进行计算并输出为excel表格。

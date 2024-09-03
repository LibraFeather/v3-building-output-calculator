# 建筑产值简易计算工具v0.8

Calista C.Manstainne，Recognized User L，15/08/2024

本工具可实现如下功能：

- 通过读取游戏文件，自动计算建筑的所有生产方式组合，并计算此组合下的利润、人均利润和回报率，计算结果以excel文件形式输出

适配版本：1.7.6

## 使用前操作

### 安装Python

本工具基于Python开发，因此需要安装Python解释器来运作。

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

1. **配置游戏文件路径**：打开`config\path.py`文件，将`VANILLA_PATH`变量修改为`Victoria 3\game`的路径。
2. **运行程序**：运行`calculator.py`。
3. **查看结果**：结果会被输出至`_output\buildings`文件夹。

## 注意事项

本程序计算的利润仅基于建筑生产和消耗的商品，且仅考虑基础价格，如果建筑存在其他效果，或者建筑受到其他修正影响，本程序不会考虑这些，因此计算结果和真实值可能存在偏差。

### mod相关

1. 本工具可以计算mod建筑的产值，但是需要你的代码格式与原版文件保持一致。如果格式有很大的不同，可能会导致计算出现问题。在运行过程中，如果遇到异常，这个工具会尝试告诉你在哪里出现了问题。
2. 如果要计算mod建筑，可以将mod文件复制进`input`文件夹（不是mod文件夹，而是mod文件夹内的文件），或者可以在`config\path.py`文件里将`MOD_PATH`变量修改为mod的路径，程序会自动读取`metadata.json`，以确定哪些文件夹需要覆盖原版文件。
3. 在生成总表时，如果所有建筑的生产方式都小于五个，那么这个工具会试图把所有的自动化生产方式都归类到一列。但是，如果生产方式组的名称并非“自动化”（用中文本地化进行判断），那么工具将无法正确识别。这不会导致错误，只是可能会把一些生产方式错误地归类到自动化列。
4. 程序只会识别`<pm>.building_modifiers`中的一部分`modifier`：
   1. `workforce_scaled`和`level_scaled`中的
      1. `goods_input/output_<good>_add`
      2. `building_employment_<pop_type>_add`
   2. `unscaled`中的
      1. `goods_input/output_<good>_add/mult`
5. 程序会将`technology`的`era`转化为`int`变量，读取方式是读取`era`变量的最后一个字符。

# 建筑产值简易计算工具v0.8

Calista C.Manstainne，Recognized User L，07/09/2024

本工具可实现如下功能：

- 通过读取游戏文件，自动计算建筑的产出信息，结果以excel文件形式输出。

适配版本：1.7.6

## 使用前操作

### 安装Python

本工具基于Python开发，因此需要安装Python解释器来运作。

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

1. **配置游戏文件路径**：打开`config\path.py`文件，将`VANILLA_PATH`变量修改为`Victoria 3\game`的路径。
2. **运行程序**：运行`calculator.py`。
3. **查看结果**：结果会被输出至`_output\buildings`文件夹。

## 注意事项

本程序计算的利润仅基于建筑生产和消耗的商品，且仅考虑基础价格，如果建筑存在其他效果，或者建筑受到其他修正影响，本工具不会考虑，因此计算结果和真实值可能存在偏差。

### mod相关

1. 本工具可以计算mod建筑的产值，但是可能因为代码格式导致程序出错。
2. 在运行过程中，如果遇到异常，本工具会尝试显示出现了何种格式问题。
3. 计算mod建筑时，可以选择：
   1. 在`config\path.py`文件里将`MOD_PATH`变量修改为mod的路径，程序会自动读取`metadata.json`，以确定哪些文件夹需要覆盖原版文件。
   2. 将mod文件复制进`_input`文件夹（不是整个文件夹，而是文件夹内的文件）。
4. 在生成总表时，如果所有建筑的生产方式都小于五个，那么本工具会试图把所有的自动化生产方式都归类到一列（需要生产方式组的中文本地化为“自动化”）。如果四个生产方式都不满足条件，第三个生产方式组的生产方式会出现在“自动化”列下。
5. 程序只会识别`<pm>.building_modifiers`中的一部分`modifier`：
   1. `workforce_scaled`和`level_scaled`中的
      1. `goods_input/output_<good>_add`
      2. `building_employment_<pop_type>_add`
   2. `unscaled`中的
      1. `goods_input/output_<good>_add/mult`
6. 程序会将`technology`的`era`转化为`int`变量，解析方式是通过正则表达式捕获`era`变量中的第一段连续数字，这可能无法处理某些命名。

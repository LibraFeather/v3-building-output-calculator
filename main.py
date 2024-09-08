import sys

from models.calculator import Calculator

calculator = Calculator()
calculator.output()
if getattr(sys, "frozen", False):
    input("按回车键退出")

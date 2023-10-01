# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/8/19 8:53
@Auth: 泡芙芙的猫窝
@File: converters.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

# 自定义路由转换器

# 验证当前用户名是否符合命名规则
class UsernameConverter:
    regex = '[a-zA-Z0-9_-]{5,20}'

    def to_python(self, value):
        return value


# 手机号转换器
class MobileConverter:
    regex = '1[3-9]\d{9}'

    def to_python(self, value):
        return str(value)  # 转换为str


# uuid转换器
class UUIDConverter:
    regex = '[\w-]+'

    def to_python(self, value):
        return value
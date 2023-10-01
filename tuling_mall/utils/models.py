# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/19 14:16
@Auth: 泡芙芙的猫窝
@File: models.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

# 多个表中可能会使用到时间创建的功能

from django.db import models

# 模型类基类
class BaseModel(models.Model):
    """时间字段"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    """
    我们创建完表之后进行同步时，当前这个BaseModel当成有个普通的表进行创建
    在业务模块中继承当前这个类，并创建父类的字段
    该模型类基类并不需要单独的创建一个表
    """
    class Meta:
        # 表名这个类是一个抽象模型类  用于继承  不会对当前这个类迁移时产生一个单独的表
        abstract = True
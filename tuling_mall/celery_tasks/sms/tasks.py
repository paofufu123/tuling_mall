# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/17 17:44
@Auth: 泡芙芙的猫窝
@File: tasks.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

# 任务名字必须叫tasks.py


# 发送短信任务
from libs.yuntongxun.sms import CCP
from celery_tasks.main import  app

# 1. 任务函数必须使用celery实例中的task装饰器进行装饰
# 2. 当任务加上装饰器之后则celery就可以进行任务检测了
@app.task
def celery_send_sms_code(mobile, code):
    CCP().send_template_sms(mobile, [code, 5], 1)

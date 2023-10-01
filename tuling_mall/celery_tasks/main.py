# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/17 17:36
@Auth: 泡芙芙的猫窝
@File: main.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

import os
from celery import Celery


# 1. 设置celery的运行环境，来自manage.py中的代码
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tuling_mall.settings')

# 2. 创建celery实例，main参数是指当前脚本的父级路径
app = Celery(main='celery_tasks')

# 3.通过配置文件设置生产者
# config_from_object(配置文件路径)
app.config_from_object('celery_tasks.config')

# 4.使用celery自动检测任务，需要将指定的任务路径写入到当前的配置项中
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])


# 5.在终端中启动celery进行并发处理，在项目根目录之下
# celery启动需要注意你当前的电脑系统版本
# MacOS or Linux
    # celery -A celery_tasks.main worker -l INFO
# Windows
    # 1. 下载eventlet
    # 2. 启动指令
        # celery -A celery_tasks.main worker -l INFO -P eventlet -c 1000


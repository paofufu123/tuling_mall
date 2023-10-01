# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/21 14:04
@Auth: 泡芙芙的猫窝
@File: storage.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""


"""
自定义文件存储类
"""
from django.core.files.storage import Storage

# 1. 继承Storage类
class MyStorage(Storage):
    # 2. 重写 _open()和_save()方法
    """
    复制Storage类的open()与save()方法
    代码体内容改为pass
    方法名前`_`：
        open → _open
        save → _save
    """
    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content, max_length=None):
        pass

    # 3.重写url方法
    def url(self, name):
        # name字段其实就是 数据表中image字段中的file_id
        return 'http://172.26.200.150:8888/' + name

# 4. 在settings.py中进行配置
# FastDFS的存储类配置
# DEFAULT_FILE_STORAGE = 'utils.FastDFS.storage.MyStorage'





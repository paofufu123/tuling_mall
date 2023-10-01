# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/22 15:01
@Auth: 泡芙芙的猫窝
@File: search_indexes.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""


from haystack import indexes
from .models import SKU

# 需要在模型所对应的子应用中创建search_indexes文件
class SKUIndexes(indexes.SearchIndex, indexes.Indexable):
    """
    SKU索引数据模型类
        每一个searcIndex索引类必须且只能有一个text字段 用于指定哪些字段作为主要的搜索关键字
        document=True 表示允许文档搜索
        use_template=True 允许用户自定义搜索文档
        搜索文档需要自己建立：templates/
    """
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 根据SKU模型生成索引数据
        return SKU

    def index_queryset(self, using=None):
        # SKU.objects.filter(is_launched=True)
        return self.get_model().objects.filter(is_launched=True)



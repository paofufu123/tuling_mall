# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/22 19:27
@Auth: 泡芙芙的猫窝
@File: crons.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

import os
import time
from django.conf import  settings
from django.template import loader
from .models import ContentCategory
from utils.goods import get_categories

# 页面静态化 [将数据固定的页面写入到指定目录-前端front_end_pc]
def generate_static_index_html():
    # 生成静态html文件
    print('%s: generate_static_index_html' % time.ctime())

    # 获取到商品频道和分类信息
    categories = get_categories()

    # 广告内容
    contents = dict()
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 渲染模板
    context = {
        'categories': categories,
        'contents': contents
    }

    # 获取首页的html文件
    template = loader.get_template('index.html')

    # 渲染首页的html字符串
    html_text = template.render(context)

    # 将html文件写入到指定文件夹中，文件名为index.html
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'front_end_pc/index.html')
    print(file_path)
    with open(file_path,'w',encoding='utf-8') as f:
        f.write(html_text)


"""
首页一般都是由开发工程师配置
详情页是由运营部门配置的
详情页较为特殊，不使用定时任务，而是手动生成
放置在Django目录之下的script文件夹中,新建detail.py
"""

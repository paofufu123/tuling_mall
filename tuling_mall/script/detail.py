# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/22 19:56
@Auth: 泡芙芙的猫窝
@File: detail.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

# 搭建Django环境
import os, sys
import django

# 1.找到当前项目的上一级目录
sys.path.insert(0, '../')

# 2.在项目根目录中找到settings.py文件配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tuling_mall.settings')

# 3.将找到的这个文件夹交给django运行
django.setup()


from goods.models import SKU
from utils.goods import get_categories, get_goods_specs, get_breadcrumb
from django.conf import settings

# 商品详情页静态化
def generate_detail_html(sku):
    # 1. 分类数据
    categories = get_categories()
    # 2.面包屑数据
    breadcrumb = get_breadcrumb(sku.category)
    # 3. 规格信息
    goods_specs = get_goods_specs(sku)

    # 4. 组织数据
    context = {
        'categories': categories,
        'breadcrumb': breadcrumb,
        'sku': sku,
        'specs': goods_specs
    }

    # 模板获取
    from django.template import loader
    detail_template = loader.get_template('detail.html')

    # 模板渲染
    detail_html_data = detail_template.render(context)

    # 写入文件
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'front_end_pc/goods/%s.html' % sku.id)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(detail_html_data)
        print(sku.id)


# 查询当前商品的所有详情数据
skus = SKU.objects.all()
for sku in skus:
    generate_detail_html(sku)






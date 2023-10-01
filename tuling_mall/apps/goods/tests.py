from django.test import TestCase

# Create your tests here.


import os
import django
### 把test02 改成自己的项目名即可
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tuling_mall.settings")
django.setup()

from goods.models import GoodsCategory, GoodsChannel, GoodsChannelGroup, SKU
from collections import OrderedDict

# 封装商品分类数据

# 数据顺序不能变，固定的
def get_goods_categories():
    # index = 1
    # categories = OrderedDict()  # 声明有序字典对象
    # # 获取中间表tb_goods_channel的所有实例，以 group_id 和 sequence为条件进行判断
    # category_list = GoodsChannel.objects.all().order_by('group_id', 'sequence')
    # # 遍历商品实例
    # for category in category_list:
    #     print(index, category)
    #     index += 1
    #     group_id = category.group_id  # 获取组id
    #
    #     if group_id not in categories:
    #         # 构造商品分类框架, group_id 为key
    #         categories[group_id] = {
    #             'channels': [],
    #             'sub_cats': []
    #         }
    #
    #     cats1 = category.category   # 一级分类实例
    #
    #     # 一级分类
    #     categories[group_id]['channels'].append({
    #         'id': cats1.id,
    #         'name': cats1.name,
    #         'url': category.url
    #     })
    #
    #     # 二级分类
    #     cats2 = cats1.subs.filter(parent_id=cats1.id)  # 获取所有二级分类实例
    #     for cat2 in cats2:
    #         cat2.sub_cats = []
    #         # categories[group_id]['sub_cats'].append({
    #         #     'id': cat2.id,
    #         #     'name': cat2.name,
    #         # })
    #         # 三级分类
    #         cats3 = cat2.subs.filter(parent_id=cat2.id)  # 获取所有的三级分类实例
    #         for cat3 in cats3:
    #             cat2.sub_cats.append(cat3)
    #
    #         categories[group_id]['sub_cats'].append(cat2)
    # 查询商品频道和分类
    categories = OrderedDict()

    # 从 GoodsChannel 模型中获取所有数据。
    # 查询结果将按照 group_id 的升序排列，如果 group_id 相同，则按照 sequence 的升序排列。
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        group_id = channel.group_id  # 当前组

        if group_id not in categories:
            # 如果当前组不在categories有序字典中，那么就添加当前组信息
            categories[group_id] = {'channels': [], 'sub_cats': []}

        cat1 = channel.category  # 当前频道的类别
        """
        category 是外键
        因为 cat1是 当前 channel 对象关联的 GoodsCategory 对象
        所以 可以通过 cat1 访问 GoodsCategory 对象的所有属性和方法
        - type(cat1)   # <class 'goods.models.GoodsCategory'>
        """
        # print(type(cat1), cat1.name, type(cat1.name), cat1.id, type(cat1.id))
        # 只粘贴一条结果
        # <class 'goods.models.GoodsCategory'> 手机 <class 'str'> 1 <class 'int'>

        # 追加当前频道 【一级分类】
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })
        # 构建当前类别的子类别【二级分类】
        for cat2 in cat1.subs.all():
            # cat1.subs.all() 获取的是与一级分类有绑定关系的所有二级分类【自关联】
            # print(type(cat2), cat2.name, cat2.id)
            cat2.sub_cats = []  # 存储【三级分类】
            for cat3 in cat2.subs.all():
                # cat2.subs.all() 获取的是与二级分类有绑定关系的所有三级分类【自关联】
                # print(type(cat3), cat3.name, cat3.id)
                cat2.sub_cats.append(cat3)
                # print(cat2.sub_cats)  # 查看三级分类
            categories[group_id]['sub_cats'].append(cat2)
    print(categories)

    for index, group in categories.items():
        print(index, group)
        for channel in group.get('channels'):
            print(channel.get('name'), channel.get('url'))
        for cat2 in group.get('sub_cats'):
            print(cat2)







    # print(categories)

# get_goods_categories()

from contents.models import Content,ContentCategory
def get_content():
    contents = {}
    # ads = Content.objects.filter(status=True).order_by('category_id', 'sequence')
    # # 遍历
    # for ad in ads:
    #     keys = ad.category.keys
    #     if not keys in contents:
    #         # 构造广告结构
    #         contents[keys] = []
    #     # 以key为键
    #     contents[keys].append({
    #         'id': ad.id,
    #         'title': ad.title,
    #         'url': ad.url,
    #         'default_image_url': ad.image
    #     })
    # print(contents)
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')
    print(contents)

# get_content()



# 面包屑

def get_breadcrumb(category):
    # category是实例
    dict1 = {
        'cat1': '',
        'cat2': '',
        'cat3': ''
    }
    if category.parent is None:
        # 一级
        dict1['cat1'] = category.name
    elif category.parent.parent is None:
        # 二级
        dict1['cat2'] = category.name
        dict1['cat1'] = category.parent.name
    else:
        # 三级
        dict1['cat3'] = category.name
        dict1['cat2'] = category.parent.name
        dict1['cat1'] = category.parent.parent.name




# 商品规格
"""
SKUSpecification模型类  tb_sku_specification是中间表
SpecificationOption模型类 tb_specification_option 规格选项表
SPUSpecification模型类  tb_spu_specification 商品SPU规格
"""
# def get_goods_specs(sku):
#     """
#     获取商品的规格信息
#     :param sku: 商品sku实例对象
#     :return:
#     """
#     ### 构建当前商品的【规格键】
#     """
#     sku.specs 指向 SKUSpecification模型类 [SKU具体规格]
#     """
#     # 获取 SKUSpecification模型类 [SKU具体规格] 的所有实例，按照spec_id升序排序
#     sku_specs = sku.specs.order_by('spec_id')
#     sku_key = [] # 初始化列表，存储当前商品的规格键
#     # 遍历所有的具体规格实例对象
#     for spec in sku_specs:
#         """
#         spec.option 指向 SpecificationOption模型类 [规格选项]
#         """
#         # 构建当前商品的规格键
#         # 将 SpecificationOption模型类 [规格选项] 的id添加到sku_key中
#         sku_key.append(spec.option.id)
#     print('sku_key: ', sku_key)
#
#
#     # 获取当前商品SPU的所有SKU实例
#     """
#     sku.spu 指向 SPU模型类 [商品SPU]
#     sku.spu.sku_set 从SPU模型类反向关联SKU模型类
#     """
#     skus = sku.spu.sku_set.all()
#     # 构建不同规格参数（选项）的sku字典
#     spec_sku_map = {}
#     # 遍历每个SKU实例
#     for s in skus:
#         # 获取sku的规格参数
#         """
#         s.specs 反向关联SKUSpecification [SKU具体规格]
#         """
#         s_specs = s.specs.order_by('spec_id')
#         # 用于形成规格参数-sku字典的键
#         keys = []
#         # 遍历每个具体规格对象
#         for spec in s_specs:
#             # 将每个具体规格对象的选项ID添加到key列表中，形成规格参数-SKU字典的键
#             keys.append(spec.option.id)
#         # 向规格参数-sku字典添加记录，将构建好的规格键作为键，对应的SKU ID作为值
#         spec_sku_map[tuple(keys)] = s.id
#     print('spec_sku_map: ', spec_sku_map)
#
#     # 以下代码为：在每个选项上绑定对应的sku_id值
#     # 获取当前商品的SPU规格信息，按照id升序排序
#     """
#     sku.spu 关联到 SPU模型
#     sku.spu.specs 反向关联到 SPUSpecification [商品SPU规格]
#     """
#     goods_specs = sku.spu.specs.order_by('id')
#     # 若当前sku的规格信息不完整，则不再继续
#     if len(sku_key) < len(goods_specs):
#         return
#     for index, spec in enumerate(goods_specs):
#         # 复制当前sku的规格键，以便在后面的循环中对其进行修改。
#         keys = sku_key[:]
#         # print('keys: ',keys)
#         # 获取当前规格的所有选项
#         """
#         spec.options 反向关联 SpecificationOption模型类 [规格选项]
#         """
#         spec_options = spec.options.all()
#         # 遍历当前规格的每个选项
#         for option in spec_options:
#             # 在规格参数SKU字典中查找符合当前规格的SKU，将当前选项的ID替换到对应位置上
#             keys[index] = option.id
#             # 通过规格参数SKU字典spec_sku_map，根据构建好的规格键获取对应的SKU ID，并将其赋值给当前选项。
#             option.sku_id = spec_sku_map.get(tuple(keys))
#         # 将当前规格的所有选项赋值给spec.spec_options
#         spec.spec_options = spec_options
#         print('spec: ', spec)
#
#     print(goods_specs)





def get_goods_specs(sku):
    # 构建当前商品的规格键
    sku_specs = sku.specs.order_by('spec_id')
    sku_key = []
    for spec in sku_specs:
        sku_key.append(spec.option.id)

    # 获取当前商品的所有SKU
    skus = sku.spu.sku_set.all()
    # 构建不同规格参数（选项）的sku字典
    spec_sku_map = {}
    for s in skus:
        # 获取sku的规格参数
        s_specs = s.specs.order_by('spec_id')
        # 用于形成规格参数-sku字典的键
        key = []
        for spec in s_specs:
            key.append(spec.option.id)
        # 向规格参数-sku字典添加记录
        spec_sku_map[tuple(key)] = s.id

    # 以下代码为：在每个选项上绑定对应的sku_id值
    # 获取当前商品的规格信息
    goods_specs = sku.spu.specs.order_by('id')
    # 若当前sku的规格信息不完整，则不再继续
    if len(sku_key) < len(goods_specs):
        return
    for index, spec in enumerate(goods_specs):
        # 复制当前sku的规格键
        key = sku_key[:]
        # 该规格的选项
        spec_options = spec.options.all()
        for option in spec_options:
            # 在规格参数sku字典中查找符合当前规格的sku
            key[index] = option.id
            option.sku_id = spec_sku_map.get(tuple(key))
        spec.spec_options = spec_options

    return goods_specs


def get_goods_specs1(sku):
    goods_specs = sku.spu.specs.order_by('id')
    for specs in goods_specs:
        print(specs)
    return goods_specs

"""
specs.options.all()[0].value
"""

if __name__ == '__main__':
    try:
        sku = SKU.objects.get(id=2)
        print(sku)
        # 2: Apple MacBook Pro 13.3英寸笔记本 深灰色
        print('================')
        # get_goods_specs(sku)
        # print(get_goods_specs(sku))
        specs = get_goods_specs(sku)
        for spec in specs:
            print('=======================')
            print('spec.name ==> ', spec.name)
            for option in spec.spec_options:
                print('【option】 -->', option)
                print('option.sku_id ==> ', option.sku_id)
                print('sku_id ==> ', sku.id)
                if option.sku_id == sku.id:
                    print('二者相等')
                    print('option.value ==>', option.value)
                    print('*********************************')
                elif option.sku_id:
                    print('option.sku_id存在 ===》', option.sku_id)
                    print('option.value ==>', option.value)
                    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
                else:
                    print('option.sku_id不存在')
                    print('option.value ==>', option.value)
                    print('###############################33333')



        print('=======================')
        # print(get_goods_specs1(sku))
        # <QuerySet [<SPUSpecification: Apple MacBook Pro 笔记本: 屏幕尺寸>, <SPUSpecification: Apple MacBook Pro 笔记本: 颜色>, <SPUSpecification: Apple MacBook Pro 笔记本: 版本>]>
    except Exception as e:
        print(e)



def test():
    s = [1,2,3]
    y = [3,4,5]
    if len(s) == len(y):
        print('s的长度=y的长度')
        return
    print(dict(zip(s, y)).items())
    for x,z in dict(zip(s,y)).items():
        print(x, z)


# test()

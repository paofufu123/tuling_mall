# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/25 21:10
@Auth: 泡芙芙的猫窝
@File: utils.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

"""
购物车合并功能
以cookie为同步目标：将cookie数据拿出来添加到redis
"""

"""
用户登录了，才能进行购物车合并
"""
import pickle, base64
from django_redis import get_redis_connection

def carts_merge(request, response, user):
    """
    :param request: 所有的请求信息
    :param response: 响应信息
    :param user: 用户信息
    :return:
    """
    # 判断cookie是否有购物车信息
    carts_str = request.COOKIES.get('carts')

    if not carts_str:
        # cookie购物车不存在，直接返回response
        return response

    # 解码
    carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))

    # 初始化字典，保存 sku_id: count
    new_cart_dict = dict()
    # 初始化列表，保存 selected
    selected_list = list()  # 保存选中状态的sku_id
    unselected_list = list() # 保存未选中状态的sku_id

    for sku_id in carts_dict:
        new_cart_dict[sku_id] = carts_dict[sku_id]['count']
        selected = carts_dict[sku_id]['selected']
        if selected:
            selected_list.append(sku_id)
        else:
            unselected_list.append(sku_id)

    # 将cookie购物车合并到redis购物车
    redis_cli = get_redis_connection('carts')
    pipeline = redis_cli.pipeline()
    # 将cookie购物车的sku_id和count合并到hash中
    pipeline.hmset('carts_%s' % user.id, new_cart_dict)
    # 将cookie购物车的selected信息合并到set中
    if selected_list:
        # 选择状态，则将sku_id添加进set
        pipeline.sadd('selected_%s' % user.id, *selected_list)
    if unselected_list:
        # 未选择状态，则删除set中的sku_id
        pipeline.srem('selected_%s' % user.id, *selected_list)
    pipeline.execute()

    # 删除cookie
    response.delete_cookie('carts')
    return response
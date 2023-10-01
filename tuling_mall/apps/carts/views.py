from django.shortcuts import render

# Create your views here.

import json, pickle, base64
from django.views import View
from django.http import JsonResponse
from goods.views import SKU
from django_redis import get_redis_connection

"""
购物车数据
    用户登录状态下，保存
        user_id, sku_id, count, selected
    用户未登录状态下，保存
        sku_id, count, selected
    数据保存在哪里？
        mysql中可不可以？完全可以的，但是没有必要
        如果用户量很大，保存的数据很多，会造成数据库卡顿

        用户登录的话，数据存储在redis, hash数据类型+set数据类型
            hash
                user_id: {
                    sku_id: count
                }
            set
                selected: {sku_id, sku_id}

        用户未登录，则存储在本地的cookie
            cookie: {
                sku_id: {count: 10, selected: True},
                sku_id: {count: 10, selected: True},
                ...
            }

    存储的数据结构：无论是redis的数据还是cookie的数据都是 keys:value 形式
"""
# 添加购物车
"""
    思路分析：
        前端：点击添加购物车之后前端将商品id发送给后端

        后端：
            1. 接收请求
                接收参数并验证参数
                1.1 根据商品id查询数据库中是否存在当前商品
                1.2 数据入库, 数据入库之前需要判断用户登录状态
                    1.登录用户录入redis
                        1.1 链接redis
                        1.2 获取用户id
                        1.3 数据结构组织：hash、set

                    2.未登录用户录入cookie
                      2.1 创建cookie字典
                      2.2 字典转换为bytes
                      2.3 bytes转换为base64
                      2.4 cookie设置
            2. 返回响应
                数据结构：json

            路由：POST /carts/
    """
# 购物车的增删改查操作
class CartsView(View):
    # 获取购物车
    def get(self, request):
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            # 获取hash
            redis_cart = redis_cli.hgetall('carts_%s' % user.id)
            # 获取set
            cart_selected = redis_cli.smembers('selected_%s' % user.id)

            # 将redis中的数据结构与cookie中的数据结构保持一致
            cart_dict = dict()
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }

        else:
            # 用户未登录
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 解码
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = dict()

        # 获取所有的sku_id
        sku_ids = cart_dict.keys()
        # 根据在字典中获取的sku_id进行数据库查询
        skus = SKU.objects.filter(id__in=sku_ids)
        # 构造响应数据
        cart_skus = list()
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': cart_dict.get(sku.id).get('selected'),
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * cart_dict.get(sku.id).get('count')
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})


    # 添加购物车
    def post(self, request):
        # 接收请求
        json_dict = json.loads(request.body)
        # 获取参数
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 验证参数
        # 参数完整性
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数需补全'})

        # 判断sku_id是否在数据库中
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '当前商品不存在'})

        # 判断count是否是整型类型
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 400, 'errmsg': '商品数量有误'})

        # 判断选中状态类型
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': '选中参数类型有误'})

        # 判断用户的登录状态
        user = request.user
        if user.is_authenticated:  # 用户为登录状态
            redis_cli = get_redis_connection('carts')
            # 使用管道可以提高性能
            pipeline = redis_cli.pipeline()
            # 存储hash
            pipeline.hincrby('carts_%s' % user.id, sku_id, count)
            if selected:
                # 存储set
                pipeline.sadd('selected_%s' % user.id, sku_id)
            pipeline.execute()
            # 存储hash
            # redis_cli.hset('carts_%s' % user.id, sku_id, count)
            # redis_cli.hincrby('carts_%s' % user.id, sku_id, count)
            # 存储set
            # redis_cli.sadd('selected_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else: # 用户未登录
            # 如果用户之前操作过购物车，则本地有cookie, 判断当前有没有cookie
            carts_str = request.COOKIES.get('carts')
            if carts_str:
                # 解密
                cart_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                cart_dict = {}

            # 判断当前cookie是否存在sku_id
            if sku_id in cart_dict:
                # 如果存在，表示用户买了不止一件同类商品
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', cookie_cart_str, max_age=7*24*3600)
            return response


    # 修改/更新购物车
    def put(self, request):
        # 获取用户信息
        user = request.user
        # 获取参数
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected') # 非必传项
        # 验证参数
        # 参数完整性
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数需补全'})

        # 判断sku_id是否在数据库中
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '当前商品不存在'})

        # 判断count是否是整型类型
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 400, 'errmsg': '商品数量有误'})

        # 判断选中状态类型
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': '选中参数类型有误'})

        # 判断用户是否登录
        if user.is_authenticated:
            # 用户已登录，更新redis
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            # 更新hash，直接覆盖即可
            pl.hset('carts_%s'%user.id, sku_id, count)
            if selected:
                # 更新set
                pl.sadd('selected_%s'%user.id, sku_id)
            else:
                # 删除set
                pl.srem('selected_%s'%user.id, sku_id)
            pl.execute()
            # 构造数据
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count
            }
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': cart_sku})
        else:
            # 用户未登录，更新cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = dict()

            # 数据更新
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 编码
            cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price*count
            }
            # 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_cart_str, max_age=7*24*3600)
            return response


    # 删除购物车
    def delete(self, request):
        # 获取要删除的数据
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')

        # 判断sku_id在数据库中是否存在
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '商品不存在'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            pl.hdel('carts_%s'%user.id, sku_id)  # 删hash
            pl.srem('selected_%s'%user.id, sku_id) # 删set
            pl.execute() # 管道执行
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = dict()

            # 创建响应对象
            response = JsonResponse({'code': 0, 'errmsg': '删除数据库成功'})
            if sku_id in cart_dict:
                del cart_dict[sku_id] # 删cookie
                cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cookie_cart_str, max_age=7*24*3600)
            return response


# 购物车[取消]全选
class CartsSelectAllView(View):
    def put(self, request):
        # 接收参数
        selected = json.loads(request.body).get('selected', True)

        # 验证
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': 'selected参数类型有误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作redis
            redis_cli = get_redis_connection('carts')
            redis_cart = redis_cli.hgetall('carts_%s' % user.id)

            # 获取所有的sku_id  <list>
            sku_ids = redis_cart.keys()
            # 更新购物车所有商品的selected
            if selected: # 【全选操作】
                # 如果用户在页面中点击了全选，则将获取到的所有的sku_id放入set中
                redis_cli.sadd('selected_%s' % user.id, *sku_ids)
            else: # 【取消全选操作】
                # 如果用户在页面中取消了全选，则将set中所有的sku_id删除
                redis_cli.srem('selected_%s' % user.id, *sku_ids)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 用户未登录，操作cookie
            cart_str = request.COOKIES.get('carts')
            # 声明响应对象，通过响应对象设置cookie信息
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected
                cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cookie_cart_str, max_age=7*24*3600)
            return response


# 商品首页购物车粗略信息
class CartSimpleView(View):
    def get(self, request):
        user = request.user
        # 判断用户是否登录
        if user.is_authenticated:
            # 用户已登录，操作redis
            redis_cli = get_redis_connection('carts')
            redis_cart = redis_cli.hgetall('carts_%s' % user.id) # 获取hash
            cart_selected = redis_cli.smembers('selected_%s' % user.id) # 获取set

            #构造和cookie结构一样的字典数据
            cart_dict = dict()
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 用户未登录，操作cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = dict()

        # 获取所有的sku_id
        skus_id = cart_dict.keys()
        # 获取所有sku_id代表的商品
        skus = SKU.objects.filter(id__in=skus_id)
        # 构造响应数据
        cart_skus = list()
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})





from django.shortcuts import render

# Create your views here.
import json
from datetime import datetime
from decimal import Decimal
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.db import transaction
from utils.views import LoginRequiredJsonMixin
from users.models import Address
from goods.models import SKU
from .models import OrderInfo, OrderGoods

"""
前端：发送请求获取地址信息和购物车选中的商品信息
后端：
    必须时登录用户才能访问订单页面
    业务逻辑：
        地址信息和购物车选中的商品信息  数据查询
    响应：json
    路由： GET orders/settlement/
"""
# 订单结算页面展示
class OrderSettlementView(LoginRequiredJsonMixin, View):
    def get(self, request):
        # 获取用户信息
        user = request.user

        # 获取redis中被选中的商品信息
        redis_cli = get_redis_connection('carts')
        redis_carts = redis_cli.hgetall('carts_%s' % user.id)
        carts_selected = redis_cli.smembers('selected_%s' % user.id)

        cart = dict()
        # 存储被选中商品的购物车信息 {sku_id: count}
        for sku_id in carts_selected:
            cart[int(sku_id)] = int(redis_carts[sku_id])

        # 组织商品信息
        sku_list = list()
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'count': cart.get(sku.id),
                'amount': sku.price * cart.get(sku.id)
            })

        # 运费
        from decimal import Decimal
        freight = Decimal('10.00')

        # 获取用户所有的地址信息
        addresses = Address.objects.filter(user=user, is_deleted=False)
        # 组织地址数据
        addresses_list = list()
        for address in addresses:
            addresses_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        # 数据响应
        context = {
            'skus': sku_list,
            'freight': freight,
            'addresses': addresses_list
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'context': context})


# 提交订单
class OrderCommitView(LoginRequiredJsonMixin, View):
    def post(self, request):
        # 接收请求
        json_dict = json.loads(request.body)
        # 接收参数
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 验证参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '请选择地址和支付方式'})

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '当前地址不存在'})

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '参数pay_method有误'})

        """订单基本信息保存"""
        # 获取用户信息
        user = request.user

        # 生成订单编号
        from datetime import datetime
        order_id = datetime.now().strftime('%Y%m%d%H%M%S%f') + ('%09d' % user.id)

        # 因为订单数据的保存会涉及多张表的修改、保存操作，为了保持数据的原子性，使用事务
        # 使用上下文管理开启数据库事务
        with transaction.atomic():
            # 创建事务起始点
            point = transaction.savepoint()

            # 暴力回滚
            try:
                order = OrderInfo.objects.create(
                    order_id = order_id,
                    user = user,
                    address = address,
                    total_count = 0,
                    total_amount = Decimal('0'),
                    freight = Decimal('10.00'),
                    pay_method = pay_method,
                    status = OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == 2 else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                """保存商品信息表"""
                # 查询redis中已被勾选的商品
                redis_cli = get_redis_connection('carts')
                redis_cart = redis_cli.hgetall('carts_%s' % user.id)
                selected = redis_cli.smembers('selected_%s' % user.id)

                # 组织redis的数据结构为字典, 存储被选中的商品
                carts = dict()
                for sku_id in selected:
                    carts[int(sku_id)] = int(redis_cart[sku_id])

                # 遍历购物车中被勾选的商品信息
                sku_ids = carts.keys()
                for sku_id in sku_ids:
                    while True:
                        # 查询SKU信息
                        sku = SKU.objects.get(id=sku_id)
                        # 获取购物车对应的商品数量
                        sku_count = carts[sku.id]

                        """
                        当前代码的判断是在表数据插入之后才进行的
                        如果当前的库存数<购物车数量，那么当前就不能创建订单信息
                        如果订单信息还是创建了，那么这就是一条"垃圾数据"
                        ask: 
                            如何保证库存数>购物车数量，才创建订单？
                            库存出<购物车数量，不创建订单？
                        solution: 事务
                            from django.db import transaction
                        """
                        # 商品数量>库存数量，返回错误信息，并进行数据回滚
                        if sku_count > sku.stock:
                            # 事务回滚点
                            transaction.savepoint_rollback(point)
                            return JsonResponse({'code': 400, 'errmsg': '库存不足'})

                        # 模拟延迟
                        import time
                        time.sleep(5)

                        ##### 这几段代码会带来超卖问题
                        # sku减少库存，增加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        ##### 这几段代码会带来超卖问题


                        # 使用乐观锁解决超卖问题
                        old_stock = sku.stock
                        new_stock = old_stock - sku_count
                        new_sales = sku.sales + sku_count

                        # 数据没有改动就进行更新
                        result = SKU.objects.filter(id=sku.id, stock=old_stock).update(stock=new_stock,sales=new_sales)
                        if not result:
                            # 如果result为0则表示数据已被修改
                            # return JsonResponse({'code': 400, 'errmsg': '下单失败'})
                            continue   # 跳出本次循环

                        # 保存商品信息
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 更新订单基本信息中的总价和商品总数
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)

                        # 如果下单成功或者失败则跳出循环
                        break

                # 添加邮费和保存订单信息
                order.total_amount += order.freight
                order.save()

                # 事务提交点[with上下文管理协议会自动提交事务，可写也可不写]
                transaction.savepoint_commit(point)
            except Exception:
                # 下单失败返回事务起始点
                transaction.savepoint_rollback(point)
                return JsonResponse({'code': 400, 'errmsg': '下单失败'})

        # 清除购物车中已结算的商品
        pl = redis_cli.pipeline()
        pl.hdel('carts_%s' % user.id, *selected)
        pl.srem('selected_%s' % user.id, *selected)
        pl.execute()

        # 响应提交订单结果
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'order_id': order.order_id})


"""
有bug
当用户提交订单信息时，会发生超卖问题
线程：资源竞争问题
"""


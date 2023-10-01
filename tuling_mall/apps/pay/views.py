from django.shortcuts import render

# Create your views here.


"""
sdk下载: pip install python-alipay-sdk

开发需求:
    1. 生成跳转到支付宝的链接
    2. 保存交易完成后支付宝返回的交易流水号

开发步骤:
    1.设置交易公钥和私钥
        openssl
        OpenSSL> genrsa -out app_private_key.pem   2048  # 私钥
        OpenSSL> rsa -in app_private_key.pem -pubout -out app_public_key.pem # 导出公钥
        OpenSSL> exit

    2.将私钥放入key目录之下，将项目公钥复制到支付宝沙箱环境中

    3.复制支付宝公钥并放入到key文件夹中
"""


from django.http import JsonResponse
from django.views import View
from utils.views import LoginRequiredJsonMixin
from orders.models import OrderInfo
from django.conf import settings
from .models import Payment

"""
后端:
    获取前端传递过来的订单id
    验证订单id-根据前端传递的id进行数据查询
    读取应用私钥和支付宝公钥
    创建支付宝实例对象
    调用支付宝的支付方法
    拼接回调链接
    返回响应
路由:  payment/order_id/
"""

# 生成支付宝支付链接，跳转支付页面
class PayUrlView(LoginRequiredJsonMixin, View):
    def get(self, request, order_id):
        # 获取用户信息
        user = request.user

        # 订单信息验证
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                user=user
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '此订单不存在'})

        # 读取图灵商城私钥和支付宝公钥
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH, 'r', encoding='utf-8').read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH, 'r', encoding='utf-8').read()

        # 创建支付宝实例对象
        from alipay import AliPay, AliPayConfig
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type='RSA2', # 加密规则
            debug=settings.ALIPAY_DEBUG,
            config=AliPayConfig(timeout=60), # 当前配置项可以不用配置
        )

        # 创建支付订单，生成支付链接的部分内容
        # api_alipay_trade_page_pay 当前支付方式针对于页面
        order_string = alipay.api_alipay_trade_page_pay(
            subject='图灵商城测试订单',
            out_trade_no=order_id,
            # 支付宝无法将货币类型转为json数据格式，因此需要将类型转为str
            total_amount=str(order.total_amount),
            return_url=settings.ALIPAY_RETURN_URL
        )

        # 拼接回调地址
        pay_url = settings.ALIPAY_URL + '?' + order_string

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'alipay_url': pay_url})



"""
保存支付宝订单流水号
    前端：当用户支付完成之后会跳转到支付成功页面，在跳转的过程中携带了查询字符串信息
    将查询字符串信息传递给后端
    
    后端：
        请求：PUT 接收数据
        业务逻辑：将查询字符串中的数据转为字典并进行验证
        路由：PUT /payment/status/
"""
# 订单状态更改
class PaymentStatusView(View):
    def put(self, request):
        # 接收数据
        data = request.GET
        # 提取并删除查询字符串中的sign
        data = data.dict()
        sign = data.pop('sign')

        # 读取图灵商城私钥和支付宝公钥
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH, 'r', encoding='utf-8').read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH, 'r', encoding='utf-8').read()

        # 创建支付宝实例对象
        from alipay import AliPay, AliPayConfig
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type='RSA2',  # 加密规则
            debug=settings.ALIPAY_DEBUG,
            config=AliPayConfig(timeout=60),  # 当前配置项可以不用配置
        )

        # 验证支付宝支付状态
        success = alipay.verify(data, sign)
        if success:
            # 支付宝交易流水号
            trade_no = data.get('trade_no')
            # 订单号
            order_id = data.get('out_trade_no')

            # 将交易流水号进行保存
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_no
            )

            # 更新订单状态
            OrderInfo.objects.filter(order_id=order_id).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
            )
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'trade_id': trade_no})
        else:
            return JsonResponse({'code': 400, 'errmsg': '订单更新失败'})




"""
当前支付宝支付功能使用的是沙箱操作
    沙箱操作和线上环境基本是一样的
"""


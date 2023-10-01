from django.shortcuts import render

# Create your views here.
"""
restful的规则：
    规则1：我们之后再视图类中编写操作方法需要对应http请求
    规则2：在`/`后需要编写获取的物品的名词，如`/products`
        名词全部都为复数形式
        获取id为4的物品时，如`/products/4`
    当前的业务模型为前后端分离
        需要通过url进行交互
    http：在网站开发中一般使用以下请求方法
        get【获取】
            /products/ 获取全部商品
            /products/4 获取全部商品
        post【增加】
            /products/  
        put【修改】
            /products/1
        delete【删除】
            /products/1
"""
"""
判断用户名是否重复
    后端思路：
        接收请求 --》接收前端所发送过来的用户名
    业务逻辑：
        根据用户名查询数据库，如果查询数量等于0则没有注册
        否则就已经注册过
    响应：
        json
        {code: 0/1, errmsg: ok/error_message}
    步骤：
        1.接收用户名
        2.根据用户名查询数据
        3.返回响应
"""
from django.views import View
from .models import User  # 导入模型
from django.http import JsonResponse
import json,re
from django.contrib.auth import login
from django_redis import get_redis_connection


# 用户名是否重复
class UsernameCountView(View):
    """统计用户名数量"""
    # 获取用户姓名
    def get(self,request,username):
        # 1.获取到用户名称之后查询用户名称数量
        count = User.objects.filter(username=username).count()
        # 2.返回响应
        # 后端传递count信息给前端
        return JsonResponse({"code":0,"count":count,"errmsg":"ok"})


# 手机号是否重复
class MobileCountView(View):
    def get(self, request, mobile):
        mobile_count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 0, 'count': mobile_count, 'errmsg': 'ok'})


'''
关于用户注册的功能实现
    获取前端所传送过来的数据
    验证前端所传送过来的数据的正确性
    完成用户注册之后的状态保持
    完成前端页面中的图片验证码

代码编写步骤：
    1. 接收请求
    2. 获取数据
    3. 验证数据
        3.1 用户名、密码、确认密码、手机号、协议同一
        3.2 用户名必须满足正则规则且不能重复 页面验证后端是永远不能相信的
        3.3 密码满足规则
        3.4 确认密码与密码是否保持一致
        3.5 手机号满足规则且不能重复
        3.6 协议同意
    4. 数据入库
    5. 返回响应
'''
# 注册功能
class RegisterView(View):
    def post(self, request):
        # 接收数据
        body_dict = json.loads(request.body)
        # 获取参数
        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        sms_code = body_dict.get('sms_code')
        allow = body_dict.get('allow')

        # 验证数据
        if not all([username, password, password2, mobile, sms_code, allow]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 验证用户名
        if not re.match(r'^[A-Za-z0-9]{5,20}',username):
            return JsonResponse({'code': 400, 'errmsg':'username参数有误'})

        # 验证密码
        if not re.match('^[a-zA-Z0-9._@]{8,20}',password):
            return JsonResponse({'code': 400, 'errmsg': 'password参数有误'})

        # 判断两次验证码是否一致
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '两次密码输入不一致'})

        # 判断手机号格式
        if not re.match('1[3-9]\d{9}',mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号格式有误'})

        # 判断短信验证码是否正确
        redis_cli = get_redis_connection('code')
        redis_sms_code = redis_cli.get(mobile)
        if not redis_sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码不存在/失效'})
        if redis_sms_code.decode() != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码输入错误'})

        # 判断是否勾选用户协议
        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '请勾选用户协议'})

        # 数据入库
        user = User.objects.create_user(
            username=username,
            password=password,
            mobile=mobile
        )

        # 在数据入库之后一般有两种选择
        # 1.用户注册完之后跳转到首页并做登录保持 --> 让用户用得更爽
        # 本项目选择登录保持 --> 使用django系统内置的session
        # 2.用户完成注册之后跳转到登录页面让用户重新登录  --> 让用户确保当前的用户名和密码传播构建正确
        login(request, user)

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})



"""
网站的登录功能主要是完成了什么事情？
状态保持
    浏览器当前登录的用户是谁
    在需要权限的页面中进行账户的权限校验
"""
# 用户登录功能
"""
后端：
    请求：接收数据
    业务逻辑：验证用户名和密码是否正确
    响应：JSON
    路由：POST  login/
步骤：
    1.接收数据
    2.验证数据的完整性
    判断是否为手机号登录
    3.验证用户名与密码是否正确
    4.设置session信息
    5.判断是否记住登录
    6.返回响应
"""
class LoginView(View):
    def post(self, request):
        # 接收数据
        json_dict = json.loads(request.body)
        username = json_dict.get('username')
        password = json_dict.get('password')
        remembered = json_dict.get('remembered')

        # 验证数据的完整性
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必要参数'})

        # 判断username是用户名还是手机号,如果是手机号，则使用手机号登录
        """
        因为User模型继承了AbstractUser，所以也拥有USERNAME_FIELD常量
        """
        if re.match('1[3-9]\d{9}',username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        # 验证用户名和密码是否正确
        from django.contrib.auth import authenticate
        """
        from django.contrib.auth import authenticate
        authenticate用于账号验证
        验证通过，返回user对象
        验证失败，返回None
        """
        user = authenticate(username=username, password=password)
        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '账号和密码错误'})

        # 设置session信息
        from django.contrib.auth import login
        login(request, user)

        # 判断是否勾选了记住登录
        if remembered:  # 如果记住登录
            # 设置过期时间,默认有效期2周
            request.session.set_expiry(None)
        else:
            # 关闭浏览器，立即清除session
            request.session.set_expiry(0)

        """
        为了登录成功之后在首页显示用户昵称，则需要设置一个cookie来保存用户的昵称信息
        前端代码获取到这个cookie之后可以直接显示
        """
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.set_cookie('username', username) # 设置cookie

        # 导入购物车合并功能
        from carts.utils import carts_merge
        response = carts_merge(request, response, user)

        return response


# 账号退出
"""
前端：当用户点击了退出按钮之后，发送一个axios请求 delete
后端：
    请求：delete
    业务逻辑：删除session信息和cookie信息
    响应：json
"""
class LogoutView(View):
    def delete(self, request):
        # 删除session  在django框架中提供了用户退出的功能
        from django.contrib.auth import logout
        logout(request)
        # 删除cookie
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')
        return response


# 用户中心
"""
所谓的用户中心就是展示当前用户所登录的账号信息
前提：访问登录页面需要有账号信息
用户中心页面有权限功能
"""
"""
django内部为我们提供了一个账号登录状态验证的功能
    LoginRequiredMixin
"""
# from django.contrib.auth.mixins import LoginRequiredMixin
# # 用户中心
# class CenterView(LoginRequiredMixin, View):
#     方法一：重写LoginRequiredMixin的dispathc()方法
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'code': 400, 'errmsg': '当前无访问权限'})
#         return super().dispatch(request, *args, **kwargs)
#
#     方法二：重写LoginRequiredMixin类中使用到的handle_no_permission方法
#     def handle_no_permission(self):
#         return JsonResponse({'code': 400, 'errmsg': '当前无访问权限'})
#
#     def get(self, request):
#         return JsonResponse({'code':0, 'errmsg': '已登录...'})



# 方法三优化：单独拆分出来成为一个文件
from utils.views import LoginRequiredJsonMixin
class CenterView(LoginRequiredJsonMixin, View):
    def get(self, request):
        # 获取用户信息
        user = request.user
        # 构造用户信息
        info_data = {
            'username': user.username,
            'mobile': user.mobile,
            'email': user.email,
            'email_active': user.email_active
        }

        return JsonResponse({'code':0, 'errmsg': 'ok', 'info_data': info_data})


# 邮箱信息保存与激活邮件信息发送
class EmailView(LoginRequiredJsonMixin, View):
    def put(self, request):
        # 获取用户信息
        user = request.user
        # 获取数据
        email = json.loads(request.body).get('email')

        # 判断邮箱参数是否存在
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        # 验证邮箱格式是否正确
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式不正确'})

        # 保存邮箱
        user.email = email
        user.save()

        # 邮件发送
        """
        Django自带邮件发送功能
        Django调用send_mail进行邮件发送
        邮件服务器：第三方 or 自建邮件服务器
        """
        from users.utils import generic_email_verify_token
        # 在邮箱验证时需要确定邮箱与用户账号的绑定关系
        token = generic_email_verify_token(request.user.id)
        verify_url = 'http://127.0.0.1:8080/success_verify_email.html?token=%s' % token
        subject = '图灵商城邮箱激活邮件'  # 邮件主题
        from_email='图灵商城<【请填写自己的邮箱】>' # 发件人
        recipient_list = ['请填写收件人邮箱'] # 收件人列表
        message = None

        html_message="""
            <p>尊敬的用户：</p>
            <p>&nbsp;&nbsp;您好！</p>
            <p>&nbsp;&nbsp;感谢您使用图灵商城。</p>
            <p>&nbsp;&nbsp;您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>
            <p><a href="%s">%s</a></p>
        """ % (email, verify_url, verify_url)

        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message  # 多媒体文本
        )
        """
        为了提高用户体验，需要用celery异步发送邮件
        """
        # # 异步邮件发送
        # from celery_tasks.email.tasks import celery_send_email
        # celery_send_email.delay(
        #     subject=subject,
        #     message=message,
        #     from_email=from_email,
        #     recipient_list=recipient_list,
        #     html_message=html_message
        # )

        return JsonResponse({'code': 0, 'errmsg': 'ok'})


# 邮箱激活
class EmailVerifyView(View):
    def put(self, request):
        # 获取前端传递过来的查询字符串参数
        params = request.GET
        # 获取数据
        token = params.get('token')

        if token is None:
            return JsonResponse({'code': 400, 'errmsg':'参数不全'})

        from users.utils import check_verify_token
        user_id = check_verify_token(token)
        if user_id is None:
            return JsonResponse({'code': 400, 'errmsg': '参数异常'})

        # 查询对应数据
        user = User.objects.get(id=user_id)
        user.email_active = True
        user.save()

        return JsonResponse({'code': 0, 'errmsg': 'ok'})


# 修改密码
"""
前端：发送axios请求，修改密码
后端：
    请求：接收参数
    业务逻辑：
        接收请求，获取参数
        验证参数：完整性、原始密码正确性check_password()、新密码规范性、两次密码一致性
        设置新密码并保存 set_password()
        立即退出登录，清除session信息 logout()
        删除名为username的cookie信息 delete_cookie()
        返回响应
    响应: json
    路由: PUT password/
"""
class ChangePasswordView(LoginRequiredJsonMixin, View):
    def put(self, request):
        # 获取用户信息
        user = request.user
        # 接收请求
        json_dict = json.loads(request.body)
        # 获取参数
        old_password = json_dict.get('old_password')
        new_password = json_dict.get('new_password')
        new_password2 = json_dict.get('new_password2')
        # 验证参数
        # 验证参数的一致性
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必要参数'})
        # 验证旧密码是否正确
        if not user.check_password(old_password):
            return JsonResponse({'code': 400, 'errmsg': '输入的原始密码错误...'})
        # 验证两次输入的密码是否一致
        if new_password != new_password2:
            return JsonResponse({'code': 400, 'errmsg': '两次输入的密码不一致'})
        # 判断输入的密码格式
        if not re.match('^[0-9A-Za-z]{8,20}$',new_password):
            return JsonResponse({'code': 400, 'errmsg': '输入密码格式不正确...'})
        try:
            # 修改密码，并保存
            user.set_password(new_password)
            user.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '修改密码失败'})

        # 清除状态保持，即退出登录
        from django.contrib.auth import logout
        logout(request)

        # 清除名为username的cookie
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')
        return response



from goods.models import SKU
# 用户浏览记录
class UserBrowserHistoryView(LoginRequiredJsonMixin, View):
    # 显示浏览记录
    def get(self, request):
        redis_cli = get_redis_connection('history')
        # 获取存储的所有sku_id, <list>
        sku_ids = redis_cli.lrange('history_%s'%request.user.id, 0, -1)
        # 根据sku_ids列表数据进行查询
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'skus': skus})

    # 添加浏览记录
    def post(self, request):
        # 接收参数
        sku_id = json.loads(request.body).get('sku_id')
        # 验证参数，验证商品是否存在
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '暂无数据'})

        # 保存用户浏览数据
        redis_cli = get_redis_connection('history')
        pipeline = redis_cli.pipeline()
        user_id = request.user.id # 获取用户的id
        """
        推荐使用 有序集合，因为浏览记录是有顺序的
        这里使用的是 列表
        """
        # 去重
        pipeline.lrem('history_%s' % user_id, 0, sku_id)
        # 存储
        pipeline.lpush('history_%s' % user_id, sku_id)
        # 截取,类似切片
        pipeline.ltrim('history_%s' % user_id, 0, 4)
        # 管道执行
        pipeline.execute()

        # 返回响应结果
        return JsonResponse({'code': 0, 'errmsg':' ok'})













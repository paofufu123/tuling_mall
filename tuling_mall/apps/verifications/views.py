from django.shortcuts import render
from django.views import View
from libs.captcha.captcha import captcha  # 导入验证码
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
# Create your views here.


"""
前端
    在页面中的img标签里的src属性中并借了一个url
    url = http://127.0.0.1:8000/image_codes/uuid/
后端：
    请求：接收路由中的uuid
    业务逻辑：生成验证码内容与验证码图片，通过redis保存uuid验证码内容
    响应：返回图片
    路由：GET  image_codes/<uuid>/
    步骤：
        1.接收前端发送过来的uuid
        2.生成验证码内容与验证码图片
        3.通过redis保存uuid与验证码内容
        4.返回图片
"""
# 图形验证码
class ImageCodeView(View):
    def get(self, request, uuid):
        # 1. 生成图片验证码内容与验证码图片
        # 当前方法会返回元组 (验证码内容, 图片)
        text, image = captcha.generate_captcha()

        # 2. 存入到redis
        redis_cli = get_redis_connection('code')
        redis_cli.setex('img_%s'%uuid, 300, text)

        # 3.返回图片
        # 二进制图片类型的数据通过HttpResponse
        return HttpResponse(image, content_type='png')


"""
短信验证码发送流程
    前端：当用户输入完手机号、图片验证码之后，将发送一个axios请求
        http://127.0.0.1:8000/sms_codes/<mobile:mobile>/?image_code=xxx&image_code_id=xxxx
    后端:
        请求 > 接收请求、获取参数[手机号是路由的关键字，通过视图类中的类方法参数进行获取；用户的图片验证码与uuid在查询字符串中(request.GET.get)]
        业务逻辑 > 验证参数，验证图片验证码内容，生成短信验证码，保存短信验证码(redis)、发送短信验证码
        响应 > {'code':0, 'errmsg': 'ok'}
    开发步骤
        1. 获取请求参数
        2. 验证参数
        3. 验证图片验证码
        4. 生成短信验证码
        5. 保存短信验证码
        6. 发送短信验证码
        7. 返回响应
"""
# 短信验证码
class SMSCodeView(View):
    def get(self, request, mobile):
        # 获取请求参数
        image_code = request.GET.get('image_code')  # 图形验证码内容
        image_code_id = request.GET.get('image_code_id') # uuid

        # 验证请求参数
        # 是否齐全
        if not all([image_code, image_code_id]):
            return JsonResponse({'code': 400, 'errmsg':'参数不全'})
        # 判断图形验证码是否存在、输入正确
        redis_cli = get_redis_connection('code')
        redis_image_code = (redis_cli.get('img_%s' % image_code_id))
        if not redis_image_code:
            return JsonResponse({'code': 400, 'errmsg': '图片验证码已经过期'})
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': 400, 'errmsg': '图形验证码输入错误...'})


        '''
        创建短信验证码的状态标记位
        '''
        send_flag = redis_cli.get('send_flag_%s' % mobile)
        if send_flag: # 如果存在，就代表短信已发送，且还在时效期内
            return JsonResponse({'code': 400, 'errmsg': '不要频繁发送验证码'})
        # 如果send_flag不存在，即短信还未发送，或者短信发送了，但是时效期已过

        # 构造短信验证码内容[4位数]
        import random
        sms_code = '%04d' % random.randint(0,9999)

        # 保存短信验证码
        """
        为了减少redis连接次数，可以使用管道技术进行指令缓存，之后一起提交给redis
        """
        pipeline = redis_cli.pipeline()
        pipeline.setex(mobile, 300, sms_code)
        pipeline.setex('send_flag_%s' % mobile, 60, 1)
        pipeline.execute() # 提交管道

        # 发送短信验证码
        from libs.yuntongxun.sms import CCP
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # celery 调用任务需要使用delay方法
        # from celery_tasks.sms.tasks import celery_send_sms_code
        # celery_send_sms_code.delay(mobile,sms_code)

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})



"""
celery消息队列
    消息队列是为了解决在并发环境下消息延迟的问题
    
    手机短信和图形验证码如何完成？
        100w人同时注册
        一个人注册一个账号所发送的短信验证码 1s
        排队100w秒
    消息队列
"""
"""tuling_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,register_converter


from utils import converters # 导入自定义的路由转换器
# 注册路由转换器
register_converter(converters.UsernameConverter, 'username')
register_converter(converters.MobileConverter, 'mobile')
register_converter(converters.UUIDConverter, 'uuid')

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('log/',log), # 为日志视图配置路由
    path('', include('users.urls')),
    path('', include('verifications.urls')),
    path('', include('areas.urls')),
    path('', include('goods.urls')),
    path('', include('contents.urls')),
    path('', include('carts.urls')),
    path('', include('orders.urls')),
    path('', include('pay.urls'))
]



# from django.http import HttpResponse
#
# 日志函数
# def log(request):
#     import logging # 导入模块
#     # 创建日志器对象，获取日志器
#     logger = logging.getLogger('django')
#     # 使用日志器对象调用方法
#     logger.info('user login...')
#     logger.warning('redis error')
#     logger.error('django error')
#     # debug的等级低于info等级
#     # debug等级的信息不会被输出，因为日志器的输出等级为info
#     # 虽然写了，但是不会被记录
#     logger.debug('mix level')
#     return HttpResponse('log...')
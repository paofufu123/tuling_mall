from django.db import models

# Create your models here.

"""
用户字段需要根据页面功能去确定
    不单单是登录注册页面
    大家进入到公司之后，确定当前项目有没有用户中心
        如果用户中心中有一些字段，那么就需要注意了

根据当前页面分析得出：
    用户名
    密码
    手机号
    邮箱
    邮箱状态验证
"""


# class User(models.Model):
#     """
#     当前自定义的用户模型能否用于生产环境？
#     password是明文存储的，不能用于生产环境，因为存在安全隐患
#     需要对password进行加密：使用django内置的用户模型类
#     """
#     # 用户名是否可以重复
#     username = models.CharField(max_length=20,unique=True)
#     password = models.CharField(max_length=20)
#     mobile = models.CharField(max_length=11,unique=True)
#

# 使用系统自带的用户模型类
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    mobile = models.CharField(max_length=11,unique=True)
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    # tips: 绑定Address表，为啥得是str形式？因为代码自上而下运行，Address在User下面
    # on_delete=models.SET_NULL 表示当关联的对象被删除时，将该外键字段设置为NULL
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name


"""
如果大家使用的是django内置的用户模型类
    那么需要在settings.py中进行用户模型类的指定
    自定义的模型类会与内置模型类冲突
"""



from utils.models import BaseModel
class Address(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='绑定用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='详细地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']



"""
默认地址是否要放在地址表中，即Address模型类？
不用，原因如下：
    用户可能不会设置默认地址表
    当前地址表中的字段已经够多了
    默认地址跟用户账号有关系
综上：默认地址存放在用户表中，即User模型类中，设置为外键
    default_address = models.ForeignKey('Address')
"""
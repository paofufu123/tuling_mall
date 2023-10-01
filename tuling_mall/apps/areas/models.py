from django.db import models

# Create your models here.


# 定义收货地址表
class Area(models.Model):
    """省市区"""
    name = models.CharField(max_length=20, verbose_name='名称')
    """
    self 自己关联自己，自关联
    on_delete=models.SET_NULL  当主表被删除，那么相关联的子表的字段为null
    related_name='subs' 一对多，可以通过一查询到多，反向关联
    模型的外键，在数据库中，字段会自动加上 _id
    """
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs',
                               null=True, blank=True, verbose_name='上级行政区划')

    # 创建元信息
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = verbose_name

    # 将当前模型类中的数据返回成省市区的名称
    def __str__(self):
        return self.name

"""
查询省份信息
    Area.objects.filter(parent=None)
    Area.objects.filter(parent__isnull=True)

查询城市信息
    Area.objects.filter(parent=130000) # 查询id为130000管辖的所有城市区
    
    province = Area.objects.get(id=130000) # 查询id为130000的城市
    province.subs.all() # 查询id为130000管辖的所有城市区
"""
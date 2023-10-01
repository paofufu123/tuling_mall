from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json, re
from areas.models import Area
from users.models import Address

# Create your views here.

"""
需求：获取省份信息
前端：当页面加载时会发送一个axios请求来获取省份信息
后端：
    请求参数：无
    业务逻辑：查询省份信息
步骤：
    1. 查询省份信息
    2. 返回响应
"""
# 查询省份信息
class AreaView(View):
    def get(self, request):
        # 对省份信息进行缓存查询
        from django.core.cache import cache
        province_list = cache.get('province')

        # 如果缓存查询没有，那么就进行数据库查询
        if not province_list:
            # 查询所有省份信息
            provinces = Area.objects.filter(parent=None)
            # 将查询结果集对象转为字典
            province_list = []
            for province in provinces:
                province_list.append({
                    'id': province.id,
                    'name': province.name
                })
            # 保存缓存数据
            cache.set('province', province_list, 24*3600)
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': province_list})



# 获取城市区县信息
class SubAreaView(View):
    def get(self, request, area_id):
        # 对城市区县信息进行缓存查询
        from django.core.cache import cache
        subs = cache.get('city_%s'%area_id)
        if not subs:
            parent_model = Area.objects.get(id=area_id)  # 查询实或区的父级
            sub_list = parent_model.subs.all()  # 通过上一级行政区划查询下一级区划的所有信息

            subs = []
            for sub in sub_list:
                subs.append({
                    'id': sub.id,
                    'name': sub.name
                })
            cache.set('city_%s'%area_id, subs, 24*3600)

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data': {'subs': subs}})

"""
优化，不变的信息可以放在缓存
from django.core.cache import cache
"""



"""
创建并保存用户地址信息
前端：当用户在页面中写完信息并保存时，发送一个axios请求
后端：
    请求：接受前端发送过来的数据
    业务逻辑：
        接收数据
        验证数据
        数据入库
        返回响应 json
    响应：json
路由定义：GET /addresses/create/
"""
# 新增地址
from utils.views import LoginRequiredJsonMixin
class CreateAddressView(LoginRequiredJsonMixin, View):
    def post(self, request):
        # 接收请求
        json_dict = json.loads(request.body)
        # 获取参数
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 用户账号信息
        user = request.user

        # 验证必传参数的完整性
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必要参数'})

        # 验证手机
        if not re.match('1[3-9]\d{9}',mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机格式不正确'})

        # 验证固定电话
        if tel:
            if not re.match('^0\d{2,3}-\d{7,8}$',tel):
                return JsonResponse({'code': 400, 'errmsg': '固定电话格式有误'})

        # 验证邮箱
        if email:
            if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
                return JsonResponse({'code': 400, 'errmsg': '邮箱格式有误'})

        # 数据入库
        try:
            address = Address.objects.create(
                user=user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 当前address是objects，需要转为字典
            address_dict = dict(
                user=user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '新增地址失败, %s' % e})


# 显示地址/获取地址
class ShowAddressView(LoginRequiredJsonMixin,View):
    def get(self, request):
        # 获取用户信息
        user = request.user
        # 查询用户地址信息
        addresses = Address.objects.filter(user=user, is_deleted=False)
        address_dict_lst = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }

            # 默认地址信息
            default_address = user.default_address
            # 如果用户第一次设置地址，则默认地址为None，需要单独判断
            """
            第一次判断当前这个地址是否为第一次添加
            第二次判断是否为一个默认的，如果是，则显示小标签
            第三次判断是将不是默认地址的往后排
            """
            if default_address is None:
                address_dict_lst.append(address_dict)
            elif default_address.id == address.id:
                address_dict_lst.insert(0, address_dict)
            else:
                address_dict_lst.append(address_dict)

        # 当前这个变量使用给前端判断是否为一个默认地址，如果是，则显示小标签
        default_id = user.default_address_id
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'addresses': address_dict_lst,
            'default_address_id': default_id
        })


# 修改/删除地址
class UpdateDestroyAddressView(LoginRequiredJsonMixin, View):
    # 修改地址
    def put(self, request, area_id):
        # 接收请求
        json_dict = json.loads(request.body)
        # 获取参数
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 验证参数
        # 验证必传参数的完整性
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必要参数'})

        # 验证手机
        if not re.match('1[3-9]\d{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机格式不正确'})

        # 验证固定电话
        if tel:
            if not re.match('^0\d{2,3}-\d{7,8}$', tel):
                return JsonResponse({'code': 400, 'errmsg': '固定电话格式有误'})

        # 验证邮箱
        if email:
            if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '邮箱格式有误'})

        # 修改地址,数据入库
        try:
            Address.objects.filter(id=area_id).update(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '更新失败'})

        # 查询数据
        address = Address.objects.get(id=area_id)

        # 构造dict结构的数据
        address_dict = dict(
            id=address.id,
            title=address.receiver,
            receiver=address.receiver,
            province=address.province.name,
            city=address.province.name,
            district=address.district.name,
            place=address.place,
            mobile=address.mobile,
            tel=address.tel,
            email=address.email
        )
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})

    # 删除地址
    def delete(self, request, area_id):
        # 查询地址
        try:
            address = Address.objects.get(id=area_id)
            # 将逻辑删除is_delete的值更改为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '当前地址不存在'})
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


# 设置默认地址
class DefaultAddressView(LoginRequiredJsonMixin, View):
    def put(self, request, address_id):
        try:
            # 查询地址是否存在
            address = Address.objects.get(id=address_id)
            # 设置为默认地址
            request.user.default_address = address
            request.user.save()
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        except Exception as e:
            print('设置为默认地址失败...',e)
            return JsonResponse({'code': 400, 'errmsg': 'ok'})


# 设置地址标题
class UpdateTitleAddressView(LoginRequiredJsonMixin, View):
    def put(self, request, address_id):
        # 接收参数
        title = json.loads(request.body).get('title')
        # 查询地址
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': "地址不存在"})
        # 修改地址标题
        address.title = title
        address.save()
        # 响应数据
        return JsonResponse({'code':0, 'errmsg': 'ok'})

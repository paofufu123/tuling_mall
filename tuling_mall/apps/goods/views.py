from django.shortcuts import render

# Create your views here.

# 1. 将client配置文件放入到项目中的utils/FastDFS/目录之下
# 2. 当前代码需要在django shell中执行

# FastDFS 测试代码,只能在Django shell环境中运行
# from fdfs_client.client import Fdfs_client
#
# # 1. 创建客户端
# client = Fdfs_client('utils/FastDFS/client.conf')
#
# # 2. 上传图片
# result = client.upload_by_filename('/home/paofufu/Desktop/NewProject/img/1.jpg')
#
# # 3. 获取file_id
# print(result)
# 图片上传成功后会返回字典数据，file_id在字典中
# 当前代码在django shell中执行


from django.views import View
from utils.goods import get_categories, get_breadcrumb, get_goods_specs
from contents import models
from goods.models import GoodsCategory, SKU, GoodsVisitCount
from django.http import JsonResponse
from django.core.paginator import Paginator

# 首页商品分类与广告的渲染
class IndexView(View):
    def get(self, request):
        """
        通过视图类将页面进行渲染
        首页数据大致分为两个部分
            1. 商品分类数据
            2. 广告数据
        :param request:
        :return:
        """
        # 1. 查询商品分类数据
        categories = get_categories()

        # 2. 广告数据
        contents = {}
        content_categories = models.ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 返回页面
        context = {
            'categories': categories,
            'contents': contents
        }

        return render(request, 'index.html', context)





"""
访问http://172.26.200.150:8000/index/是没有图片显示的
Content模型类的tb_content数据表中的image字段存储的是file_id
    如：group1/M00/00/01/CtM3BVrLmc-AJdVSAAEI5Wm7zaw8639396
    要想显示图片，格式：协议://ip:port/file_id
那么我们如何在file_id前加ip:port? → 重写FastDFS的存储类Storage
步骤：
    1. 在utils下的FastDFS文件夹中新建一个名为storage.py的文件
"""

# 分类数据获取
class ListView(View):
    """
    根据用户在首页点击的分类商品按钮获取对应数据
    开发步骤
        1. 接收参数
        2. 获取分类id
        3. 根据分类id进行分类数据的查询验证
        4. 获取面包屑数据
        5. 查询分类对应的sku数据并进行排序和分页
        6. 返回响应
    """
    def get(self, request, category_id):
        """
        :param category_id: 三级菜单id
        """
        # 获取排序数据、分页数据与当前页码
        ordering = request.GET.get('ordering')
        page_size = request.GET.get('page_size')
        page = request.GET.get('page')

        try:
            # 查询数据-获取商品种类实例
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg':'参数缺失'})

        # 获取面包屑数据
        breadcrumb = get_breadcrumb(category)

        # 查询对应的sku数据并进行排序
        # 查询该商品种类的所有商品实例
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)

        # 分页
        paginator = Paginator(skus, per_page=page_size)
        # 获取第page页
        page_skus = paginator.page(page)

        # 数据结构构造
        sku_list = []
        for sku in page_skus.object_list:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        # 获取页码总数
        total_num = paginator.num_pages

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'list': sku_list,
            'count': total_num,
            'breadcrumb': breadcrumb
        })


# 热销排行
class HotGoodsView(View):
    def get(self, request, category_id):
        # 根据销量进行倒序展示
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'hot_skus': hot_skus})


"""
商品搜索功能
    使用全文检索的方式进行查询
    需要借助于搜索引擎 - ES
    根据当前用户输入的词组进行查询

    原理：将存储的数据分词，分成多个关键字和关键词组

    ElasticSearch是用 Java 实现的，开源的搜索引擎。
    它可以快速地储存、搜索和分析海量数据。维基百科、Stack Overflow、Github等都采用它。
    ElasticSearch的底层是开源库Lucene 。但是，没法直接使用 Lucene，必须自己写代码去调用它的接口。
    ElasticSearch不支持对中文进行分词建立索引，需要配合扩展elasticsearch-analysis-ik来实现中文分词处理。

    使用方式：
        1. 拉取镜像：sudo docker image pull delron/elasticsearch-ik:2.4.6-1.0
        2. 修改elasticsearch.yml配置文件中的ip地址
        3. 运行指令：
            sudo docker run -dti --name=elasticsearch --network=host -v /home/poppies/Desktop/elasticsearch-2.4.6/config:/usr/share/elasticsearch/config delron/elasticsearch-ik:2.4.6-1.0
        4. 验证服务：192.168.65.167:9200

    Haystack扩展建立索引
        1. pip install django-haystack
           pip install elasticsearch==2.4.1

        2. 注册haystack

        3. 创建配置文件
            HAYSTACK_CONNECTIONS = {
                'default': {
                    'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
                    'URL': 'http://192.168.65.167:9200/',  # Elasticsearch服务器ip地址，端口号固定为9200
                    'INDEX_NAME': 'tuling_mall',  # Elasticsearch建立的索引库的名称
                },
            }

        4. 在goods子应用之下创建search_indexes文件

        5. 数据模板文件创建
            templates/search/indexes/goods/sku_text.txt

        6. python manage.py rebuild_index
"""
from haystack.views import SearchView
# 搜索功能
class MySearchView(SearchView):
    # haystack本身实现数据搜索与数据返回
    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),  # 搜索关键字
                'page_size': context['page'].paginator.num_pages, # 总页数
                'count': context['page'].paginator.count, # 搜索结果数量
            })

        return JsonResponse(data_list, safe=False)




# 商品详情
class DetailView(View):
    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 1. 分类数据
        categories = get_categories()

        # 2. 面包屑
        breadcrumb = get_breadcrumb(sku.category)

        # 3. 规格信息
        goods_specs = get_goods_specs(sku)

        # 4.组织数据结构
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }

        # 5. 返回一个html页面
        return render(request, 'detail.html', context)


"""
目前为止：
    在我们写的所有视图文件中，只有IndexView和DetailView是返回html文件的，而且只能同过8000端口进行访问
    但是我们的前端文件却在8080端口
    那么该如何做才能同过8080端口去访问到这两个在8000端口的页面？？？
solution: 页面静态化
    将后端渲染的html页面直接写入到前端文件夹中
    然后通过前端服务器访问后端生成的html文件
    首页index.html 与 商品详情页detail.index共同点：
        查询数据库
        一般情况下，这两个页面的数据是固定的
        为了提高网站的访问速度，最快的方式是不让前端访问后端、后端访问数据库
        简单来说：前端中的数据是写死的
页面静态化：查询一次数据库，将数据全部取出来，直接将数据写死到html页面、
当用户再次访问首页时，访问的就是静态的HTML，不必访问数据库了
如果之后数据发生变动，那么就重新生成一个新的页面进行替换即可

首页index.html的数据大部分都是内容
contents是广告内容，goods是商品
这次选择将首页index.html的静态脚本写在contents子应用中,命名为crons.py
"""



# 商品访问量
"""
当用户访问到商品详情页时，会自动触发前端页面detail.js的detail_visit方法
发送了一个post请求
后端一旦接收到这个请求之后,向数据库中的统计表tb_goods_vist进行数据操作
    第一次访问  ---> 创建一个浏览器数据
    count增加
"""
class CategoryVisitCountView(View):
    def post(self, request, category_id):
        # 验证分类id
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '暂无数据'})

        # 查询当天的访问记录
        from datetime import date
        today = date.today()  # 当天时间 YYYY-mm-dd

        try:
            gvc = GoodsVisitCount.objects.get(category=category, date=today)
        except GoodsVisitCount.DoesNotExist:
            # 如果没有找到统计记录则代表第一次访问，创建统计记录
            GoodsVisitCount.objects.create(category=category, count=1, date=today)
        else:
            #如果数据存在，则更新数据
            gvc.count += 1
            gvc.save()
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


"""
用户最近浏览数据是实时更新的
写在users子应用中，因为浏览记录是用户行为
"""

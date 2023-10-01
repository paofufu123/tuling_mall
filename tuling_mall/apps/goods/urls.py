# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/8/19 8:46
@Auth: 泡芙芙的猫窝
@File: urls.py.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

from django.urls import path
from . import views


urlpatterns = [
    path('index/', views.IndexView.as_view()),
    path('list/<int:category_id>/skus/', views.ListView.as_view()),
    path('hot/<int:category_id>/', views.HotGoodsView.as_view()),
    path('search/', views.MySearchView()),
    path('detail/<int:sku_id>/', views.DetailView.as_view()),
    path('detail/visit/<int:category_id>/', views.CategoryVisitCountView.as_view()),

]

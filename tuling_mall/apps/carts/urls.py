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
    path('carts/', views.CartsView.as_view()),
    path('carts/selection/', views.CartsSelectAllView.as_view()),
    path('carts/simple/', views.CartSimpleView.as_view()),

]

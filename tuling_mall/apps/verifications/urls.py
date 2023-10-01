# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/17 11:10
@Auth: 泡芙芙的猫窝
@File: urls.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

from django.urls import path
from verifications import views

urlpatterns = [
    path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    path('sms_codes/<mobile:mobile>/', views.SMSCodeView.as_view())
]
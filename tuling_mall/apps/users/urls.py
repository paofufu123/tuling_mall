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
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/', views.MobileCountView.as_view()),
    # path('log/',log), # 为日志视图配置路由
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('info/', views.CenterView.as_view()),
    path('emails/', views.EmailView.as_view()),
    path('emails/verification/', views.EmailVerifyView.as_view()),
    path('password/', views.ChangePasswordView.as_view()),
    path('browse_histories/', views.UserBrowserHistoryView.as_view())
]

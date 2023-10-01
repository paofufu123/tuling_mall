# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/18 15:28
@Auth: 泡芙芙的猫窝
@File: views.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

class LoginRequiredJsonMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return JsonResponse({'code': 400, 'errmsg': '账号未登录'})
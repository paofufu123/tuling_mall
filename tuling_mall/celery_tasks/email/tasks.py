# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/18 18:55
@Auth: 泡芙芙的猫窝
@File: tasks.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""
from django.core.mail import send_mail
from celery_tasks.main import app

@app.task
def celery_send_email(subject, message, from_email, recipient_list, html_message):
    try:
        print('调用邮件发送函数')
        send_mail(
            subject=subject,  # 邮件主题
            message=message,
            from_email=from_email,  # 发件人
            recipient_list=recipient_list,  # 收件人列表
            # 多媒体文本
            html_message=html_message
        )
        print('邮箱发送成功')
    except Exception as e:
        print(f'异步邮箱fail...{e}',)

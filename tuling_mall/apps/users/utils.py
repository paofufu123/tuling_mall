# -*- coding: utf-8 -*-
"""
______________________________
@Time: 2023/9/18 18:47
@Auth: 泡芙芙的猫窝
@File: utils.py
@IDE: PyCharm
@moto: (>^ω^<)喵~
______________________________
"""

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tuling_mall.settings import SECRET_KEY

# 对邮件验证链接的token值，即user id进行加密
def generic_email_verify_token(user_id):
    # 创建一个加密类实例, 根据Django的密钥进行加密，时效性一天
    serializer = Serializer(secret_key=SECRET_KEY, expires_in=3600*24)
    # 加密数据 <bytes>
    data = serializer.dumps({'user_id': user_id})
    # 返回加密数据 <str>
    return data.decode()


# 解密
def check_verify_token(token):
    # 创建一个加密类实例, 根据Django的密钥进行加密，时效性一天
    serializer = Serializer(secret_key=SECRET_KEY, expires_in=3600 * 24)
    # 解密操作，在解密时很可能出现失败情况
    try:
        result = serializer.loads(token)
    except:
        return None
    return result.get('user_id')
# 自定义一个过滤器，定义点击排行前三的样式
import functools
from flask import session,g

from info.models import User


def index_class(index):

    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


def user_login_data(f):
    """ 判断用户是否登陆"""
    # 从session中获取用户的id
    @functools.wraps(f)
    def wapper(*args,**kwargs):
        user_id = session.get("user_id")
        user = None

        # 获取用户信息
        if user_id:
            user = User.query.get(user_id)
        g.user = user
        return f(*args,**kwargs)
    return wapper

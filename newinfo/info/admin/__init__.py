from flask import Blueprint
from flask import redirect
from flask import request
from flask import session

admin_blue = Blueprint("admin",__name__,url_prefix="/admin")


from . import views

# 在跳转到管理员登陆界面之前先要判断该账号是否为管理员
@admin_blue.before_request
def check_admin():
    is_admin = session.get("is_admin",None)

    if not is_admin and not request.url.endswith("/admin/login"):
        return redirect("/")
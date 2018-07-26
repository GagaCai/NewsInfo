import random
from datetime import datetime

from flask import session

from info import constants, db
from info import redis_store
from flask import make_response, jsonify
from flask import request

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import  captcha
from info.utils.response_code import RET
import re

from . import passport_blue

@passport_blue.route("/logout")
def logout():
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin", None)

    return jsonify(errno = RET.OK,errmsg = "退出成功")

"""

    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:

"""

@passport_blue.route("/login",methods = ["POST"])
def login():
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    user = User.query.filter(User.mobile == mobile).first()

    if not user:
        return jsonify(errno = RET.DATAERR,errmsg = "请先注册")

    if not user.check_password(password):
        return jsonify(errno = RET.PARAMERR,errmsg = "密码输入有误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin

    user.last_login = datetime.now()
    db.session.commit()

    print("登陆成功")
    return jsonify(errno = RET.OK,errmsg = "登陆成功")


"""

    1. 获取参数和判断是否有值
    2. 从redis中获取指定手机号对应的短信验证码的
    3. 校验验证码
    4. 初始化 user 模型，并设置数据并添加到数据库
    5. 保存当前用户的状态
    6. 返回注册的结果
    :return:

"""


@passport_blue.route("/register",methods=["POST"])
def register():
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password = request.json.get("password")

    if not all([mobile,smscode,password]):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入内容")

    sms_code = redis_store.get("sms_code" + mobile)
    print(sms_code)
    if not sms_code:
        return jsonify(errno = RET.DATAERR,errmsg = "验证码已过期")

    if sms_code != smscode:
        return jsonify(errno = RET.PARAMERR,errmsg = "验证码输入错误")

    user = User()
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile
    user.last_login = datetime.now()

    db.session.add(user)
    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "注册成功")


"""
发送短信验证码实现流程：
    接收前端发送过来的请求参数
    检查参数是否已经全部传过来
    判断手机号格式是否正确
    检查图片验证码是否正确，若不正确，则返回
    删除图片验证码
    生成随机的短信验证码
    使用第三方SDK发送短信验证码

"""


@passport_blue.route("/sms_code",methods = ["POST"])
def sms_code():
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")

    # 验证内容是否填写完整
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入正确的信息")
    # 验证手机号是否填写正确
    if not re.match(r"1[356789]\d{9}",mobile):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入正确的手机号")
    # 获取数据库中的验证码
    real_image_code = redis_store.get("image_code_" + image_code_id)
    if not real_image_code:
        return jsonify(errno = RET.DATAERR,errmsg = "验证码已过期")
    # 获取数据库中的验证码与填写的验证码是否一致
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入正确的验证码")

    result = random.randint(0,999999)
    sms_code = "%06d"%result
    print(sms_code)

    redis_store.set("sms_code"+mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    # 发送短信
    # 第一个参数表示手机号
    # 第二个参数表示[],左边的参数表示短信验证码，右边的参数表示多少分钟之后过期
    # 第三个参数表示模板id,固定的写法是１
    # statusCode = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # if statusCode != 0:
    #     return jsonify(errno = RET.THIRDERR,errmsg = "短信发送失败")

    return jsonify(errno = RET.OK,errmsg = "发送成功")


"""实现图片验证码功能"""


@passport_blue.route("/image_code")
def get_code_id():
    # 根据接口文档的规则获取每一个客户端的验证码的图片id
    code_id = request.args.get("code_id")
    # 通过验证码的函数生成随机图片验证码
    name, text, image = captcha.generate_captcha()
    # 将验证码保存在redis数据库中5分钟
    redis_store.set("image_code_"+code_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    # 对客户端做出响应
    resp = make_response(image)
    # 由于是GET请求，设置响应头的数据类型为传递图片数据类型
    resp.headers["Content-Type"] = "image/jpg"

    return resp


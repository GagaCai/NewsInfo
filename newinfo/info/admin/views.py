from datetime import datetime,timedelta
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import constants
from info import db
from info.models import User, News, Category
import time

from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from info.utils.common import user_login_data


@admin_blue.route("/add_category",methods = ["POST"])
def add_category():
    cid = request.json.get("id")
    name = request.json.get("name")

    if cid:
        category = Category.query.get(cid)
        category.name = name
    else:
        category = Category()
        category.name = name
        db.session.add(category)

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "ok")


@admin_blue.route("/news_type")
def news_type():
    categorys = Category.query.all()

    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())

    category_list.pop(0)
    data = {
        "categories":category_list
    }

    return render_template("admin/news_type.html", data = data)


@admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
def news_edit_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        categorys = Category.query.all()

        category_list = []
        for category in categorys:
            category_list.append(category.to_dict())

        category_list.pop(0)

        data = {
            "news": news.to_dict(),
            "categories":category_list
        }

        return render_template("admin/news_edit_detail.html", data = data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image").read()
    content = request.form.get("content")

    if not all([title,category_id,digest,content]):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入修改内容")

    key = storage(index_image)
    news = News.query.get(news_id)
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.content = content

    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "ok")


# @admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
# def news_edit_detail():
#     if request.method == "GET":
#         news_id = request.args.get("news_id")
#         news = News.query.get(news_id)
#         categorys =  Category.query.all()
#
#         category_list = []
#         for category in categorys:
#             category_list.append(category.to_dict())
#
#         category_list.pop(0)
#         data = {
#             "news":news.to_dict(),
#             "categories":category_list
#         }
#         return render_template("admin/news_edit_detail.html",data = data)
#
#     news_id = request.form.get("news_id")
#     print(news_id)
#     print(type(news_id))
#
#     title = request.form.get("title")
#     digest = request.form.get("digest")
#     content = request.form.get("content")
#     index_image = request.files.get("index_image").read()
#     category_id = request.form.get("category_id")
#     # 1.1 判断数据是否有值
#     if not all([title, digest, content, category_id]):
#         return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
#
#     key = storage(index_image)
#     news  = News.query.get(news_id)
#     news.title = title
#     news.category_id = category_id
#     news.digest = digest
#     news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
#     news.content = content
#     db.session.commit()
#     return jsonify(errno = RET.OK,errmsg = "ok")


@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p",1)
    keywords = request.args.get("keywords","")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    filters = []
    if keywords:
        filters.append(News.title.contains(keywords))
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,10,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    new_list = []
    for item in items:
        new_list.append(item.to_review_dict())

    data = {
        "news_list":new_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("admin/news_edit.html", data = data)


@admin_blue.route("/news_review_detail",methods = ["GET","POST"])
def news_review_detail():
    news_id = request.args.get("news_id")


    if request.method == "GET":
        news = News.query.get(news_id)
        data = {
            "news":news.to_dict()
        }

        return render_template("admin/news_review_detail.html", data = data)


    news_id = request.json.get("news_id")
    action = request.json.get("action")
    news = News.query.get(news_id)


    if action == "accept":
        news.status = 0
    else:
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno = RET.PARAMERR,errmsg = "请输入拒绝的原因")

        news.status = -1
        news.reason = reason

    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "ok")


@admin_blue.route("/news_review")
def news_review():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords","")
    try:
        page = int(page)
    except Exception as e:
        page = 1

    news = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,9,False)
    items = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_list = []
    for new in items:
        news_list.append(new.to_review_dict())

    data = {
        "news_list":news_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("admin/news_review.html", data = data)


@admin_blue.route("/user_list")
def user_list():
    page = request.args.get("p",1)

    try:
        page = int(page)
    except Exception as e:
        page = 1

    users = []
    current_page = 1
    total_page = 1

    paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,5,False)

    items = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    user_list = []
    for item in items:
        user_list.append(item.to_admin_dict())

    data = {
        "users":user_list,
        "current_page":current_page,
        "total_page":total_page

    }

    return render_template("admin/user_list.html", data = data)


@admin_blue.route("/user_count")
def user_count():
    # 总人数
    total_count = 0
    # 每个月新增人数
    mon_count = 0
    # 每天新增人数
    day_count = 0

    # 获取到所有的人数,剔除小编,因为小编是员工,不是用户
    total_count = User.query.filter(User.is_admin == False).count()

    # 获取到当前的时间
    t = time.localtime()
    # 2018-07-01
    mon_time = "%d-%02d-01"%(t.tm_year,t.tm_mon)
    # 2018-07-01 00:00:00
    mon_time_begin = datetime.strptime(mon_time,"%Y-%m-%d")
    mon_count = User.query.filter(User.is_admin == False,User.create_time > mon_time_begin).count()

    # 2018-07-11
    day_time = "%d-%02d-%02d" % (t.tm_year, t.tm_mon,t.tm_mday)
    # 2018-07-01 00:00:00
    day_time_begin = datetime.strptime(day_time, "%Y-%m-%d")
    day_count = User.query.filter(User.is_admin == False, User.create_time > day_time_begin).count()

    # 2018-07-11
    today_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    # 2018-07-01 00:00:00
    today_begin_date = datetime.strptime(day_time, "%Y-%m-%d")
    active_count = []
    active_time = []
    for i in range(0,30):
       begin_date =  today_begin_date - timedelta(days=i)
       end_date =  today_begin_date - timedelta(days=(i - 1))
       # 30天的总人数
       count = User.query.filter(User.is_admin == False, User.create_time > begin_date,User.create_time < end_date).count()
       active_count.append(count)
       active_time.append(begin_date.strftime("%Y-%m-%d"))
    """
    需求:
    统计,这一个月每天新增用户量,往前面推30天

    """

    active_count.reverse()
    active_time.reverse()
    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_time":active_time,
        "active_count":active_count
    }
    return render_template("admin/user_count.html", data = data)


@admin_blue.route("/logout")
def logout():
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin", None)

    return jsonify(errno = RET.OK,errmsg = "退出成功")

    # return redirect("admin.login.html")

@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user
    return render_template("admin/index.html", user = user.to_dict())


@admin_blue.route("/login",methods = ["GET","POST"])
def admin_login():
    if request.method == "GET":
        user_id = session.get("user_id",None)
        is_admin = session.get("is_admin",None)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        return render_template("admin/login.html")
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter(User.mobile == username,User.is_admin == True).first()

    if not all([username,password]):
        return render_template("admin/login.html", errmsg="请输入账号密码")
    if not user:
        return render_template("admin/login.html", errmsg ="没有此用户")
    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.admin_index"))



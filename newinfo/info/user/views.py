from flask import render_template,g, jsonify
from flask import request
from info import db
from info.models import News, Category, User
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from info import constants

from . import profile_blue


# @profile_blue.route("/other_news_list")
# def other_news_list():
#     page = request.args.get("p",1)
#
#     try:
#         page = int(page)
#     except Exception as e:
#         page = 1
#
#     user_id = request.args.get("user_id")
#     paginate = News.query.filter(News.user_id == user_id).paginate(page,7,False)
#     items = paginate.items
#     current_page = paginate.page
#     total_page = paginate.pages
#
#     news_list = []
#     for item in items:
#         news_list.append(item.to_review_dict())
#
#     data = {
#         "news_list":news_list,
#         "current_page":current_page,
#         "total_page":total_page
#     }
#
#     return render_template("news/other.html",data = data)



@profile_blue.route("/other_info")
@user_login_data
def other_info():
    user = g.user
    user_id = request.args.get("id")
    print(user_id)
    other = User.query.get(user_id)
    # 页面显示实现
    page = request.args.get("p", 1)
    print(page)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = News.query.filter(News.user_id == user_id).paginate(page, 3, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    is_followed = False
    if other and user:
        if other in user.followed:
            is_followed = True

    data = {
        "user_info": user.to_dict() if user else None,
        "other_info":other.to_dict(),
        "is_followed": is_followed,
        "news_list":news_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("news/other.html",data = data)


@profile_blue.route("/user_follow")
@user_login_data
def user_follow():
    user = g.user
    page = request.args.get("p",1)

    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = user.followed.paginate(page,4,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    followed_list = []
    for item in items:
        followed_list.append(item.to_dict())

    data = {
        "users":followed_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("news/user_follow.html",data = data)


@profile_blue.route("/news_list")
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = News.query.filter(News.user_id == user.id).paginate(page,5,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []
    for new in items:
        news_list.append(new.to_review_dict())

    data = {
        "news_list":news_list,
        "current_page":current_page,
        "total_page":total_page

    }

    return render_template("news/user_news_list.html",data = data)


@profile_blue.route("/news_release",methods = ["GET","POST"])
@user_login_data
def news_release():
    user = g.user
    if request.method == "GET":
        categorys =  Category.query.all()
        category_list = []
        for category in categorys:
            category_list.append(category.to_dict())
        category_list.pop(0)
        data = {
            "categories":category_list
        }
        return render_template("news/user_news_release.html",data = data)

    title = request.form.get("title")
    source = "个人发布"
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image").read()
    content = request.form.get("content")

    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")

    key = storage(index_image)
    news = News()
    news.title = title
    news.source = source
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = user.id
    news.status = 1

    db.session.add(news)
    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "ok")





@profile_blue.route("/collection")
@user_login_data
def collection():
    user = g.user
    page = request.args.get("p",1)

    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = user.collection_news.paginate(page,5,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    collection_list = []
    for collection in items:
        collection_list.append(collection.to_review_dict())

    data = {
            "collections": collection_list,
            "current_page":current_page ,
            "total_page":total_page

    }

    return render_template("news/user_collection.html",data = data)


@profile_blue.route("/pass_info",methods = ["GET","POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not user.check_password(old_password):
        return jsonify(errno = RET.PWDERR,errmsg = "密码不正确")
    user.password = new_password
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="修改成功")


@profile_blue.route("/pic_info",methods = ["GET","POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info":user.to_dict() if user else None
        }
        return render_template("news/user_pic_info.html",data = data)
    avatar = request.files.get("avatar").read()
    key = storage(avatar)
    user.avatar_url = key
    db.session.commit()

    data = {
        "avatar_url" : constants.QINIU_DOMIN_PREFIX + key
    }

    return jsonify(errno=RET.OK, errmsg="修改成功",data = data)

@profile_blue.route("/base_info",methods = ["GET","POST"])
@user_login_data
def base_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info":user.to_dict() if user else None
        }
        return render_template("news/user_base_info.html",data = data)

    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "修改成功")


@profile_blue.route("/info")
@user_login_data
def get_user_info():
    user = g.user
    data = {
        "user_info":user.to_dict() if user else None

    }
    return render_template("news/user.html",data = data)
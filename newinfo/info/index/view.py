from flask import Flask,render_template,current_app, jsonify
from flask import request,g
from flask import session
from info.utils.common import user_login_data
from info.models import User, News,Category
from info.utils.response_code import RET
from . import index_blue


"""实现新闻列表数据"""
@index_blue.route("/news_list")
def news_list():
    """
        获取指定分类的新闻列表
        1. 获取参数
        2. 校验参数
        3. 查询数据
        4. 返回数据
        :return:
    """
    # 获取新闻编号
    cid = request.args.get("cid",1)
    page = request.args.get("page",1)
    per_page = request.args.get("per_page",10)

    # 校验前段传来的数据是否正确
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.erro(e)
        cid = 1
        page = 1
        per_page = 10

    filter = [News.status == 0]
    if cid != 1:
        filter.append(News.category_id == cid)
    paginate_page = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page, per_page, False)
    # paginate_page = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page,per_page,False)

    items = paginate_page.items
    total_page = paginate_page.pages
    current_page = paginate_page.pages

    news_list = []
    for item in items:
        news_list.append(item.to_dict())

    data = {
        "news_dict_li": news_list,
        "total_page":total_page,
        "current_page":current_page

    }

    return jsonify(errno = RET.OK,errmsg = "ok",data = data)


@index_blue.route("/favicon.ico")
def get_favicon():
    return current_app.send_static_file("news/favicon.ico")
    # return current_app.send_static_file("news/favicon.ico")

@index_blue.route("/")
@user_login_data
def index():
    user = g.user
    """ 判断用户是否登陆"""
    # 从session中获取用户的id
    # user_id = session.get("user_id")
    # user = None
    #
    # # 获取用户信息
    # if user_id:
    #     user = User.query.get(user_id)

    """ 实现点击排行模块功能"""
    news_list = []
    news = News.query.order_by(News.create_time.desc()).limit(10)

    for new in news:
        news_list.append(new.to_dict())

    """实现首页头部新闻种类"""
    # 1、实现最新选项功能
    categorys = Category.query.all()
    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())


    data = {
        "user_info":user.to_dict() if user else None,
        "click_news_list":news_list,
        "categories":category_list
    }
    return render_template("news/index.html",data = data)
from flask import request, jsonify
from flask import session

from info import db
from info.models import User, News, Comment, CommentLike
from info.utils.response_code import RET
from . import news_blue
from flask import render_template,g
from info.utils.common import user_login_data

@news_blue.route("/followed_user",methods = ["POST"])
@user_login_data
def followed_user():
    user = g.user
    user_id = request.json.get("user_id")
    action = request.json.get("action")
    print(user_id)
    print(action)
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "用户未登陆")
    other = User.query.get(user_id)
    if action == "follow":
        if other in user.followed:
            return jsonify(errno = RET.NODATA,errmsg = "已关注")
        else:
            user.followed.append(other)
    else:
        if other in user.followed:
            print(user.followed.count())
            user.followed.remove(other)
        else:
            return jsonify(errno = RET.NODATA,errmsg = "没有关注")
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "ok")


# 后台评论点赞功能的实现
"""
   后端提供点赞和取消点赞功能
   当用户点击未点赞按钮，执行点赞逻辑，向后端发起点赞请求，取消点赞则反之
   在新闻显示完成之后，底部评论会根据当前登录用户显示是否点赞图标
"""
@news_blue.route("/comment_like",methods = ["POST"])
@user_login_data
def comment_like():
    user = g.user
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    comment = Comment.query.get(comment_id)

    if not user:
        return jsonify(errno = RET.SESSIONERR,erromsg = "请登陆")

    # 查询该评论是否点赞
    comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id, CommentLike.user_id == user.id).first()

    # 判断用户鼠标点击事件
    if action == "add":
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            db.session.add(comment_like)
            comment.like_count += 1
    else:
        db.session.delete(comment_like)
        comment.like_count -= 1

    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "点赞成功")


# 获取用户新闻评论并将评论存储至数据库中
@news_blue.route("/news_comment",methods = ["POST"])
@user_login_data
def news_comment():
    user = g.user
    news_id = request.json.get("news_id")
    comment_str = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "用户未登陆")

    news = News.query.get(news_id)
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str

    if parent_id:
        comment.parent_id = parent_id

    db.session.add(comment)
    db.session.commit()

    # data = comment.to_dict()


    return jsonify(errno = RET.OK,errmsg = "评论成功" ,data = comment.to_dict())


# 新闻后台接口实现
@news_blue.route("/news_collect",methods = ["POST"])
@user_login_data
def news_collect():
    user = g.user
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    news = News.query.get(news_id)
    if not user:
        return jsonify(errno = RET.SERVERERR,errmsg = "用户未登录")


    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "搜藏成功")


@news_blue.route("/<int:new_id>")
@user_login_data
def news_detail(new_id):
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
    news = News.query.order_by(News.clicks.desc()).limit(10)

    for new in news:
        news_list.append(new.to_dict())

    """获取新闻详情"""
    new_data = News.query.get(new_id)

    """
    新闻搜藏功能实现：
        前端根据后台返回数据显示收藏或者取消收藏按钮
        后端提供收藏与取消收藏接口
        前端发起收藏或者取消收藏请求
    """
    is_collected = False

    if user:
        if new_data in user.collection_news:
            is_collected = True
    print(is_collected)


    """关注的实现"""
    # 1,用户登陆才能关注，新闻需要有作者
    is_followed = False
    if user:
        if new_data.user and new_data.user in user.followed:
            is_followed = True
    print("关注成功")

    """
    在新闻详情页中显示评论数据:
    1、根据新闻id获取新闻评论

    """
    comments = Comment.query.filter(Comment.news_id == new_id).order_by(Comment.create_time.desc()).all()
    comment_list = []

    # 获取点赞数据，从而在前端显示
    commentLike_list = []
    comment_like_ids = []
    if user:
        commentLike_list = CommentLike.query.filter(CommentLike.user_id == user.id).all()
        comment_like_ids = [comment_like.comment_id for comment_like in commentLike_list]
    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment_dict )


    data = {
        "user_info":user.to_dict() if user else None,
        "click_news_list":news_list,
        "is_collected":is_collected,
        "news":new_data.to_dict(),
        "comments":comment_list,
        "is_followed":is_followed
    }
    return render_template("news/detail.html",data = data)
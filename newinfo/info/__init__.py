import logging
from logging.handlers import RotatingFileHandler
import redis
from flask import Flask
from flask import g
from flask import render_template
from flask_wtf.csrf import CSRFProtect,generate_csrf
from flask_session import Session
from  flask_sqlalchemy import SQLAlchemy
from config import config_map


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


# 初始化数据库的第二种方式
db = SQLAlchemy()

redis_store = None


def create_app(config_name):
    app = Flask(__name__)

    config_class = config_map.get(config_name)

    # 添加配置
    app.config.from_object(config_class)
    # 初始化数据库
    # db = SQLAlchemy(app)
    db.init_app(app)
    # 初始化redis

    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST,port=config_class.REDIS_PORT,decode_responses=True)
    # 初始化session
    Session(app)

    from info.utils.common import index_class
    app.add_template_filter(index_class,"indexClass")
    # 设置CSRF防御，避免CSRF攻击
    CSRFProtect(app)

    @app.after_request
    def after_request(response):
        csrf_token = generate_csrf()

        response.set_cookie("csrf_token",csrf_token)
        return response

    from info.utils.common import user_login_data
    # 404全局页面
    @app.errorhandler(404)
    @user_login_data
    def erro_404_handler(erro):
        user = g.user
        data = {
            "user_info":user.to_dict() if user else None
        }
        return render_template("news/404.html",data = data)

    # 首页蓝图
    from info.index import index_blue
    app.register_blueprint(index_blue)
    # 注册登陆蓝图
    from info.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 新闻详情蓝图
    from info.news import news_blue
    app.register_blueprint(news_blue)

    #个人中心蓝图
    from info.user import profile_blue
    app.register_blueprint(profile_blue)

    # 管理员蓝图注册
    from info.admin import admin_blue
    app.register_blueprint(admin_blue)


    return app



import redis


class Config(object):
    SECRET_KEY = "sjfdkalglgr"

    # 建立数据库连接
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 设置session的配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    # 设置session数据保留时间
    PERMANENT_SESSION_LIFETIME = 86400 * 3

# 开发测试阶段的配置
class DevelopmentConfig(Config):
    DEBUG = True

# 上线后的配置
class ProductionConfig(Config):
    DEBUG = False

config_map = {
    "develop":DevelopmentConfig,
    "product":ProductionConfig
}
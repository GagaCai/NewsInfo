from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from info import create_app,db
from info import models


# 动态传值
from info.models import User

app = create_app("develop")
manager = Manager(app)
Migrate(app,db)
manager.add_command("mysql",MigrateCommand)


@manager.option('-n','--name',dest = 'name')
@manager.option("-p","--password",dest = "password")
def creat_super_user(name,password):
    user = User()
    user.nick_name = name
    user.password = password
    user.mobile = name
    user.is_admin = True

    db.session.add(user)
    db.session.commit()





if __name__ == '__main__':
    # app.run(host='192.168.54.128' ,port = 8800)
    manager.run()
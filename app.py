import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
import os
from extensions import db, celery, init_celery
from models import db
from flask_cors import CORS
from user import user_bp
from event import event_bp
from auth import auth_bp
from tasks_manager import tasks_bp
from message import msg_bp
from services import redis_client
from cache import cache
load_dotenv()


def create_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"], "allow_headers": "*"}
    })
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CELERY_BROKER_URL'] = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"
    app.config['CELERY_RESULT_BACKEND'] = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"

    db.init_app(app)
    init_celery(app)  # 初始化 celery
    Migrate(app, db)
    redis_client.init_app(app)

    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(msg_bp)

    cache.set('config', {
        'site_name': '管理系统',
        'version': '1.0.0'
    })

    # 设置日志
    if not os.path.exists('logs'):
        os.makedirs('logs')  # 如果 logs 文件夹不存在，则创建它

    handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.ERROR)  # 设置日志级别
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)

    return app



# 创建 Flask 应用
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

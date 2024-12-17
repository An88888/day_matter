# app.py

import logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
import os
from crontab import crontab_bp
from extensions import init_celery
from interval import interval_bp
from models import db
from flask_cors import CORS
from user import user_bp
from event import event_bp
from auth import auth_bp
from tasks_manager import tasks_bp
from message import msg_bp
from image import image_bp
from food import food_bp
from cate import cate_bp
from ingredient import ingredient_bp
from scrape import scrape_bp
from services import redis_client
from cache import cache
from message import msg_send_all


def create_app():
    load_dotenv()
    app = Flask(__name__)
    # 创建一个 BackgroundScheduler 实例
    scheduler = BackgroundScheduler()
    CORS(app, resources={
        r"/*": {"origins": [
            # "http://127.0.0.1:51740",
            # "http://121.204.220.53:51740"
            "*"
        ],
                "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"], "allow_headers": "*"}
    })
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure Redis connection
    redis_host = os.getenv('REDIS_HOST', '172.18.0.3')
    redis_port = os.getenv('REDIS_PORT', 6379)
    redis_password = os.getenv('REDIS_PASSWORD', 'redis_DbhdZH')
    app.config['REDIS_URL'] = f'redis://:{redis_password}@{redis_host}:{redis_port}/0'

    # app.config['CELERY_BROKER_URL'] = f'redis://{redis_password}@{redis_host}:{redis_port}/0'
    # app.config['CELERY_RESULT_BACKEND'] = f'redis://{redis_password}@{redis_host}:{redis_port}/0'

    db.init_app(app)
    # celery= init_celery(app)  # 初始化 celery
    Migrate(app, db)
    redis_client.init_app(app)

    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(msg_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(food_bp)
    app.register_blueprint(cate_bp)
    app.register_blueprint(ingredient_bp)
    app.register_blueprint(scrape_bp)
    app.register_blueprint(crontab_bp)
    app.register_blueprint(interval_bp)

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

    # 定义定时任务，每天下午5点半执行
    def scheduled_task():
        with app.app_context():
            msg_send_all()

    scheduler.add_job(scheduled_task, 'cron', hour=18, minute=00)
    # 启动调度器
    scheduler.start()

    return app



# 创建 Flask 应用
app = create_app()
BASE_DIR = app.root_path


if __name__ == '__main__':
    app.run(debug=False)


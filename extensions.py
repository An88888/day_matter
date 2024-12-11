from flask import Flask
from celery import Celery, Task
from flask_sqlalchemy import SQLAlchemy
import os
import logging

# 初始化共享实例
db = SQLAlchemy()

# 获取当前文件所在目录的父目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建 Celery 实例时明确指定 broker 类型
celery = Celery('app',
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),  # 明确指定 Redis
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    broker_connection_retry_on_startup=True  # 添加重试选项
)

# 设置 Celery 默认配置
celery.conf.update(
    broker_transport_options={'visibility_timeout': 3600},  # Redis 特定配置
    task_serializer='json',
    accept_content=['json'],  # 限制接受的内容类型
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    imports=['tasks'],
    include=['tasks'],
    task_autodiscover_packages=['tasks']
)

# 配置日志
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

beat_log_file = os.path.join(log_dir, 'celery_beat.log')  # 直接在logs目录下创建celery_beat.log文件

beat_handler = logging.FileHandler(beat_log_file)
beat_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

beat_logger = logging.getLogger('celery.beat')
beat_logger.addHandler(beat_handler)
beat_logger.setLevel(logging.INFO)


def init_celery(app: Flask):
    # 使用 Flask 配置更新 Celery 配置
    celery.conf.update(
        broker_url=os.getenv('REDIS_URL'),
        result_backend=os.getenv('REDIS_URL')
    )
    app.logger.info(f"Celery broker URL: {celery.conf.broker_url}")

    class ContextTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
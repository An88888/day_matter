from flask import Flask
from celery import Celery, Task
from flask_sqlalchemy import SQLAlchemy
import os

# 初始化共享实例
db = SQLAlchemy()

# 获取当前文件所在目录的父目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建 Celery 实例时明确指定 broker 类型
celery = Celery('app',
    broker_url='redis://localhost:6379/0',  # 明确指定 Redis
    result_backend='redis://localhost:6379/0',
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

def init_celery(app: Flask):
    # 使用 Flask 配置更新 Celery 配置
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )

    class ContextTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    
    # 手动导入任务模块
    import tasks
    
    return celery
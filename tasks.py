from datetime import datetime

from extensions import celery
import logging
from models import User, Event
from sms import send_message
logger = logging.getLogger(__name__)  # 获取当前模块的 logger

@celery.task(name='tasks.execute_task')
def tack_check():
    logger.error("========execute_task_start")


@celery.task(name='tasks.execute_task')
def execute_task():
    logger.error("========execute_task_start")

    # 获取当前所有用户
    users = User.query.all()

    for user in users:
        # 获取当前用户绑定的所有事件
        events = Event.query.filter_by(user_id=user.id).all()  # 根据用户ID过滤事件

        if events:
            # 汇总事件信息
            event_summary = []

            for event in events:
                # 计算距离目标日期还有多少天
                days_until_target = (event.target_date - datetime.today().date()).days
                event_summary.append(f"- {event.name}: 还有 {days_until_target} 天到期")

            # 将事件摘要列表转换为字符串
            event_summary_str = "\n".join(event_summary)

            # 发送信息给用户
            send_message(user, event_summary_str)

    logger.error("========execute_task_end")

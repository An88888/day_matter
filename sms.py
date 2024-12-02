# sms.py
import requests
import logging
logger = logging.getLogger(__name__)  # 获取当前模块的 logger


def send_message(user,message, title="Daily Events"):
    url = "https://api.day.app/push"
    payload = {
        "body": message,
        "title": title,
        "device_key": user
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        pass
    else:
        logger.error("======send_error")
        logger.error(response)

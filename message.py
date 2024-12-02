from flask import Blueprint, request
import constants
from decorators import login_required, response_format, admin_required
from models import User
from sms import send_message

import logging

msg_bp = Blueprint('msg', __name__)
logger = logging.getLogger(__name__)  # 获取当前模块的 logger


# 创建或更新任务
@msg_bp.route('/msg/send', methods=['POST'])
@login_required
@admin_required
@response_format
def msg_send():
    try:
        data = request.get_json()
        message = data.get('content')
        user_id = data.get('user_id')
        user_info = User.query.get(user_id)
        if user_info:
            pass
        else:
            return {"code": constants.RESULT_FAIL, "message": "用户不存在"}
        user = user_info.device_key
        send_message(user,message)
        return {"code": constants.RESULT_SUCCESS}

    except Exception as e:
        return {"code": constants.RESULT_FAIL, "message": str(e)}

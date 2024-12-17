# auth.py
import hashlib
import time
from flask import Blueprint, request, session
import constants
from decorators import response_format
from models import User
from services import redis_client
from cache import cache
import uuid
from urllib.parse import quote
import os

auth_bp = Blueprint('auth', __name__)


# 用户登录
@auth_bp.route('/login', methods=['POST'])
@response_format
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = User.query.filter_by(username=username, password=hashed_password).first()

    if user is None:
        return {"code": constants.RESULT_FAIL, "message": "用户名或密码错误"}

    token = generate_user_token(user)

    return {
        "code": constants.RESULT_SUCCESS,
        "data": {
            "token": token,
            "user": {"id": user.id, "username": user.username, "isAdmin": user.is_admin},
        }
    }


@auth_bp.route('/qrcode_login', methods=['POST'])
@response_format
def check_qrcode_login_status():
    data = request.get_json()
    login_token = data.get('login_token')
    user_id = redis_client.get(f"qrcode_login:{login_token}")

    if user_id:
        user_id = user_id.decode()  # 将字节串转换为字符串
        if user_id == "pending":
            return {"code": constants.RESULT_SUCCESS, "data": {"status": "waiting"}}
        else:
            user = User.query.get(user_id)
            if user:
                token = generate_user_token(user)
                redis_client.delete(f"qrcode_login:{login_token}")  # 登录成功后删除 Redis 中的登录状态
                return {"code": constants.RESULT_SUCCESS, "data": {"status": "success", "token": token}}

    return {"code": constants.RESULT_FAIL, "message": "无效的请求或登录会话已过期"}


@auth_bp.route('/qrcode_confirm_login', methods=['POST'])
@response_format
def confirm_qrcode_login():
    data = request.get_json()
    login_token = data.get('login_token')
    user_id = data.get('user_id')

    # 检查登录 token 是否有效
    stored_user_id = redis_client.get(f"qrcode_login:{login_token}")
    if stored_user_id and stored_user_id.decode() == "pending":
        # 更新 Redis 中的登录状态为已确认的用户 ID
        redis_client.setex(f"qrcode_login:{login_token}", 300, user_id)
        return {"code": constants.RESULT_SUCCESS, "message": "登录确认成功"}
    else:
        return {"code": constants.RESULT_FAIL, "message": "无效的请求或登录会话已过期"}


@auth_bp.route('/logout', methods=['POST'])
@response_format
def logout():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return {"code": constants.RESULT_FAIL, "message": "未提供 token"}

    redis_client.delete(token)

    user_id = token.split(":")[-1]
    cache.delete(str(user_id))

    return {
        "code": constants.RESULT_SUCCESS,
        "message": "登出成功"
    }


@auth_bp.route('/qrcode_login_url', methods=['GET'])
@response_format
def get_qrcode_login_url():
    app_id = os.getenv('WX_APP_ID')  # 替换为你的微信公众号AppID
    redirect_uri = quote("https://yourdomain.com/wechat/callback")  # 替换为你的回调URL
    state = str(uuid.uuid4())  # 生成一个随机状态值，用于防止CSRF攻击
    redis_client.setex(f"wechat_login:{state}", 300, "pending")  # 使用Redis存储状态值

    wechat_login_url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"appid={app_id}&redirect_uri={redirect_uri}&response_type=code"
        f"&scope=snsapi_userinfo&state={state}#wechat_redirect"
    )

    return {
        "code": "success",
        "data": {
            "login_url": wechat_login_url,
            "login_token": state
        }
    }


def generate_user_token(user):
    token = f"user:{user.id}"
    current_timestamp = int(time.time())
    redis_client.setex(token, 3600, current_timestamp)
    user_info = {
        'id': user.id,
        'username': user.username,
        'is_admin': user.is_admin
    }
    cache.set(str(user.id), user_info)
    return token

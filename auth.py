import hashlib
import time
from flask import Blueprint, request, session
import constants
from decorators import response_format
from models import User
from services import redis_client
from cache import cache


auth_bp = Blueprint('auth', __name__)

# 用户登录
@auth_bp.route('/login', methods=['POST'])
@response_format
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = User.query.filter_by(username=username, password=hashed_password).first()  # 确保 User 模型已经导入

    if user is None:
        return {"code":constants.RESULT_FAIL,"message": "用户名或密码错误"}

    # 登录成功，生成 token（这里简单使用用户 ID 作为 token）
    token = f"user:{user.id}"  # 示例：使用用户名的 ID 作为 token

    current_timestamp = int(time.time())

    # 将 token 存储到 Redis，过期时间为 1 小时（3600 秒）
    redis_client.setex(token, 3600, current_timestamp)
    # 存储用户信息到会话
    user_info = {
        'id': user.id,
        'username': user.username,
        'is_admin': user.is_admin
    }
    cache.set(str(user.id), user_info)

    return {
        "code":constants.RESULT_SUCCESS,
        "data": {
            "token": current_timestamp,
            "user": {"id": user.id, "username": user.username, "isAdmin": user.is_admin},
        }
    }


@auth_bp.route('/logout', methods=['POST'])
@response_format
def logout():
    # 从请求中获取 token
    data = request.get_json()
    token = data.get('token')

    if not token:
        return {"code": constants.RESULT_FAIL, "message": "未提供 token"}

    # 从 Redis 中删除 token
    redis_client.delete(token)

    # 可选：从缓存中删除用户信息
    user_id = token.split(":")[-1]  # 提取用户 ID
    cache.delete(str(user_id))

    return {
        "code": constants.RESULT_SUCCESS,
        "message": "登出成功"
    }
from flask import  request, Response, session, g
from functools import wraps
import json
import constants
from services import redis_client
from cache import cache
def response_format(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 调用原始视图函数
        objects = func(*args, **kwargs)

        # 如果返回的是 Flask 的 Response 对象，直接返回
        if isinstance(objects, Response):
            return objects

        # 如果返回的是字典，则进行 JSON 序列化
        data = json.dumps(objects)

        # 检查是否为 JSONP 请求
        callback = request.args.get('callback') or request.form.get('callback')
        if callback:
            # 如果有 callback 参数，返回 JSONP 格式
            data = f'{callback}({data});'
            return Response(data, content_type='application/javascript')

        # 默认返回 JSON 格式
        return Response(data, content_type='application/json')

    return decorated_function



def login_required(func):
    # 身份校验
    @wraps(func)
    def inner(*args, **kwargs):
        token = request.headers.get('token')

        if token:
            token = token.split('_')
            key = f"user:{token[1]}"

            # 从 Redis 中读取 token
            current_timestamp = redis_client.get(key)
            if current_timestamp:
                current_timestamp = current_timestamp.decode('utf-8')
                if current_timestamp == token[0]:
                    user_info = cache.get(token[1])
                    if user_info:
                        g.user_info = user_info
                    return func(*args, **kwargs)
        return {"code": constants.UNAUTHORIZED, "msg": "Token expired"}


    return inner


def admin_required(func):
    #  校验是否管理员
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_info = g.user_info

        # 检查是否为管理员
        if user_info and not user_info['is_admin']:
            return {"code": constants.RESULT_FAIL, "message": "权限不足"}
        # 如果检查通过，调用原始的视图函数
        return func(*args, **kwargs)

    return wrapper
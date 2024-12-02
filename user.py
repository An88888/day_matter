# user.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format, admin_required
from models import db, User
import hashlib

user_bp = Blueprint('user', __name__)

# 用户注册
@user_bp.route('/users/save', methods=['POST'])
@login_required
@admin_required
@response_format
def user_save():
    data = request.get_json()
    user_id = data.get('id')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')  # 默认值为 False

    if role == 'admin':
        is_admin = True
    else:
        is_admin = False

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return {"code": constants.RESULT_FAIL, "message": "用户不存在"}

        # 更新用户名
        if username and user.username != username:
            if User.query.filter_by(username=username).first():
                return {"code": constants.RESULT_FAIL, "message": "用户名已存在"}
            user.username = username

        # 更新密码
        if password:
            user.password = hashlib.sha256(password.encode()).hexdigest()

        # 更新角色
        user.is_admin = is_admin

    else:
        # 创建新用户
        if User.query.filter_by(username=username).first():
            return {"code": constants.RESULT_FAIL, "message": "用户已存在"}

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        new_user = User(username=username, password=hashed_password, is_admin=is_admin)
        db.session.add(new_user)

    db.session.commit()

    return {"code": constants.RESULT_SUCCESS, "message": "操作成功"}

# 获取所有用户
@user_bp.route('/users', methods=['GET'])
@login_required
@admin_required
@response_format
def get_users():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    username = request.args.get('username', '')

    # 构建查询
    query = User.query

    # 如果有搜索关键词，添加过滤条件
    if username:
        query = query.filter(User.username.ilike(f'%{username}%'))

    # 获取总记录数
    total = query.count()

    # 分页查询
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': user.id,
                'username': user.username,
                'role': 'admin' if user.is_admin else 'user'
            } for user in users
        ],
        'total': total
    }


# 删除用户
@user_bp.route('/users/del', methods=['POST'])
@login_required
@admin_required
@response_format
def delete_user():
    data = request.get_json()
    user_id = data.get('id')
    user = User.query.get(user_id)
    if user is None:
        return {"code":constants.RESULT_FAIL,"message": "用户不存在"}

    db.session.delete(user)
    db.session.commit()
    return {"code":constants.RESULT_SUCCESS,"message": "用户删除成功"}

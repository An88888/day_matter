# event.py
from flask import Blueprint, request, jsonify, g

import constants
from decorators import login_required, response_format
from models import db, Event
from datetime import datetime

event_bp = Blueprint('event', __name__)

# 创建事件
@event_bp.route('/events/save', methods=['POST'])
@login_required
@response_format
def event_save():
    data = request.get_json()
    event_id = data.get('id')  # 事件ID，如果存在则更新，否则创建
    name = data.get('name')
    target_date = data.get('target_date')  # 假设是字符串格式，如 "2023-12-31"
    status = data.get('status')  # 创建事件的用户ID
    user_info = g.user_info

    # 将 target_date 转换为日期对象
    target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

    if event_id and event_id >0:
        # 更新现有事件
        event = Event.query.get(event_id)
        if not event:
            return {"code": constants.RESULT_FAIL, "message": "Event not found"}

        # 确保当前用户有权限更新
        if event.user_id != user_info['id'] and not user_info['is_admin']:
            return {"code": constants.RESULT_FAIL,
                    "message": "You do not have permission to update this event"}

        event.name = name
        event.target_date = target_date
        event.status = status  # 如果 status 是要更新的字段

    else:
        # 创建新事件
        event = Event(name=name, target_date=target_date, user_id=user_info['id'], status=status)
        db.session.add(event)

    db.session.commit()

    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "event_id": event.id}

# 获取用户的所有事件
@event_bp.route('/events', methods=['GET'])
@login_required
@response_format
def get_user_events():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    title = request.args.get('title', '')
    user_info = g.user_info

    # 构建查询
    query = Event.query
    if user_info and not user_info['is_admin']:
        query = query.filter(Event.user_id == user_info.id)
    # 如果有搜索关键词，添加过滤条件
    if title:
        query = query.filter(Event.name.ilike(f'%{title}%'))

    # 获取总记录数
    total = query.count()

    # 分页查询
    events = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': event.id,
                'name': event.name,
                'status': event.status,
                'target_date': str(event.target_date)
            } for event in events
        ],
        'total': total
    }

# 删除事件
@event_bp.route('/events/del', methods=['POST'])
@login_required
@response_format
def delete_event():
    data = request.get_json()
    event_id = data.get('id')  # 事件ID，如果存在则更新，否则创建

    user_info = g.user_info

    event = Event.query.get(event_id)
    if event is None:
        return {"code":constants.RESULT_FAIL,"message": "事件不存在"}

    if user_info and (user_info['is_admin'] or event.user_id == user_info['id']):
        pass
    else:
        return {"code": constants.RESULT_FAIL,"message": "权限不足"}

    db.session.delete(event)
    db.session.commit()
    return {"code":constants.RESULT_SUCCESS,"message": "事件删除成功"}

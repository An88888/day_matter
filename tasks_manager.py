from flask import Blueprint, request
import constants
from decorators import login_required, response_format, admin_required
from models import db, ScheduledTask
from celery import current_app
import logging

tasks_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)  # 获取当前模块的 logger


# 创建或更新任务
@tasks_bp.route('/tasks/save', methods=['POST'])
@login_required
@admin_required
@response_format
def task_save():
    data = request.get_json()
    task_id = data.get('id')
    name = data.get('name')
    task_type = data.get('task_type')
    is_active = data.get('is_active', True)
    schedule_type = data.get('schedule_type', 'crontab')
    crontab_expression = data.get('crontab_expression')
    interval_every = data.get('interval_every')
    interval_period = data.get('interval_period')

    # 验证任务数据
    if not name or len(name) < 3:
        return {"code": constants.RESULT_FAIL, "message": "任务名称无效"}

    try:
        if task_id:
            task = ScheduledTask.query.get(task_id)
            if not task:
                return {"code": constants.RESULT_FAIL, "message": "任务不存在"}

            # 更新任务信息
            task.name = name
            task.task_type = task_type
            task.is_active = is_active
            task.schedule_type = schedule_type
            task.crontab_expression = crontab_expression
            task.interval_every = interval_every
            task.interval_period = interval_period

        else:
            # 创建新任务
            if ScheduledTask.query.filter_by(name=name).first():
                return {"code": constants.RESULT_FAIL, "message": "任务已存在"}

            new_task = ScheduledTask(
                name=name,
                task_type=task_type,
                is_active=is_active,
                schedule_type=schedule_type,
                crontab_expression=crontab_expression,
                interval_every=interval_every,
                interval_period=interval_period
            )
            db.session.add(new_task)

        db.session.commit()
        return {"code": constants.RESULT_SUCCESS, "message": "操作成功"}

    except Exception as e:
        db.session.rollback()  # 回滚事务
        return {"code": constants.RESULT_FAIL, "message": str(e)}

# 获取所有任务
@tasks_bp.route('/tasks', methods=['GET'])
@login_required
@admin_required
@response_format
def get_tasks():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    name = request.args.get('name', '')

    # 构建查询
    query = ScheduledTask.query

    # 如果有搜索关键词，添加过滤条件
    if name:
        query = query.filter(ScheduledTask.name.ilike(f'%{name}%'))

    # 获取总记录数
    total = query.count()

    # 分页查询
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': task.id,
                'name': task.name,
                'task_type': task.task_type,
                'is_active': task.is_active,
                'frequency': task.frequency,
                'schedule_type': task.schedule_type,
                # 根据任务的调度类型返回相应的字段
                'crontab_expression': task.crontab.schedule if task.is_periodic and task.schedule_type == 'crontab' else None,
                'interval_every': task.interval.every if task.is_periodic and task.schedule_type == 'interval' else None,
                'interval_period': task.interval.period if task.is_periodic and task.schedule_type == 'interval' else None
            } for task in tasks
        ],
        'total': total
    }


# 删除任务
@tasks_bp.route('/tasks/del', methods=['POST'])
@login_required
@admin_required
@response_format
def delete_task():
    data = request.get_json()
    task_id = data.get('id')
    task = ScheduledTask.query.get(task_id)
    if task is None:
        return {"code": constants.RESULT_FAIL, "message": "任务不存在"}

    try:
        db.session.delete(task)
        db.session.commit()
        return {"code": constants.RESULT_SUCCESS, "message": "任务删除成功"}
    except Exception as e:
        db.session.rollback()  # 回滚事务
        return {"code": constants.RESULT_FAIL, "message": str(e)}


# 获取所有任务
@tasks_bp.route('/tasks/list', methods=['GET'])
@login_required
@admin_required
@response_format
def get_tasks_list():
    # 获取所有注册的任务
    task_list = current_app.tasks
    
    # 提取自定义任务（排除 celery. 开头的系统任务）
    task_info = []
    for task_name, task in task_list.items():
        # 只处理不是以 'celery.' 开头的任务
        if not task_name.startswith('celery.') and hasattr(task, 'run'):
            task_info.append({
                'name': task_name,
                'type': task.__class__.__name__,
                'description': task.__doc__ or '无描述'
            })

    return {
        'code': 200, 
        'data': task_info, 
        'message': '获取任务列表成功'
    }
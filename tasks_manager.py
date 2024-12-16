from datetime import timedelta

from flask import Blueprint, request
import constants
from decorators import login_required, response_format, admin_required
from models import db, ScheduledTask, CrontabSchedule, IntervalSchedule
from celery import current_app
import logging
from extensions import celery

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
    task_type = data.get('task_name')
    is_active = data.get('is_active', True)
    schedule_type = data.get('schedule_type', 'crontab')
    crontab_id =data.get('crontab_id')
    interval_id =data.get('interval_id')
    crontab_id = None if crontab_id == '' or crontab_id is None else int(crontab_id)
    interval_id = None if interval_id == '' or interval_id is None else int(interval_id)

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
            task.crontab_id = crontab_id
            task.interval_id = interval_id

        else:
            # 创建新任务
            if ScheduledTask.query.filter_by(name=name).first():
                return {"code": constants.RESULT_FAIL, "message": "任务已存在"}

            task = ScheduledTask(
                name=name,
                task_type=task_type,
                is_active=is_active,
                schedule_type=schedule_type,
                crontab_id=crontab_id,
                interval_id=interval_id,
            )
            db.session.add(task)

        db.session.commit()
        send_celery(task)
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
                'crontab_id': task.crontab_id,
                'interval_id': task.interval_id,
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


def send_celery(new_task):
    task_path = new_task.task_type
    task_name = task_path.split('.')[-1]

    # 动态获取任务对象
    task = celery.tasks.get(task_path)
    try:

        if not task:
            return {"code": constants.RESULT_FAIL, "message": "任务未找到"}

        if new_task.is_active == False:
            # 暂停任务
            celery.control.revoke(task_name)
            return {"code": constants.RESULT_SUCCESS, "message": "任务已暂停"}

        if new_task.schedule_type == 'crontab':
            crontab = CrontabSchedule.query.get(new_task.crontab_id)
            if not crontab:
                return {"code": constants.RESULT_FAIL, "message": "Crontab 未找到"}

            # 创建 Celery 的 crontab 调度
            celery.add_periodic_task(
                crontab(minute=crontab.minute, hour=crontab.hour,
                        day_of_week=crontab.day_of_week,
                        day_of_month=crontab.day_of_month,
                        month_of_year=crontab.month_of_year),
                task.s(),
                name=f'task-{new_task.name}'  # 可选，给任务一个唯一的名称
            )
        elif new_task.schedule_type == 'interval':
            interval_period = IntervalSchedule.query.get(new_task.interval_id)
            if not interval_period:
                return {"code": constants.RESULT_FAIL, "message": "Interval 未找到"}

            # 根据 period 字段的值计算间隔时间（单位：秒）
            if interval_period.period == 'seconds':
                interval_seconds = interval_period.every
            elif interval_period.period == 'minutes':
                interval_seconds = interval_period.every * 60
            elif interval_period.period == 'hours':
                interval_seconds = interval_period.every * 3600
            elif interval_period.period == 'days':
                interval_seconds = interval_period.every * 86400
            else:
                return {"code": constants.RESULT_FAIL, "message": "无效的 period 参数"}

            # 添加周期性任务
            celery.add_periodic_task(
                interval_seconds,  # 间隔时间，单位：秒
                task.s(),
                name=f'task-{new_task.name}',  # 给任务一个唯一的名称
            )
        else:
            return {"code": constants.RESULT_FAIL, "message": "无效的 schedule_type 参数"}
    except Exception as e:
        logger.error("========add_task_erroe")
        logger.error(e)
        print(e)

    return {"code": constants.RESULT_SUCCESS, "message": "任务添加成功"}
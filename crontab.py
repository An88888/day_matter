# food.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format
from models import db, CrontabSchedule

crontab_bp = Blueprint('crontab', __name__)

@crontab_bp.route('/crontab/save', methods=['POST'])
@login_required
@response_format
def crontab_save():
    data = request.get_json()
    crontab_id = data.get('id')  # crontabID，如果存在则更新，否则创建

    schedule = data.get('schedule')

    # 将调度表达式拆分成各个部分
    parts = schedule.split()

    if len(parts) == 5:
        minute = parts[0]
        hour = parts[1]
        day_of_month = parts[2]
        month_of_year = parts[3]
        day_of_week = parts[4]
    else:
        return {"code": constants.RESULT_FAIL, "message": "crontab crontab expression"}

    if crontab_id and crontab_id > 0:
        crontab = CrontabSchedule.query.get(crontab_id)
        if not crontab:
            return {"code": constants.RESULT_FAIL, "message": "crontab item not found"}

        crontab.minute = minute
        crontab.hour = hour
        crontab.day_of_week = day_of_week
        crontab.day_of_month = day_of_month
        crontab.month_of_year = month_of_year


    else:
        crontab = CrontabSchedule(
            minute = minute,
            hour = hour,
            day_of_week = day_of_week,
            day_of_month = day_of_month,
            month_of_year = month_of_year,
        )
        db.session.add(crontab)

    db.session.commit()

    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "crontab_id": crontab.id}


@crontab_bp.route('/crontab', methods=['GET'])
@login_required
@response_format
def get_crontab():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    # 构建查询
    query = CrontabSchedule.query

    # 获取总记录数
    total = query.count()

    # 分页查询
    crontabs = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': crontab.id,
                'schedule': f"{crontab.minute} {crontab.hour} {crontab.day_of_week} {crontab.day_of_month} {crontab.month_of_year}"

            } for crontab in crontabs
        ],
        'total': total
    }


@crontab_bp.route('/crontab/del', methods=['POST'])
@login_required
@response_format
def delete_crontab():
    data = request.get_json()
    crontab_id = data.get('id')  # 食物ID

    crontab = CrontabSchedule.query.get(crontab_id)
    if crontab is None:
        return {"code": constants.RESULT_FAIL, "message": "crontab item not found"}

    db.session.delete(crontab)
    db.session.commit()
    return {"code": constants.RESULT_SUCCESS, "message": "crontab item deleted successfully"}



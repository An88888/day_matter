# food.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format
from models import db, IntervalSchedule

interval_bp = Blueprint('interval', __name__)

@interval_bp.route('/interval/save', methods=['POST'])
@login_required
@response_format
def interval_save():
    data = request.get_json()
    interval_id = data.get('id')  # crontabID，如果存在则更新，否则创建
    every = data.get('duration')
    period = data.get('unit')

    if interval_id and interval_id > 0:
        interval = IntervalSchedule.query.get(interval_id)
        if not interval:
            return {"code": constants.RESULT_FAIL, "message": "interval item not found"}

        interval.every = every
        interval.period = period

    else:
        # 创建新食物项
        interval = IntervalSchedule(
            every = every,
            period = period,
        )
        db.session.add(interval)

    db.session.commit()

    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "interval_id": interval.id}


@interval_bp.route('/interval', methods=['GET'])
@login_required
@response_format
def get_interval():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    # 构建查询
    query = IntervalSchedule.query

    # 获取总记录数
    total = query.count()

    # 分页查询
    intervals = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': interval.id,
                'duration': interval.every,
                'unit': interval.period
            } for interval in intervals
        ],
        'total': total
    }

@interval_bp.route('/interval/del', methods=['POST'])
@login_required
@response_format
def delete_interval():
    data = request.get_json()
    interval_id = data.get('id')  # 食物ID

    interval = IntervalSchedule.query.get(interval_id)
    if interval is None:
        return {"code": constants.RESULT_FAIL, "message": "interval item not found"}

    db.session.delete(interval)
    db.session.commit()
    return {"code": constants.RESULT_SUCCESS, "message": "interval item deleted successfully"}



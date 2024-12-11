# food.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format
from models import db, Cate

cate_bp = Blueprint('cate', __name__)

# 创建食物项
# 创建食物项
@cate_bp.route('/cate/save', methods=['POST'])
@login_required
@response_format
def cate_save():
    data = request.get_json()
    cate_id = data.get('id')  # 分类ID，如果存在则更新，否则创建
    name = data.get('name')
    user_info = g.user_info


    if cate_id and cate_id > 0:
        # 更新现有分类
        cate = Cate.query.get(cate_id)
        if not cate_id:
            return {"code": constants.RESULT_FAIL, "message": "Cate item not found"}

        cate_id.name = name

    else:
        # 创建新分类
        cate = Cate(
            name=name,
            user_id=user_info['id'],  # 绑定当前用户ID
        )
        db.session.add(cate)

    db.session.commit()
    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "cate_id": cate.id}


# 获取所有食物项
@cate_bp.route('/cate', methods=['GET'])
@login_required
@response_format
def get_cate():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    name = request.args.get('title', '')

    # 构建查询
    query = Cate.query

    if name:
        query = query.filter(Cate.name.ilike(f'%{name}%'))
    # 获取总记录数
    total = query.count()

    # 分页查询
    cates = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': cate.id,
                'name': cate.name,
            } for cate in cates
        ],
        'total': total
    }

# 删除食物项
@cate_bp.route('/food/del', methods=['POST'])
@login_required
@response_format
def delete_cate():
    data = request.get_json()
    food_id = data.get('id')  # 食物ID

    user_info = g.user_info

    cate = Cate.query.get(food_id)
    if cate is None:
        return {"code": constants.RESULT_FAIL, "message": "Cate item not found"}

    if user_info and (user_info['is_admin'] or cate.user_id == user_info['id']):
        pass
    else:
        return {"code": constants.RESULT_FAIL, "message": "Insufficient permissions"}

    db.session.delete(cate)
    db.session.commit()
    return {"code": constants.RESULT_SUCCESS, "message": "Cate item deleted successfully"}

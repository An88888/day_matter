# food.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format
from models import db, Ingredient

ingredient_bp = Blueprint('ingredient', __name__)

# 创建食物项
# 创建食物项
@ingredient_bp.route('/ingredient/save', methods=['POST'])
@login_required
@response_format
def ingredient_save():
    data = request.get_json()
    ingredient_id = data.get('id')  # 食物ID，如果存在则更新，否则创建
    name = data.get('name')
    user_info = g.user_info


    if ingredient_id and ingredient_id > 0:
        # 更新现有食物项
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient:
            return {"code": constants.RESULT_FAIL, "message": "Food item not found"}

        ingredient.name = name

    else:
        # 创建新食物项
        ingredient = Ingredient(
            name=name,
            user_id=user_info['id'],  # 绑定当前用户ID
        )
        db.session.add(ingredient)

    db.session.commit()

    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "ingredient_id": ingredient.id}


# 获取所有食物项
@ingredient_bp.route('/ingredient', methods=['GET'])
@login_required
@response_format
def get_ingredient():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    name = request.args.get('title', '')

    # 构建查询
    query = Ingredient.query

    if name:
        query = query.filter(Ingredient.name.ilike(f'%{name}%'))
    # 获取总记录数
    total = query.count()

    # 分页查询
    ingredients = query.offset((page - 1) * page_size).limit(page_size).all()

    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': ingredient.id,
                'name': ingredient.name,

            } for ingredient in ingredients
        ],
        'total': total
    }

# 删除食物项
@ingredient_bp.route('/ingredient/del', methods=['POST'])
@login_required
@response_format
def delete_ingredient():
    data = request.get_json()
    food_id = data.get('id')  # 食物ID

    user_info = g.user_info

    ingredient = Ingredient.query.get(food_id)
    if ingredient is None:
        return {"code": constants.RESULT_FAIL, "message": "Ingredient item not found"}

    if user_info and (user_info['is_admin'] or ingredient.user_id == user_info['id']):
        pass
    else:
        return {"code": constants.RESULT_FAIL, "message": "Insufficient permissions"}

    db.session.delete(ingredient)
    db.session.commit()
    return {"code": constants.RESULT_SUCCESS, "message": "Ingredient item deleted successfully"}



# food.py
from flask import Blueprint, request, g
import constants
from decorators import login_required, response_format
from models import db, Food, Image, Cate, FoodIngredient, FoodCate

food_bp = Blueprint('food', __name__)

# 创建食物项
# 创建食物项
@food_bp.route('/food/save', methods=['POST'])
@login_required
@response_format
def food_save():
    data = request.get_json()
    food_id = data.get('id')  # 食物ID，如果存在则更新，否则创建
    name = data.get('name')
    ingredients = data.get('ingredients')  # 食材
    procedure = data.get('procedure')  # 制作方法
    image_list = data.get('images')
    cate_list = data.get('cate')
    ingredients_list = data.get('ingredients')

    user_info = g.user_info

    if food_id and food_id > 0:
        # 更新现有食物项
        food = Food.query.get(food_id)
        if not food:
            return {"code": constants.RESULT_FAIL, "message": "Food item not found"}

        food.name = name
        food.ingredients = ingredients
        food.procedure = procedure

    else:
        # 创建新食物项
        food = Food(
            name=name,
            procedure=procedure,
            user_id=user_info['id'],  # 绑定当前用户ID
        )
        db.session.add(food)

    db.session.commit()
    __save_goods_img(image_list, food)
    __save_goods_cate(cate_list,food)
    __save_goods_ingredients(ingredients_list,food)

    # 返回成功信息
    return {"code": constants.RESULT_SUCCESS, "food_id": food.id}


# 获取所有食物项
@food_bp.route('/food', methods=['GET'])
@login_required
@response_format
def get_foods():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    name = request.args.get('title', '')

    # 构建查询
    query = Food.query

    if name:
        query = query.filter(Food.name.ilike(f'%{name}%'))
    # 获取总记录数
    total = query.count()

    # 分页查询
    foods = query.offset((page - 1) * page_size).limit(page_size).all()



    # 返回数据
    return {
        "code": constants.RESULT_SUCCESS,
        'data': [
            {
                'id': food.id,
                'name': food.name,
                'cate': [cate.id for cate in food.cate],
                'ingredients': [ingredient.id for ingredient in food.ingredient],
                'ing_names' : [food_ingredient.ingredient.name for food_ingredient in food.ingredient],
                'procedure': food.procedure,
                'images': [image.url for image in food.images]
            } for food in foods
        ],
        'total': total
    }

# 删除食物项
@food_bp.route('/food/del', methods=['POST'])
@login_required
@response_format
def delete_food():
    data = request.get_json()
    food_id = data.get('id')  # 食物ID

    user_info = g.user_info

    food = Food.query.get(food_id)
    if food is None:
        return {"code": constants.RESULT_FAIL, "message": "Food item not found"}

    if user_info and (user_info['is_admin'] or food.user_id == user_info['id']):
        pass
    else:
        return {"code": constants.RESULT_FAIL, "message": "Insufficient permissions"}

    db.session.delete(food)
    db.session.commit()
    return {"code": constants.RESULT_SUCCESS, "message": "Food item deleted successfully"}


def __save_goods_img(image_list, new_food):
    if not new_food or not new_food.id:
        raise ValueError("Invalid food information provided.")

    # 清除旧的图片记录
    Image.query.filter_by(food_id=new_food.id).delete()

    if image_list:
        for img in image_list:
            if img:
                goods_img = Image(url=img, food_id=new_food.id)  # 直接设置 food_id
                try:
                    db.session.add(goods_img)  # 添加新的 Image 实例
                    db.session.commit()  # 提交会话
                except Exception as e:
                    db.session.rollback()  # 回滚会话
                    print(f"Error saving image {img}: {e}")
            else:
                print("Received an empty image URL.")
    else:
        print("No images provided to save.")

def __save_goods_cate(cate_list, new_food):
    if not new_food or not new_food.id:
        raise ValueError("Invalid food information provided.")

    # 清除旧的图片记录
    FoodCate.query.filter_by(food_id=new_food.id).delete()

    if cate_list:
        for cate in cate_list:
            if cate:
                goods_cate = FoodCate(cate_id=cate, food_id=new_food.id)  # 直接设置 food_id
                try:
                    db.session.add(goods_cate)  # 添加新的 Image 实例
                    db.session.commit()  # 提交会话
                except Exception as e:
                    db.session.rollback()  # 回滚会话
                    print(f"Error saving cate {cate}: {e}")
            else:
                print("Received an empty cate name.")
    else:
        print("No cate provided to save.")

def __save_goods_ingredients(ingredients_list, new_food):
    if not new_food or not new_food.id:
        raise ValueError("Invalid food information provided.")

    # 清除旧的图片记录
    FoodIngredient.query.filter_by(food_id=new_food.id).delete()

    if ingredients_list:
        for ingredients in ingredients_list:
            if ingredients:
                goods_ingredients = FoodIngredient(ingredient_id=ingredients, food_id=new_food.id)  # 直接设置 food_id
                try:
                    db.session.add(goods_ingredients)  # 添加新的 Image 实例
                    db.session.commit()  # 提交会话
                except Exception as e:
                    db.session.rollback()  # 回滚会话
                    print(f"Error saving ingredients {ingredients}: {e}")
            else:
                print("Received an empty ingredients URL.")
    else:
        print("No ingredients provided to save.")
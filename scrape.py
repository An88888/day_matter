from flask import Blueprint, request
import constants
from models import Food, db, Ingredient, FoodIngredient
from decorators import login_required, response_format
from kitchen import Kitchen

scrape_bp = Blueprint('scrape', __name__)


@scrape_bp.route('/scrape', methods=['GET'])
@login_required
@response_format
def scrape_recipes():
    kitchen = Kitchen()

    page = request.args.get('page', 1, type=int)

    html = kitchen.get_page(kitchen.url.format(page))
    if html:
        recipes = kitchen.parse_page(html)
        for recipe in recipes:
            new_food = Food(
                name=recipe[0],
                procedure=recipe[1],
                user_id=1,
            )
            save_food(new_food, recipe)
            handel_foods(new_food, recipe[2])

    db.session.commit()  # 提交所有变更
    return {"code": constants.RESULT_SUCCESS, "message": "数据爬取完成！"}

def save_food(new_food, recipe):
    existing_food = Food.query.filter_by(name=recipe[0]).first()
    if existing_food:
        print(f"菜名 '{recipe[0]}' 已存在，跳过...")
        return

    db.session.add(new_food)


def handel_foods(new_food, ingredients):
    ingredients_list = ingredients.split('、')

    if ingredients_list and len(ingredients_list) > 1:
        for ingredient_name in ingredients_list:
            ingredient_name = ingredient_name.strip()
            existing_ingredient = Ingredient.query.filter_by(name=ingredient_name).first()

            if existing_ingredient:
                ingredient_id = existing_ingredient.id
                print(f"食材 '{ingredient_name}' 已存在，ID 为 {ingredient_id}")
            else:
                new_ingredient = Ingredient(
                    name=ingredient_name,
                    user_id=1
                )
                db.session.add(new_ingredient)
                # 提交以获取 ID
                db.session.commit()
                ingredient_id = new_ingredient.id
                print(f"创建新的食材 '{ingredient_name}'，ID 为 {ingredient_id}")

            food_ingredient = FoodIngredient(
                food_id=new_food.id,
                ingredient_id=ingredient_id
            )
            db.session.add(food_ingredient)
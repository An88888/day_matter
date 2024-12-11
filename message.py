from flask import Blueprint, request
import constants
from decorators import login_required, response_format, admin_required
from models import User, Food
from sms import send_message
from weather import Weather
import random

import logging

msg_bp = Blueprint('msg', __name__)
logger = logging.getLogger(__name__)  # 获取当前模块的 logger


# 创建或更新任务
@msg_bp.route('/msg/send', methods=['POST'])
@login_required
@admin_required
@response_format
def msg_send():
    try:
        data = request.get_json()
        message = data.get('content')
        user_id = data.get('user_id')
        user_info = User.query.get(user_id)
        if user_info:
            pass
        else:
            return {"code": constants.RESULT_FAIL, "message": "用户不存在"}
        user = user_info.device_key
        send_message(user,message)
        return {"code": constants.RESULT_SUCCESS}

    except Exception as e:
        return {"code": constants.RESULT_FAIL, "message": str(e)}


# @msg_bp.route('/msg/all', methods=['POST'])
# @login_required
# @admin_required
@response_format
def msg_send_all():
    try:
        # 获取所有食物和其对应的食材信息
        message = ''  # 初始化消息字符串

        foods_name = get_today_food()
        if foods_name and isinstance(foods_name,list) and len(foods_name) > 0:
            pass
        else:
            return {"code": constants.RESULT_FAIL, "message": "没有菜"}

        foods = Food.query.filter(Food.name.in_(foods_name)).all()  # 筛选与 foods_name 匹配的菜名

        for food in foods:
            # 获取菜名
            food_name = food.name

            # 获取所需材料
            ingredient_names = [ingredient.ingredient.name for ingredient in food.ingredient]

            # 将菜名和食材格式化为字符串
            if ingredient_names:
                ingredient_list = ', '.join(ingredient_names)  # 连接食材为字符串
                message += f"{food_name}: {ingredient_list}\n"  # 组装消息
            else:
                message += f"{food_name}: (无材料)\n"  # 如果没有材料
        # 获取所有用户
        user_qs = User.query.filter(User.device_key.isnot(None), User.device_key != '').all()
        if user_qs:
            for user in user_qs:
                send_message(user.device_key, message, '今日菜单')  # 发送消息给用户

            return {"code": constants.RESULT_SUCCESS}
        else:
            return {"code": constants.RESULT_FAIL, "message": "用户不存在"}

    except Exception as e:
        return {"code": constants.RESULT_FAIL, "message": str(e)}


def get_today_food():
    foods_with_ingredients = Food.query.filter(Food.ingredient.any()).all()
    food_names = [food.name for food in foods_with_ingredients]

    return random.sample(food_names, min(len(food_names), 2))

    # weather_api = Weather()  # 创建 Weather 类的实例
    # weather_data = weather_api.get_weather()  # 通过实例调用 get_weather 方法
    #
    # if isinstance(weather_data, dict) and weather_data.get("code") == constants.RESULT_SUCCESS:
    #     weather_data = weather_data.get("data")
    #     weather, temperature, humidity = weather_data['weather'], weather_data['temperature'], weather_data['humidity']
    #
    #     return choose_dishes_based_on_weather(food_names, weather, temperature, humidity)
    #
    # return []
def choose_dishes_based_on_weather(dish_names, weather, temperature, humidity):
    """根据天气条件选择菜名"""
    if humidity > 70:
        suitable_dishes = [dish for dish in dish_names if "凉" in dish or "沙拉" in dish]  # 高湿选择清淡的菜
    elif weather in ['晴', '云'] and temperature > '25':
        suitable_dishes = [dish for dish in dish_names if "凉" in dish or "沙拉" in dish]  # 晴天选择清淡的菜
    elif weather in ['Rain', 'Thunderstorm', 'Snow']:
        suitable_dishes = [dish for dish in dish_names if "汤" in dish or "炖" in dish]  # 雨天或雪天选择热汤
    elif temperature < '15':
        suitable_dishes = [dish for dish in dish_names if "火锅" in dish or "炖" in dish]  # 寒冷天气选择温暖的菜
    else:
        suitable_dishes = [dish for dish in dish_names if "热" in dish]  # 其他情况选择热菜

    name = random.sample(suitable_dishes, min(len(suitable_dishes), 2))
    # 随机选择两道菜
    return name
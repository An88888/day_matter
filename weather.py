# weather.py
import requests
from fake_useragent import UserAgent
import os
import constants

class Weather:
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.url = os.getenv('WEATHER_URL')
        self.city = os.getenv('WEATHER_API_CITY')

        self.ua = UserAgent()  # 创建 UserAgent 实例

    def get_weather(self):
        # 构建请求 URL
        params = {
            'key': self.api_key,
            'city': self.city,
        }
        # 发送请求
        response = requests.get(self.url, headers={"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}, params=params)

        print("======get_we")
        print(response)

        # 检查响应状态
        if response.status_code == 200:
            data = response.json()
            weather = data['lives'][0]['weather']  # 获取天气状态
            temperature = str(data['lives'][0]['temperature'])  # 获取当前温度
            humidity = int(data['lives'][0]['humidity'])  # 获取当前湿度
            return {"code": constants.RESULT_SUCCESS,
                    "data": {"weather":weather,
                             "temperature":temperature,
                             "humidity":humidity,
                             }}
        else:
            return {"code": constants.RESULT_FAIL}

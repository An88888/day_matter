import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class Kitchen:
    def __init__(self):
        self.url = "https://www.xiachufang.com/explore/?page={}"
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }

    def get_page(self, url):
        try:
            res = requests.get(url=url, headers=self.headers)
            res.raise_for_status()
            return res.text
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None

    def parse_page(self, html):
        bs_foods = BeautifulSoup(html, 'html.parser')
        tag_name = bs_foods.find_all('p', class_='name')
        tag_procedure = bs_foods.find_all('p', class_='ing ellipsis')

        list_all = []

        for x in range(len(tag_name)):
            recipe_name = tag_name[x].text.strip()
            recipe_link = 'https://www.xiachufang.com'+ tag_name[x].find('a')['href']
            ingredients = tag_procedure[x].text.strip() if x < len(tag_procedure) else "无食材"

            list_all.append([recipe_name, recipe_link, ingredients])

        return list_all
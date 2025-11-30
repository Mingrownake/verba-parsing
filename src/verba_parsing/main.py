import pandas
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import json
import math
import asyncio
import httpx

def main():
  result = test_selenium()
  select_item_to_file(result)

def get_item_info(item_id: str):
  print(f"Start: {item_id}")
  url = f"https://sam-basket-cdn-01mg.geobasket.ru/vol{item_id[0:4]}/part{item_id[0:6]}/{item_id}/info/ru/card.json"
  response = requests.get(url)
  data = {}
  if response.status_code == 200:
    data = response.json()
  item_info = {
    "description": data.get("description")
  }
  return item_info

def test_selenium():
  page = 1
  base_url = f"https://www.wildberries.ru/__internal/u-search/exactmatch/ru/api/v18/search?appType=3&curr=rub&dest=-3217375&f14177451=15000203&hide_dtype=9;11&priceU=0;1000000&inheritFilters=false&lang=ru&query=пальто%20из%20натуральной%20шерсти&resultset=catalog&sort=popular&suppressSpellcheck=false"

  driver = get_driver()
  total_pages = math.ceil(get_response(driver, base_url).get("total") / 100)
  result_array = []
  while(total_pages > page):
      page = page + 1
      base_url = f"{base_url}&page={page}"
      items = get_response(driver, base_url).get('products', [])
      result_array.extend(items)
  return result_array

def get_driver() -> webdriver:
  options = Options()
  options.add_argument("User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 YaBrowser/25.10.0.0 Safari/537.36")
  options.add_argument("--disable-blink-features=AutomationControlled")
  driver = webdriver.Chrome(options=options)
  return driver

def get_response(driver: webdriver, url: str):
  wait = 5
  driver.get(url=url)
  WebDriverWait(driver, wait).until(
            ec.presence_of_element_located((By.TAG_NAME, "pre")))
  all_page_text = driver.find_element(By.TAG_NAME, "pre").text
  result = json.loads(all_page_text)
  return result


def select_item_to_file(products):
  items = []
  min_rating = 4.5
  for product in products:
    rating = float(product.get('rating'))
    if rating > min_rating:
      id = product.get("id")
      name = product.get("name")
      price = int(product.get("sizes")[0].get("price").get("product")) / 100
      subject_id = product.get("subjectId")
      kind_id = product.get("kindId")
      brand_id = product.get("brandId")
      item_info = get_item_info(str(id))
      item = {
        "url": f"https://www.wildberries.ru/product/{id}/data?subject={subject_id}&kind={kind_id}&brand={brand_id}&lang=ru",
        "article": id,
        "name": name,
        "price": price,
        "description": item_info["description"]
      }
      items.append(item)
  result = pandas.DataFrame(items)
  result.to_excel("test.xlsx")

if __name__ == "__main__":
  main()

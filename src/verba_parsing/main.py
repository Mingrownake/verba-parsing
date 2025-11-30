import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import json
import math
import asyncio
import httpx

async def main():
  products = test_selenium()
  items = []
  timeout = 60.0
  async with httpx.AsyncClient(timeout=timeout) as client:
    tasks = [test_item(client, product) for product in products]
    items = await asyncio.gather(*tasks)
  result = pd.DataFrame(items)
  result = result[result["url"] != "NONE"]
  result.to_excel("test.xlsx")

async def get_item_info(client: httpx.AsyncClient, item_id: str):
  url = get_wb_cnd(item_id)
  response = await client.get(url)
  data = {}
  if response.status_code == 200:
    data = response.json()
    item_data = {}
    item_data = {
        "description": data.get("description")
    }
    return item_data
  
    
def get_wb_cnd(item_id: str) -> str:
  part = ""
  vol = ""
  part = item_id[0:6]
  if len(item_id) == 9:
    part = item_id[0:6]
    vol = item_id[0:4]
  elif len(item_id) == 8:
    part = item_id[0:5]
    vol = item_id[0:3]
  elif len(item_id) == 7:
    part = item_id[0:4]
    vol = item_id[0:2]
  host = "http://sam-basket-cdn-01mg.geobasket.ru"
  return f"{host}/vol{vol}/part{part}/{item_id}/info/ru/card.json"
  
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

async def test_item(client: httpx.AsyncClient, product):
  min_rating = 4.5
  item = {
    "url": f"NONE",
    "article": "NONE",
    "name": "NONE",
    "price": "NONE",
    "description": "NONE",
    "rating": ""
  }
  rating = float(product.get('reviewRating'))
  if rating >= min_rating:
    id = str(product.get("id"))
    name = product.get("name")
    price = int(product.get("sizes")[0].get("price").get("product")) / 100
    subject_id = product.get("subjectId")
    kind_id = product.get("kindId")
    brand_id = product.get("brandId")
    item_info = await get_item_info(client, id)
    item = {
      "url": f"https://www.wildberries.ru/product/{id}/data?subject={subject_id}&kind={kind_id}&brand={brand_id}&lang=ru",
      "article": id,
      "name": name,
      "price": price,
      "description": item_info.get("description"),
      "rating": rating
    }
  return item

if __name__ == "__main__":
  asyncio.run(main())

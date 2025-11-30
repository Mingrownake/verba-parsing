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
  products = get_all_items()
  items = []
  timeout = 60.0 #Заглушка
  async with httpx.AsyncClient(timeout=timeout) as client:
    tasks = [build_item(client, product) for product in products]
    items = await asyncio.gather(*tasks)
  result = pd.DataFrame(items)
  result = result[result["url"] != "NONE"] #Оставлю пока так, чтобы NONE не ловить
  result.to_excel("test.xlsx")

async def get_item_info(client: httpx.AsyncClient, item_id: str):
  url_info = f"{get_wb_cnd(item_id)}/info/ru/card.json"
  response = await client.get(url_info)
  data = {}
  if response.status_code == 200:
    data = response.json()
    photo_count = int(data.get("media").get("photo_count"))
    tasks = get_photo_url(item_id, photo_count)
    photo_link = ",".join(tasks)
    item_data = {
        "description": data.get("description"),
        "photo_link": photo_link,
        "options": data.get("options")
    }
    return item_data
  
def get_photo_url(item_id: str, count: int):
  result_list = []
  base_url = get_wb_cnd(item_id)
  for i in range(1, count + 1):
    current_url = f"{base_url}/images/big/{i}.webp"
    result_list.append(current_url)
  return result_list

def get_size_list(array) -> str:
  sizes = []
  for item in array:
    sizes.append(item.get("name"))
  return ",".join(sizes)

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
  host = "https://sam-basket-cdn-01mg.geobasket.ru"
  return f"{host}/vol{vol}/part{part}/{item_id}"
  
def get_all_items():
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

async def build_item(client: httpx.AsyncClient, product):
  min_rating = 4.5
  item = {
    "url": "NONE",
    "article": "NONE",
    "name": "NONE",
    "price": "NONE",
    "description": "NONE",
    "photo_link": "NONE",
    "options": "NONE",
    "supplier": "NONE",
    "supplier_url": "NONE",
    "sizes":  "NONE",
    "totalQuantity": "NONE",
    "rating": "NONE",
    "feedbacks": "NONE"
  }
  rating = float(product.get('nmReviewRating'))
  if rating > min_rating:
    id = str(product.get("id"))
    name = product.get("name")
    price = int(product.get("sizes")[0].get("price").get("product")) / 100
    subject_id = product.get("subjectId")
    kind_id = product.get("kindId")
    brand_id = product.get("brandId")
    supplier = product.get("supplier")
    sizes = get_size_list(product.get("sizes"))
    totalQuantity = product.get("totalQuantity")
    feedbacks = product.get("nmFeedbacks")
    item_info = await get_item_info(client, id)
    item = {
      "url": f"https://www.wildberries.ru/product/{id}/data?subject={subject_id}&kind={kind_id}&brand={brand_id}&lang=ru",
      "article": id,
      "name": name,
      "price": price,
      "description": item_info.get("description"),
      "photo_link": item_info.get("photo_link"),
      "options": item_info.get("options"),
      "supplier": supplier,
      "supplier_url": f"https://www.wildberries.ru/seller/{id}",
      "sizes":  sizes,
      "totalQuantity": totalQuantity,
      "rating": rating,
      "feedbacks": feedbacks
    }
  return item

if __name__ == "__main__":
  asyncio.run(main())

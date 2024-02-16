import sys

sys.path.append("src")

import time
import requests
from bs4 import BeautifulSoup, Tag
from log import my_logger
import re
import pandas as pd

def scrape_text(url: str, limit: int = 2) -> pd.DataFrame:
    """
    ククパッドのページからテキストを取得する関数

    Args:
        url (str): URL

    Returns:
        Dataframe: クックパッドのページから取得したテキストとその他の情報

                カラム：
                    url: URL
                    title: タイトル
                    text: テキスト
        
        List: レシピのURL

    Error:
        Exception: station_exits not found
    """

    # クールダウン
    time.sleep(1.5)

    # リクエスト
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # テキストの情報を取得
    # <div class="recipe-title-and-author">
    #   <h2>
    #     <a class="recipe-title" href="/recipe/1234567">タイトル</a>
    # ...
    # という構造のHTMLからから1234567の部分を取得する
    
    # divの取得(個数は3個まで)
    div_list = soup.find_all("div", class_="recipe-title-and-author", limit=limit)

    if div_list is None:
        # detect_pattern.py で、station_exits が見つからなかった場合を解決しているはず
        raise Exception("text not found " + url)
    
    df = pd.DataFrame(columns=["title", "ingredients", "instruction"])
    recipe_urls = []
    for div in div_list:
        title      = div.find("a", class_="recipe-title").get_text(strip=True)
        my_logger.info(f"タイトル: {title}")
        recipe_url = div.find("a", class_="recipe-title").get("href")
        recipe_url = "https://cookpad.com" + recipe_url
        recipe_urls.append(recipe_url)
        
        res_instruction = requests.get(recipe_url)
        soup_instruction = BeautifulSoup(res_instruction.text, "html.parser")
        
        div_instruction_list = soup_instruction.find_all("ol", class_="steps_wrapper", limit=10)
        div_instruction_list = div_instruction_list[0].find_all("p", class_="step_text")
        
        div_ingredients_list = soup_instruction.find_all("div", id="ingredients_list")
        div_ingredients_list = div_ingredients_list[0].find_all("div", class_="ingredient_row")
        
        ingredients_all = ""
        text_all = ""
        
        for div_tmp in div_ingredients_list:
            text = div_tmp.get_text(strip=True)
            ingredients_all = ingredients_all + text + "\n"
        
        
        for div_tmp in div_instruction_list:
            text = div_tmp.get_text(strip=True)
            text_all = text_all + text + "\n"
            
        df_tmp = pd.DataFrame([[title, ingredients_all, text_all]], columns=["title", "ingredients", "instruction"])
        df = pd.concat([df, df_tmp], axis=0)
    
    return df, recipe_urls
    

####################
# test
####################

# if __name__ == "__main__":
#     url = "https://www.livable.co.jp/baikyaku/faq/hiyou.html"

#     df = scrapte_text(url)

#     my_logger.info(df)
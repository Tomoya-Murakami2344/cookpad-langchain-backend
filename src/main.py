import sys

sys.path.append("../")

import constants as C
import openai
from openai import OpenAI
import pandas as pd
import utils
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

args = sys.argv
recipe = args[1]
ingredient = args[2]

"""
このファイルはクックパッドからテキストを取得してデータベースに保存するためのファイルです。
"""

if __name__ == "__main__":
    url1 = "https://cookpad.com/search/" + recipe
    url2 = "https://cookpad.com/search/" + ingredient
    # データの取得
    # cookpad からデータを取得
    df = utils.scrape_text(url1, limit=2)
    df.to_csv(f"../log/{recipe}.csv", index=False)
    df = utils.scrape_text(url2, limit=2)
    df.to_csv(f"../log/{ingredient}.csv", index=False)
    
    # assistant api を使って新しいレシピを生成
    response = utils.create_recipe(recipe, ingredient)
    
    
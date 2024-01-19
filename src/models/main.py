import sys

sys.path.append("../")

import constants as C
import pandas as pd
import models
import database as db
from database import Base, Text
import utils
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

args = sys.argv
url = args[1]

"""
このファイルは東急リバブルのページからテキストを取得してデータベースに保存するためのファイルです。
"""

if __name__ == "__main__":
    # テーブル作成
    db.create_table_if_not_exists(tables=[Text.__table__])
    
    # データの取得
    # 東急リバブルのページからテキストを取得
    df = utils.scrape_text(url)
    
    for i,row in df.iterrows():
        # データの挿入
        row_dict = row.to_dict()
        models.insert(row_dict)
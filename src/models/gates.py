import database as db
from database import Text, Text_with_Embedding
import constants as C
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    UniqueConstraint,
    Float,
    ForeignKey,
)
from geoalchemy2 import Geometry
from log import my_logger


# class Gate(db.Base):
#     @classmethod
def insert(row: dict):
    """
    Insert data into the table.

    Args:
    row (dict): Data to insert.

    Returns:
    None
    """

    # Gate インスタンスを作成
    inserted_instance = Text(
        url=row.get("url"),
        title=row.get("title"),
        text=row.get("text")
    )

    # インスタンスをデータベースセッションに追加
    db.db_session.add(inserted_instance)
    try:
        # コミット
        db.db_session.commit()
    except Exception as e:
        # ロールバック  
        db.db_session.rollback()
        raise e
    
def insert_to_Text_with_Embedding_Table(row: dict):
    """
    Insert data into the Text_with_Embedding_Table.

    Args:
    row (dict): Data to insert.

    Returns:
    None
    """

    # Gate インスタンスを作成
    inserted_instance = Text_with_Embedding(
        url=row.get("url"),
        title=row.get("title"),
        text=row.get("text"),
        embedding=row.get("embedding")
    )

    # インスタンスをデータベースセッションに追加
    db.db_session.add(inserted_instance)
    try:
        # コミット
        db.db_session.commit()
    except Exception as e:
        # ロールバック  
        db.db_session.rollback()
        raise e
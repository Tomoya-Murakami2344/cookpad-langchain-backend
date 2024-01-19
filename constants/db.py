import os

_USER = os.getenv("DB_USER")
_HOST = os.getenv("DB_HOST")
_PASSWORD = os.getenv("DB_PASSWORD")
_PORT = os.getenv("DB_PORT")
_NAME = os.getenv("DB_DATABASE")

DB_URI = f"postgresql://{_USER}:{_PASSWORD}@{_HOST}:{_PORT}/{_NAME}"

# table name
TABLE_NAME = "livable_text"

# pgvector
# ===============================
COLLECTION_NAME = "livable_vectors"
CONNECTION_STRING = DB_URI
# ===============================
import dotenv
dotenv.load_dotenv()
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools.retriever import create_retriever_tool
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_openai import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate)
from typing import List
from langchain.output_parsers import (
    OutputFixingParser,
    PydanticOutputParser,
)
from langchain_core.pydantic_v1 import BaseModel, Field

import utils
import pandas as pd
import os
import time
from main_dev import constructGraph
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

response = {}

# これでユーザーに返す情報のスキーマをコントロールできるはずだが、呼び出される時と呼び出されない時があるので今回は使用しない
# class Response(BaseModel):
#     """ユーザーに返す情報のスキーマ"""
#     title: str = Field(description="あなたが作成したレシピのタイトル")
#     ingredients: List[str] = Field(description="レシピで使用した材料のリスト")
#     instructions: List[str] = Field(description="レシピを作るための手順のリスト")

@app.route("/api/data/<ingredient>/<recipe>", methods=["GET"])
def main(ingredient, recipe):
    # URLの設定
    url1 = "https://cookpad.com/search/" + recipe
    url2 = "https://cookpad.com/search/" + ingredient
    # データの取得
    # cookpad からデータを取得
    df1,recipe_urls1 = utils.scrape_text(url1, limit=1)
    df2,recipe_urls2 = utils.scrape_text(url2, limit=1)
    df = pd.concat([df1, df2])
    
    os.makedirs("log", exist_ok=True)
    df.to_csv(f"./log/{ingredient}.csv", index=False)
    
    # csvファイルの読み込み
    loader = CSVLoader(file_path=f'./log/{ingredient}.csv', csv_args={
        'delimiter': ',',
        'quotechar': '"',
        'fieldnames': ["title","ingredient","instruction"]
    })

    # csvファイルの内容を分割
    data = loader.load()
    documents = RecursiveCharacterTextSplitter(
    chunk_size=100, chunk_overlap=20
    ).split_documents(data)
    # ベクトル化
    vector = FAISS.from_documents(documents, OpenAIEmbeddings())
    retriever = vector.as_retriever()
    # ツールの作成
    retriever_tool = create_retriever_tool(
        retriever,
        "recipe_retriever",
        "Search for information about recipes",
    )

    constructGraph(retriever_tool, ingredient, recipe, response)
    
    response["output"] = f"""
    料理名：{response.get(1)}
    材料：{response.get(2)}
    手順：{response.get(3)}
    """
    response.pop(1)
    response.pop(2)
    response.pop(3)

    try:
        data = {
            "content": response["output"],
            "urls": {
                "recipes": recipe_urls1,
                "ingredients": recipe_urls2
            }
        }
    except:
        data = {
            "content": None,
            "urls": {
                "recipes": recipe_urls1,
                "ingredients": recipe_urls2
            }
        }
    
    return jsonify(data)

keyValue = {1: "recipeName", 2: "ingredients", 3: "procedures"}
@app.route("/api/data/<ingredient>/<recipe>/<int:task_number>", methods=["GET"])
def getRecipeName(ingredient, recipe, task_number):
    # 途中経過の取得
    start = time.time()
    while(time.time() - start < 120):
        if response.get(task_number) is not None:
            try:
                print(response.get(task_number),f"==========={task_number}============")
                # response のtask_numberに対応する値を削除
                value = response.get(task_number)
                return jsonify({keyValue.get(task_number): value})
            except:
                print(response.get(task_number),f"==========={task_number}============")
                return jsonify({keyValue.get(task_number): None})

        else:
            time.sleep(5)
    
if __name__ == "__main__" and os.getenv("DEBUG") == "True":
    app.run(debug=os.getenv("DEBUG"))
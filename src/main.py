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
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
    # ツールの登録
    tools = [retriever_tool]
    # チャットモデルの作成
    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)
    llm_with_tools = llm.bind_functions([retriever_tool])
    # プロンプトの設定
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
                "ツールを使って既存のレシピを参照し、今までにない新しいレシピを作成してください。必ず、材料{ingredient}を使って料理{recipe}の作り方を教えてください。\
                以下のフォーマットに従って回答してください。{format_instructions} \
                出力フォーマット以外の情報は不要です。",
            ),
            ("user",
                "{ingredient}を使った誰も食べたことのない{recipe}のレシピを教えてください。"
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    
    agent = (
        {
            "ingredient": lambda x: x["ingredient"],
            "recipe": lambda x: x["recipe"],
            "format_instructions": lambda x: '''
            料理名：~ 
            材料：
            1. ~
            2. ~
            3. ~
            手順：
            1. ~
            2. ~
            3. ~
            ''',
            # Format agent scratchpad from intermediate steps
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | utils.parse
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[retriever_tool],
        verbose=True,
    )
    response = agent_executor.invoke(
        {"ingredient": ingredient, "recipe": recipe},
        return_only_outputs=True
    )
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
    
if __name__ == "__main__":
    app.run(debug=True)
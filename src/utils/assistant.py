import openai
from openai import OpenAI

client = OpenAI()

# 定数の設定
name = 'マンション価格の定性的分析'
instructions = '''あなたは今までにない新しいレシピを作成するアシスタントです。料理名Aと材料Bが与えられるので、与えられた2つのcsvファイルの調理方法を真似してBを使った料理Aの作り方を創作してください。

データのカラム説明：
title : 料理名
instruction : 料理の作り方

出力フォーマット：
title : 料理名
instruction : 料理の作り方

出力フォーマット以外の情報は不要です。日本語で回答してください。
'''
def create_recipe(recipe,ingredient):
    file_recipes = client.files.create(file=open(f'../log/{recipe}.csv',"rb"), purpose='assistants')
    file_ingredients = client.files.create(file=open(f'../log/{ingredient}.csv',"rb"), purpose='assistants')
    
    assistant = client.beta.assistants.create(
    name=name,
    instructions=instructions,
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-1106-preview"
    # "gpt-3.5-turbo"
    # "gpt-4-1106-preview"
    # file_ids=[file_prices.id],これはあとでスレッドを作るときに使う
    )
    thread_1 = client.beta.threads.create()
    ask(assistant.id, thread_1.id, f"{ingredient}を使った{recipe}の作り方を教えてください。", file_ids=[file_recipes.id, file_ingredients.id])
    

# 関数の定義
import time
import datetime
import os
def wait_run(thread_id: str, run_id: str):
    # run の retrieve を取得
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

    print(f"run : {run.status}")

    # run の status が queued または in_progress なら 5 秒まって再帰的に呼び出す
    if run.status == "queued" or run.status == "in_progress":
        time.sleep(15)
        return wait_run(thread_id, run_id)

    return run

def ask(assistant_id: str, thread_id: str, question: str, file_ids: list = []):
    ask_date = datetime.datetime.now().strftime("%Y-%m-%d")
                                                #%H:%M:%S")
    ask_output_dir = f"../log/{ask_date}"
    # 
    ask_timestamp = datetime.datetime.now().timestamp()

    os.makedirs(ask_output_dir, exist_ok=True)
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question,
        file_ids=file_ids,
    )
    print(f"Q: {message.content}")
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    print("run : created")
    run = wait_run(thread_id, run.id)
    
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc")
    
    for row in messages:
        for c in row.content:
            if c.type == "text":
                with open(f"{ask_output_dir}/{ask_timestamp}.txt", "a") as f:
                    f.write(f"{c.text.value}\n")
            elif c.type == "image_file":
                file_id = c.image_file.file_id

                file = client.files.content(file_id=file_id)

                with open(f"{ask_output_dir}/{file_id}.png", "wb") as f:
                    f.write(file.content)

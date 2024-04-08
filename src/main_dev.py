import os
import dotenv
dotenv.load_dotenv()

from typing import Annotated, List, Tuple, Union

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

import operator
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
import functools

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END

"""_summary_
このファイルはLangGraph(https://python.langchain.com/docs/langgraph)を使って
与えられた食材、料理名に対してその食材を使った料理のレシピをChatGPTを使って生成するプログラムである。
流れは以下の通りである。
1. 食材、料理名を受け取る
2. その食材を使ったレシピのレシピ名を生成する
3. そのレシピの材料を生成する
4. そのレシピの手順を生成する
"""

def create_agent(tools: list, system_prompt: str):
    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)
    # Each worker node will be given a name and some tools.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor

def agent_node(state, agent, name):
    # stateのmessagesに task {task_number}のみを実行するように指示する文章を追加する
    state["messages"].append(HumanMessage(content=f"タスク{state['task_number']}のみを実行してください。"))
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)], "task_number":state['task_number']}

# ============== Create Agent Supervisors ==============
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

members = ["recipeAssistant"]
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers:  {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = ["FINISH"] + members
# Using openai function calling can make output parsing easier for us
function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": options},
                ],
            },
            "task_number": {
                "title": "Task to be performed",
                "type": "integer",
            },
        },
        "required": ["next"],
    },
}
def supervisorNode(state):
    task_number = state["task_number"]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                f"Given the conversation above, up to task {task_number} has been completed."
                f"If only {task_number} equals 3, you can select FINISH. Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)

    supervisor_chain = (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )
    response = supervisor_chain.invoke(state)
    return response

# ================== Construct Graph ==================
# The agent state is the input to each node in the graph
class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str
    # Task number to be performed
    task_number: str
    
def constructGraph(tool, ingredient, recipe, response):
    assistantAgent = create_agent([tool], 
        """
        あなたは以下のタスクのうちのいずれかを実行するように指示されます。
        1. ある食材Aを使った料理Bのレシピの名前のみを生成する
        2. ある食材Aを使った料理Bのレシピの材料を生成する。以下のフォーマットに従って回答してください。
            1. ~
            2. ~
            3. ~
        3. ある食材Aを使った料理Bのレシピの手順を生成する。以下のフォーマットに従って回答してください。
            1. ~
            2. ~
            3. ~
        4. FINISH
        """
    )
    assistantNode = functools.partial(agent_node, agent=assistantAgent, name="recipeAssistant")
    
    workflow = StateGraph(AgentState)
    workflow.add_node("recipeAssistant", assistantNode)
    workflow.add_node("supervisor", supervisorNode)
    
    workflow.add_edge("recipeAssistant", "supervisor")
    # The supervisor populates the "next" field in the graph state
    # which routes to a node or finishes
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    
    # Finally, add entrypoint
    workflow.set_entry_point("supervisor")

    graph = workflow.compile()
    
    for s in graph.stream(
        {"messages": [HumanMessage(content=f"""
        食材{ingredient}を使った料理{recipe}で、新しいレシピを作成してください。
        タスクの流れは以下の通りです。
        1. 食材{ingredient}を使った料理{recipe}のレシピの名前のみを生成する
        2. 食材{ingredient}を使った料理{recipe}のレシピの材料を生成する
        3. 食材{ingredient}を使った料理{recipe}のレシピの手順を生成する
                    """)],
         "task_number": 0
        },
        {"recursion_limit": 100},
    ):
        if "__end__" not in s:
            print(s)
            if "recipeAssistant" in s:
                task_number = s["recipeAssistant"]["task_number"]
                response[task_number] = s["recipeAssistant"]["messages"][0].content
            print("----")
            

# ============== Main ==============
import utils
import pandas as pd
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS

if __name__ == "__main__":
    recipe = "カレーライス"
    ingredient = "アンチョビ"
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
    response = {}
    constructGraph(retriever_tool, ingredient, recipe, response)
    print(response)
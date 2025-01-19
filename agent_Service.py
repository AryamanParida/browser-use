from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import sys
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import SecretStr
import chromadb
# from sentence_transformers import SentenceTransformer
import uuid
from screeninfo import get_monitors
from playwright.async_api import async_playwright
from playwright._impl._api_structures import ProxySettings

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
import uvicorn

app = FastAPI()

# Getting the primary monitor's width and height for the browser full screen
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height

chroma_client = chromadb.Client()
# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

task_memory_collection = chroma_client.get_or_create_collection(name="task_memory")

key = os.getenv("key", "")
print(key)
OPENAPI_KEY = SecretStr(key)
llm = ChatOpenAI(model='gpt-4o', temperature=0.0, api_key=OPENAPI_KEY)

class TaskRequest(BaseModel):
    task: str

# def save_behavior_chroma(desc, corrected_behavior):
#     unique_id = str(uuid.uuid4())
#     # embedding = embedding_model.encode(desc).tolist()
#     task_memory_collection.add(
#         documents=[desc],
#         embeddings=[embedding],
#         metadatas=[{"corrected_behavior": corrected_behavior}],
#         ids=[unique_id]
#     )
#     print("Behavior saved to ChromaDB.")

# def find_similar_task_chroma(task_description, threshold=0.8):
#     # embedding = embedding_model.encode(task_description).tolist()
#     results = task_memory_collection.query(
#         query_embeddings=[embedding],
#         n_results=1
#     )
#     if results is None or not results["documents"]:
#         return None, None
#     else:
#         if results["distances"] is not None and results["metadatas"] is not None and len(results["distances"]) > 0 and len(results["distances"][0]) > 0:
#             similarity_score = results["distances"][0][0]
#             if similarity_score <= (1 - threshold):
#                 metadata = results["metadatas"][0]
#                 if isinstance(metadata, dict):
#                     if "corrected_behavior" in metadata:
#                         return results["documents"][0], metadata.get("corrected_behavior")
#                 else:
#                     raise TypeError(f"Expected metadata to be a dictionary, got {type(metadata)}")
#     return None, None

async def execute_task():
    # cfg = BrowserConfig(proxy=ProxySettings(
    #     server="http://localhost:8082",
    # ))
    # browser = Browser(cfg)
    browser = Browser()
    updated_task = f'''
    1) Navigate to this url https://supplier-stg.stg.meeshogcp.in/panel/v3/new/growth/xl2jo/home
    2) Login using following username: testadmin01@gmail.com and password: Meesho@123
    3) Crawl the current web page and save it in text format
    '''
    # updated_task = f'''
    # 1) Navigate http://model-metastore.meeshogcp.in/swagger-ui.html?url=https://jumpy-floor.surge.sh/test.yaml and extract page as markdown
    # '''

    # similar_task, corrected_behavior = find_similar_task_chroma(task)
    # if corrected_behavior:
    #     print(f"Found similar task: {similar_task}")
    #     print(f"Using learned behavior: {corrected_behavior}")
    #     updated_task = f"""
    #     Based on prior knowledge, the corrected way to perform this task is:
    #     {corrected_behavior}
    #     Please follow this and complete the task: {task}
    #     """

    async with await browser.new_context(
        config=BrowserContextConfig(
            trace_path="./tmp/traces/",
            cookies_file="/Users/aryamanparida/AI PROJECTS/Lang graph/cookie.json",
            browser_window_size={
                'width': screen_width,
                'height': screen_height,
            },
        ),
    ) as context:
        agent = Agent(
            task=updated_task,
            llm=llm,
            use_vision=False,
            browser_context=context,
            save_conversation_path="./save",
            max_failures=3,
            browser=browser
        )

        await agent.run()

    # await browser.close()
# task_request: TaskRequest
@app.get("/execute-task")
async def execute_task_endpoint():
    try:
        # task_request.task="Go to x.com"
        # await execute_task(task_request.task)
        resp=await execute_task()
        # return {"message": "Task executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
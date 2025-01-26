from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import sys
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import SecretStr
import chromadb
from screeninfo import get_monitors
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import html2text
import uvicorn

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

app = FastAPI()

# Getting the primary monitor's width and height for the browser full screen
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height

chroma_client = chromadb.Client()
task_memory_collection = chroma_client.get_or_create_collection(name="task_memory")

key = os.getenv("key", "")
OPENAPI_KEY = SecretStr(key)
llm = ChatOpenAI(model='gpt-4o', temperature=0.0, api_key=OPENAPI_KEY)
# llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0, api_key=OPENAPI_KEY)

global_context = None
global_agent = None 
def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    for tag in soup.find_all(style=True):
        del tag['style']

    for style_tag in soup.find_all('style'):
        style_tag.decompose()

    for script_tag in soup.find_all('script'):
        script_tag.decompose()

    for link_tag in soup.find_all('link', rel='stylesheet'):
        link_tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()

    for tag in soup.find_all():
        for attr in ['aria-', 'role', 'class', 'id']:
            if attr in tag.attrs:
                del tag[attr]

    for div in soup.find_all('div'):
        if div.get_text(strip=True).isdigit(): 
            div.decompose()
        elif not div.get_text(strip=True):  
            div.decompose()

    for svg in soup.find_all('svg'):
        svg.decompose()

    return soup.prettify()

def html_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False  
    h.ignore_images = False  
    markdown = h.handle(html_content)
    return markdown

class TaskRequest(BaseModel):
    task: str
    use_global_context: bool 

async def execute_task(task: str, use_global_context: bool):
    global global_context
    browser = Browser()
    print("task")
    print(task)
    if use_global_context and global_context is not None:
        context = global_context
    else:
        context = await browser.new_context(
            config=BrowserContextConfig(
                trace_path="./tmp/traces/",
                cookies_file="/Users/aryamanparida/AI PROJECTS/Lang graph/cookie.json",
                browser_window_size={
                    'width': screen_width,
                    'height': screen_height,
                },
            ),
        )
        if use_global_context:
            global_context = context

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=False,
        browser_context=context,
        save_conversation_path="./save",
        max_failures=3,
        browser=browser,
    )

    await agent.run()
    current_html = agent.get_current_html()
    with open("a1.html","w") as f:
        f.write(current_html)
    browser_context = agent.browser_context

    dialog_box=browser_context.dialog_info
    for dialog_data in browser_context.dialog_info:
        if dialog_data['exists']:
            print(f"Dialog detected at {dialog_data['url']}: {dialog_data['message']}")
    agent_task_status=agent.task_completed
    eval_prev_goal=agent.eval
    memory=agent.memory
    next_goal=agent.next_goal
    if agent_task_status:
        if current_html:
            cleaned_html = clean_html(current_html)
            markdown_content = html_to_markdown(cleaned_html)
            return {
                "html_content": cleaned_html,
                "markdown_content": markdown_content,
                "dialog_box":dialog_box,
                "success": True,
                "eval_prev_goal":eval_prev_goal,
                "memory":memory,
                "next_goal":next_goal,
                "message": "Task completed successfully",
            }
    else:
        return {
            "html_content": "NO HTML CONTENT FOUND" ,
            "markdown_content": "NO MARKDOWN CONTENT",
            "success": False,
            "dialog_box":dialog_box,
            "message": "Task not completed successfully",
            "eval_prev_goal":eval_prev_goal,
            "memory":memory,
            "next_goal":next_goal,
        }

@app.post("/execute-task")
async def execute_task_endpoint(task_request: TaskRequest):
    try:
        result = await execute_task(task_request.task, task_request.use_global_context)
        agent_brain=result["agent_brain"]
        eval1=""
        memory1=""
        nextgoal1=""
        print("agent_brain")
        print(agent_brain.__dict__)
        # if agent_brain is not None:
        #     eval1=agent_brain.current_state.evaluation_previous_goal
        #     memory1=agent_brain.current_state.memory
            # nextgoal1=agent_brain.current_state.next_goal
        if result["success"]:
            return {
                "message": "Task executed successfully",
                "html_content": result["html_content"],
                "markdown_content": result["markdown_content"],
                "dialog_box":result["dialog_box"],
                "eval":result["eval_prev_goal"],
                "memory":result["memory"],
                "next_goal":result["next_goal"],
                "success": True,
            }
        else:
            return {
                "message": result["message"],
                "success": False,
                "html_content": result["html_content"],
                "markdown_content": result["markdown_content"],
                "dialog_box":result["dialog_box"],
                "eval":result["eval_prev_goal"],
                "memory":result["memory"],
                "next_goal":result["next_goal"],
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
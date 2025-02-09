# app/services/task_service.py
from app.core.config import settings
from langchain_openai import ChatOpenAI
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from playwright._impl._api_structures import ProxySettings
from app.core.utils import clean_html,html_to_markdown
import os

global_context = None
agent = None
proxy = ProxySettings(server=settings.PROXY_URL)

llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.0, api_key=settings.OPENAPI_KEY)

async def execute_task(task: str, use_global_context: bool):
    global global_context, agent

    browser_config = BrowserConfig(proxy=proxy)
    browser = Browser(config=browser_config)

    if use_global_context and global_context:
        context = global_context
    else:
        context = await browser.new_context(
            config=BrowserContextConfig(
                trace_path="./tmp/traces/",
                browser_window_size={'width': 1920, 'height': 1080},
            )
        )
        if use_global_context:
            global_context = context

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=False,
        browser_context=context,
        # save_conversation_path="./save",
        max_failures=3,
        browser=browser,
    )

    await agent.run(5)
    current_html = agent.get_current_html()
    with open("current.html","w") as f:
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
                "eval":eval_prev_goal,
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
            "eval":eval_prev_goal,
            "memory":memory,
            "next_goal":next_goal,
        }

async def get_current_page():
    global agent
    if agent is None:
        return {
            "success":False,
            "msg": "No agent found",
            "current_web_page": "",
            "current_markdown": ""
        }
    else:
        current_html = agent.get_current_html()
        if current_html: 
            with open("current.html", "w") as f:
                f.write(current_html)
            
            cleaned_html = clean_html(current_html)
            markdown_content = html_to_markdown(cleaned_html)
            return {
                "success":True,
                "msg": "Agent and current HTML found",
                "current_web_page": cleaned_html,
                "current_markdown": markdown_content
            }
        else:
            return {
                "success":False,
                "msg": "Agent found but no current HTML found",
                "current_web_page": "",
                "current_markdown": ""
            }

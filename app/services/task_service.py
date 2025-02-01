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
global_agent = None
proxy = ProxySettings(server=settings.PROXY_URL)

llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.0, api_key=settings.OPENAPI_KEY)

async def execute_task(task: str, use_global_context: bool):
    global global_context, global_agent

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
    
    if current_html:
        cleaned_html = clean_html(current_html)
        markdown_content = html_to_markdown(cleaned_html)
        return {
            "html_content": cleaned_html,
            "markdown_content": markdown_content,
            "success": True,
            "message": "Task completed successfully",
        }
    else:
        return {
            "html_content": "NO HTML CONTENT FOUND",
            "markdown_content": "NO MARKDOWN CONTENT",
            "success": False,
            "message": "Task not completed successfully",
        }

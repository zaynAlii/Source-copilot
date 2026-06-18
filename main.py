from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.messages import AIMessage , AIMessageChunk ,HumanMessage , ToolCall ,ToolCallChunk ,ToolMessage  , SystemMessage
from langgraph.graph.message import BaseMessage , REMOVE_ALL_MESSAGES , RemoveMessage
from crawl4ai import AsyncWebCrawler , BrowserConfig , CrawlerRunConfig  , PruningContentFilter , CrawlResult #type:ignore
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator #type:ignore
import re
from typing import Optional
from langchain.agents.middleware import AgentMiddleware , before_agent , before_model , after_model , after_agent , AgentState , SummarizationMiddleware
from langgraph.runtime import Runtime 
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
import os 

import tempfile
from pathlib import Path
import asyncio
import aiofiles #type:ignore
import yt_dlp #type:ignore
from faster_whisper import WhisperModel  #type:ignore
import chainlit as cl 


base_url = "http://localhost:11434"
chat_model = ChatOllama(
    base_url=base_url,
    model="gemma4:e4b-it-q4_K_M",
    reasoning=True
)

summarizer_model=ChatOllama(
    base_url=base_url,
    model="gemma4:e4b-it-q4_K_M",
    reasoning=True
)

@tool
async def Crawl_website(url: str) -> str:
    """Extracts the core text content of a webpage as clean Markdown.
    
    Use this tool whenever the user provides a URL or asks you to read, analyze, 
    summarize, or answer questions about a specific website. 
    
    This tool automatically filters out website clutter like navigation bars, ads, 
    sidebars, and footer links, returning only the primary reading material.

    Args:
        url (str): The full, valid web address to crawl (e.g., 'https://example.com').

    Returns:
        str: The cleaned, essential markdown text of the webpage, or an error message.
    """
    
    runconfig=CrawlerRunConfig(
      markdown_generator=DefaultMarkdownGenerator(
          content_filter=PruningContentFilter(
              threshold=0.5
          ),
          options={"ignore_links": True}
      )
      ,
      delay_before_return_html=3.0,
      scan_full_page=True,
      scroll_delay=0.5
    )
    
    async with AsyncWebCrawler() as crawler:
        result:CrawlResult = await crawler.arun(
            url=url,
            config=runconfig
        )
        if result.success:
            return result.markdown.fit_markdown
        else :
            print(f"Crawling failed: {result.error_message}")    
            return f"Crawling failed: {result.error_message}"
    




# ============================================================
# Helpers
# ============================================================

def _normalize_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s]", "", text.lower())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _merge_overlap(previous: str, current: str) -> str:
    """
    Removes duplicated overlap between consecutive subtitle lines.

    Example:
        prev: "hello everyone"
        curr: "everyone welcome back"

    Returns:
        "welcome back"
    """

    prev_words = _normalize_text(previous).split()
    curr_words = _normalize_text(current).split()

    if not prev_words or not curr_words:
        return current

    max_overlap = min(len(prev_words), len(curr_words))

    for i in range(max_overlap, 0, -1):
        if prev_words[-i:] == curr_words[:i]:
            original_words = current.split()
            return " ".join(original_words[i:])

    return current


# ============================================================
# Subtitle Discovery
# ============================================================

async def _get_best_subtitle_languages(video_url: str) -> list[str]:
    """
    Discover available subtitle languages and choose the best one.
    """

    options = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    def run():
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(video_url, download=False)

    info = await asyncio.to_thread(run)

    manual_subs = info.get("subtitles", {}) or {}
    auto_subs = info.get("automatic_captions", {}) or {}

    available = set(manual_subs.keys()) | set(auto_subs.keys())

    if not available:
        return []

    preferred_languages = [
        "en",
        "en-US",
        "en-GB",
        "hi",
        "ur",
    ]

    for lang in preferred_languages:
        if lang in available:
            return [lang]

    return [next(iter(available))]


# ============================================================
# Subtitle Download
# ============================================================

async def _try_download_subtitle(
    video_url: str,
    temp_dir: str,
) -> Optional[str]:

    subtitle_langs = await _get_best_subtitle_languages(video_url)

    if not subtitle_langs:
        return None

    options = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": subtitle_langs,
        "subtitlesformat": "vtt",
        "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    def run():
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])

    await asyncio.to_thread(run)

    vtt_files = list(Path(temp_dir).rglob("*.vtt"))

    if vtt_files:
        return str(vtt_files[0])

    return None


# ============================================================
# VTT Cleaning
# ============================================================

async def _clean_vtt(subtitle_file: str) -> str:
    transcript: list[str] = []

    previous_text = ""

    async with aiofiles.open(
        subtitle_file,
        mode="r",
        encoding="utf-8",
        errors="ignore",
    ) as f:

        async for raw_line in f:

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("WEBVTT"):
                continue

            if line.startswith("Kind:"):
                continue

            if line.startswith("Language:"):
                continue

            if "-->" in line:
                continue

            if re.match(r"^\d+$", line):
                continue

            # remove all VTT html tags
            line = re.sub(r"<[^>]+>", "", line)

            line = line.strip()

            if not line:
                continue

            if previous_text:
                cleaned = _merge_overlap(previous_text, line)

                if cleaned:
                    transcript.append(cleaned)
            else:
                transcript.append(line)

            previous_text = line

    final_text = " ".join(transcript)

    final_text = re.sub(r"\s+", " ", final_text)

    return final_text.strip()


# ============================================================
# Main Tool
# ============================================================

@tool
async def youtube_transcript_extractor(url: str) -> str:
    """
    Extract transcript from YouTube subtitles.

    Strategy:
        1. Manual subtitles
        2. Auto-generated subtitles
        3. (Optional future fallback) Whisper

    Returns:
        Transcript text
    """

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            subtitle_file = await _try_download_subtitle(
                url,
                temp_dir,
            )

            if not subtitle_file:
                return (
                    "No subtitles or automatic captions "
                    "were available for this video."
                )

            transcript = await _clean_vtt(subtitle_file)

            if not transcript.strip():
                return (
                    "Subtitle file was downloaded but "
                    "contained no usable text."
                )

            return f"""
Source: YouTube Subtitles

Transcript:
{transcript}
"""

    except Exception as exc:
        return f"Transcript extraction failed: {str(exc)}"

      
        

def get_system_prompt():
    # async with aiofiles.open("./Agent.md" ,mode="r" , encoding="utf-8") as f:
    with open("./Agent.md" ,mode="r" , encoding="utf-8") as f:
         prompt= f.read()
    
    return prompt      

SYSTEM_PROMPT=get_system_prompt()
        

        
agent = create_agent(chat_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[Crawl_website , youtube_transcript_extractor],
        # middleware=[SummarizationMiddleware(
        #     model=summarizer_model,
        #     trigger=("fraction", 0.7),
        #     keep=("fraction", 0.2),
        #     trim_tokens_to_summarize=12000
        #     )],
        checkpointer=InMemorySaver()
    )

config:RunnableConfig={"configurable": {"thread_id": "thread_123"}}




@cl.on_message
async def user_Prompting(msg:cl.Message):
    user_input= msg.content
    
    msg=cl.Message(content="")
    
    reasoning_step=cl.Step(name="Reasoning" , type="llm")
    await reasoning_step.send()
    # 
    
    async for token_chunk in agent.astream(
            {"messages":[HumanMessage(content=user_input)]} , stream_mode=["messages","updates"] , version="v2"  ,config=config )  :
            if token_chunk["type"]=="messages":
                # print("Hello")
                data=token_chunk["data"][0]
                if isinstance(data , AIMessageChunk):
                    if data.content:
                        await  msg.stream_token(data.content) #type:ignore
                        # print(f"{data.content}" , end="" , flush=True)
                    elif data.additional_kwargs.get("reasoning_content"):
                        await reasoning_step.stream_token(data.additional_kwargs['reasoning_content'])
                        # print(f"{data.additional_kwargs['reasoning_content']}" , end="" , flush=True)
                    elif data.tool_calls:
                        for tool_call in data.tool_calls:            
                            async with cl.Step(name=f"Tool: {tool_call["name"]}" , type="tool") as tool_step:
                                tool_step.input=tool_call["args"]
                                await tool_step.stream_token(f"Executing {tool_call['name']} with args: {tool_call['args']}...")    
                                   



# if __name__ == "__main__":
#   async def main():
#     #   messages_:list[BaseMessage]=[]    #type:ignore
#       while True: 
#         print("\n")  
#         user_input = input("User: ")
#         if user_input.lower() in ["exit", "quit"]:
#             print("Exiting...")
#             break
#         # messages_.append(HumanMessage(content=user_input))
#         async for token_chunk in agent.astream(
#             {"messages":[HumanMessage(content=user_input)]} , stream_mode=["messages","updates"] , version="v2"  ,config=config )  :
#             if token_chunk["type"]=="messages":
#                 # print("Hello")
#                 data=token_chunk["data"][0]
#                 if isinstance(data , AIMessageChunk):
#                     if data.content:
#                         print(f"{data.content}" , end="" , flush=True)
#                     elif data.additional_kwargs.get("reasoning_content"):
#                         print(f"{data.additional_kwargs['reasoning_content']}" , end="" , flush=True)
#                     elif data.tool_calls:
#                         for tool_call in data.tool_calls:            
#                             print(f"\nTool name: {tool_call['name']}\n" , end="" , flush=True)   
#                             print(f"Tool args: {tool_call['args']}\n" , end="" , flush=True)   
      
          
        
    
#   import asyncio
#   asyncio.run(main())  
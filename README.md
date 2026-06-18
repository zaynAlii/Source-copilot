# Source-copilot

An intelligent AI agent that can extract, understand, and reason over content from any webpage or YouTube video.

Instead of forcing users to manually read long content, this agent ingests web pages or videos, converts them into LLM-readable text, and allows users to interact with the content naturally through multi-turn conversation.

Users can ask for summaries, explanations, learning roadmaps, prerequisite knowledge, outlines, deep technical breakdowns, and unlimited follow-up questions grounded in the extracted source.

---

## Overview

Large Language Models are powerful, but most assistants answer questions without deeply understanding external content.

This project solves that problem by building an agent that can first ingest external content and then reason over that content as if it has studied the source.

The agent works on:

* Any webpage
* Documentation websites
* Blog posts
* Technical tutorials
* Research papers published on websites
* Educational websites
* Online guides
* Knowledge bases
* YouTube videos

Once the source is processed, the user can continuously interact with that content through conversation.



---
## Tech Stack used:
   - Python
   - Langchain agent sdk
   - Yt-dlp
   - crawl4ai
   - chainlit
   - Asyncio
   - Inmemory persistance

---




---

## Core Idea

Instead of:

```text id="yrhm9l"
User → Ask question → LLM answers from general knowledge
```

This project works as:

```text id="mfekjo"
User → Provide source → Agent extracts content → LLM reasons over extracted content → User asks unlimited follow-up questions
```

The source becomes the knowledge base for the conversation.

---

## Features

### Universal Web Scraping

Users can provide almost any webpage URL.

The agent automatically:

* Crawls webpage content
* Removes unnecessary HTML and noise
* Extracts useful content
* Converts extracted content into clean LLM-ready markdown
* Uses extracted content for reasoning

Supported content includes:

* Documentation pages
* Tutorials
* Blogs
* Research content
* Technical guides
* Public websites
* Educational resources

Example:

```text id="4j95d4"
https://docs.example.com
```

---

### YouTube Video Understanding

Users can provide YouTube video URLs.

The agent automatically:

* Extracts subtitles/transcripts
* Uses transcript as reasoning context
* Supports deep interaction with video content

Example:

```text id="k6hx2g"
https://youtube.com/watch?v=...
```

---

### Multi-turn Contextual Conversations

After processing source content, users can continue asking unlimited follow-up questions.

Example:

```text id="l32mop"
User: Summarize this content

User: Teach me step by step

User: Create a roadmap for learning this topic

User: Explain this section deeply

User: I do not understand this concept

User: What prerequisites do I need first?
```

The agent continues reasoning around previously extracted content.

---

### Learning Assistant Mode

The agent helps users learn difficult content instead of just answering questions.

Capabilities:

* Summarization
* Deep explanation
* Step-by-step teaching
* Concept breakdown
* Beginner-friendly explanations
* Technical explanations

---

### Prerequisite Detection

If the content is difficult, the agent identifies missing foundational knowledge.

Example:

```text id="x9r8ix"
I find this difficult to understand
```

Example response:

```text id="v2wz8k"
Before understanding LangGraph persistence, first learn:

- State management
- Checkpointing
- Serialization
- Graph execution flow
```

---

### Source Grounded Reasoning

The agent prioritizes extracted source content over general model knowledge.

Benefits:

* Reduced hallucination
* Better reliability
* Source-aware answers
* Better technical accuracy

---

## Tech Stack

Built using:

* Python
* LangChain
* Ollama
* yt-dlp
* Async Python
* Local LLMs

---

## System Architecture

```text id="rj3el3"
                     User Input
                         │
                         │
                         ▼
                  Detect Input Type
                         │
         ┌───────────────┴────────────────┐
         │                                │
         │                                │
         ▼                                ▼
   Website URL                      YouTube URL
         │                                │
         ▼                                ▼
  Crawl_website Tool          youtube_transcript_extractor
         │                                │
         ▼                                ▼
 Extract Raw Content              Extract Transcript
         │                                │
         ▼                                ▼
 Clean + Convert                 Clean Transcript
         │                                │
         └───────────────┬────────────────┘
                         │
                         ▼
                  Inject Into Agent
                         │
                         ▼
                   LLM Reasoning
                         │
                         ▼
              Multi-turn Conversation
```

---

## Available Tools

### Crawl_website

Responsible for:

* Crawling web pages
* Extracting webpage content
* Removing HTML noise
* Returning clean markdown

---

### youtube_transcript_extractor

Responsible for:

* Extracting YouTube subtitles
* Downloading transcript data
* Cleaning transcript text
* Returning transcript for reasoning

---

## Example Use Cases

### Learn Documentation

```text id="jlwmdd"
Read this documentation page and teach me step by step
```

---

### Understand Technical Blogs

```text id="h7c0c4"
Summarize this blog and explain important concepts
```

---

### Learn From YouTube Videos

```text id="t2ozvc"
Watch this video and create a learning roadmap
```

---

### Deep Technical Understanding

```text id="a11xd0"
Explain the concepts discussed here in simple language
```

---

### Find Missing Foundations

```text id="7yemx2"
I find this difficult. Figure out what I need to learn first
```

---

### Structured Learning

```text id="ufb6p8"
Create an outline and teach me this topic in order
```

---

## Future Improvements

Planned upgrades:

* Persistent conversation memory
* Vector database retrieval
* PDF ingestion support
* Whisper fallback for videos without subtitles
* Multi-source comparison mode
* Better subtitle cleaning pipeline
* Source citation support
* Support for uploaded documents

---

## Engineering Concepts Used

This project helped me practice:

* Agent tool calling
* Multi-turn reasoning
* System prompt engineering
* Async Python
* Web scraping 
* Transcript extraction
* Tool orchestration
* Source grounded reasoning


---

## Why I Built This

Reading long technical content can be slow and difficult.

People often want to:

* Learn documentation faster
* Understand difficult technical topics
* Ask follow-up questions around content
* Break complex topics into learning steps

This project turns passive content consumption into an interactive learning experience.

Instead of reading alone…

Users can learn through conversation.

---

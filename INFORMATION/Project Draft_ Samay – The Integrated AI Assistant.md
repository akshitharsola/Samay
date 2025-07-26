<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Project Draft: Samay – The Integrated AI Assistant

## Overview

**Samay** is a custom-built, locally-integrated AI assistant designed for MacBook Air M2, focused on privacy, multi-model orchestration, and delivering high-quality research, coding, and productivity support. Its architecture unites best-in-class public assistants (Claude Pro, Gemini Pro, Perplexity Pro) with private local LLMs, optimized for both day-to-day and confidential workflows.

## Project Areas \& Scope

### 1. Multi-Agent Orchestration

- Route user input concurrently to Gemini, Claude, and Perplexity.
- Aggregate, validate, and present the best combination of responses.
- Provide a single, unified user workflow—no need to switch between services.


### 2. Local LLM Integration

- Host open-weight Hugging Face LLMs (e.g., Phi-3 Mini, Gemma) for fully private or offline tasks.
- Automatically enforce private processing for confidential files or research papers.


### 3. Research-First Design

- Deep research workflows: structured summarization, automated citation, and report aggregation.
- Support for medium and large-length prompts, adapting context window strategy as needed.


### 4. Modular and Extensible

- Basic UI (desktop app) for launching and controlling all workflows and logins.
- Future-proof for extension with audio, image, video, and IoT/smart device features.


## Project Goals

- **Quality Over Speed:** Ensure the best factual, cited, and structured outputs even at the cost of latency.
- **Privacy by Default:** Local file handling and LLM usage for confidential tasks; never transmit private data to the cloud.
- **Maximum User Control:** Manual override for output review, validation steps, retries, and workflow branching.
- **Unified Long-Term Memory:** Seamless retrieval of prior research, session history, preferences, and local knowledge base.
- **Effortless Integration:** Native browser-based login to all key assistants—no API development or key management for users.


## Samay Will Provide

- Single-login, high-control interface for Claude, Gemini, and Perplexity.
- Parallel prompt dispatch: submit once, get a multi-perspective answer.
- Output validation (checklists, citation presence, completeness), with auto-retry.
- Aggregated markdown/PDF reporting, with sections labeled by assistant/source.
- Manual checkpoints for review, edits, or re-prompting at every step.
- Memory-efficient document chunking for large inputs and research papers.
- Secure file/workspace management using the Mac’s available 95GB storage.
- Modular addition of personal/local LLMs for offline or privacy-centered tasks.


## Features Discussed \& Confirmed

- Multi-modal research intake: accept plain text, uploaded research articles, dataset files.
- Distinct workflows for coding, research, general productivity, or documentation.
- Confidential mode automatically directed to local models.
- Live monitoring and logging of workflow progress, validation status, and retries.
- Storage separation: structured directories for models, logs, reports, memory DB.


## How to Build

### Environment Preparation

- VSCode for development, Node.js, Python (Anaconda), Playwright for browser automation.
- Use Electron or Tauri for desktop app UI; Playwright for login/session handling via browser (no APIs or raw keys).
- Set up folders for models, memory, user data, logs, and workspace organization.


### Core Steps

1. **UI and Integration Foundation**
    - Create a basic desktop app that enables login to all services via browser.
    - Test and confirm session storage works for all accounts and can be reused.
2. **Parallel Prompt Orchestration**
    - Build scripts to send the same query or file to each assistant; collect responses.
    - Implement validation and auto-retry against custom checklists.
3. **Output Processing and Memory Storage**
    - Merge and organize outputs, presenting them in a clear, editable interface.
    - Log session actions, final outputs, and decisions in a local vector DB for retrieval.
4. **Confidential Mode \& Local LLMs**
    - Fingerprint confidential files; route to local models for processing.
    - Maintain full data privacy and compatibility for research needs.
5. **Extensibility \& Evolution**
    - Gradually add features for images, voice, smart device controls, as needs grow.
    - Expand validation rules and report formatting based on use.

## Summary Table

| Area | Key Feature | Implementation Notes |
| :-- | :-- | :-- |
| Orchestration | Parallel prompt to Gemini/Claude/Perplexity | Use multi-thread/process logic |
| Local AI | Private LLMs for confidential docs | Ollama/llama.cpp on-device |
| Validation/Retries | Automated checklist per task | User-configurable |
| Memory | Long-term, searchable local DB | Chroma, SQLite, folder structure |
| UI | Desktop, headless browser logins | Electron/Tauri, Playwright |
| Privacy | File tagging \& automatic routing | Scripted rules, user toggles |

**Samay** will unify the power of multiple AI agents while upholding privacy, flexibility, and transparency, making it a robust, personal AI partner for research, coding, and productivity on your MacBook Air M2.


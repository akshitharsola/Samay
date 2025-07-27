<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Samay v3 Simplified Implementation Guide

**Main Takeaway:** Focus on three core modes—Companion Chat, Confidential Mode, and Multi-Service Orchestration—minimizing complexity and enforcing a clear, machine-readable prompt pipeline (brainstorm → refine → dispatch → compare).

## 1. Core UI Structure

Reduce the number of tabs to three, each shown in the top navigation bar:


| Tab Name | Purpose |
| :-- | :-- |
| 1. Companion Chat | Personal conversational interface with local Phi-3-Mini companion (memory, persona). |
| 2. Confidential Mode | Private research sessions; uses only local LLM without external calls. |
| 3. Multi-Service Hub | Backend-verified “Ready” indicator for Claude, Gemini, Perplexity + dispatch logic. |

**UI Notes:**

- Display a single green check next to each service in the Multi-Service Hub only after a successful backend health-check ping.
- Hide all other panels (Smart Dashboard, Workflow Builder, etc.) until core functionality is rock-solid.


## 2. Backend Health-Check \& Ready Button

Implement one unified endpoint `/api/services/status` that returns:

```json
{
  "claude": true,
  "gemini": true,
  "perplexity": false
}
```

- On page load of Multi-Service Hub, call this endpoint.
- Render a checkbox or toggle for each service; automatically check when `true`, disable if `false`.
- Re-poll every 30 seconds; on any change, update UI.


## 3. Machine-Language Prompt Pipeline

All interactions with external services must follow a structured, JSON-only chat protocol.

### 3.1 Companion Chat \& Brainstorming

- **System message at session start:**

```text
System: You are Samay, my personal AI companion. Always reply in valid JSON.
```

- **User → Companion (Phi-3-Mini):**

```json
{ "phase": "brainstorm", "topic": "<user topic>" }
```

- **Assistant reply example:**

```json
{ "ideas": ["Idea 1", "Idea 2", …] }
```


### 3.2 Iterative Refinement

- **User feedback:**

```json
{ "phase": "refine", "base": "<previous JSON>", "feedback": "<user notes>" }
```

- **Assistant returns next draft:**

```json
{ "draft": "<refined prompt JSON>" }
```

- Loop until user sends `{ "phase": "finalize" }`.


### 3.3 Final Dispatch to Services

Once finalized, the companion emits:

```json
{ 
  "phase": "dispatch",
  "prompt": { …final prompt… }
}
```

- The frontend then sends **identical** JSON to each service’s chat window.


## 4. Multi-Service Orchestration \& Output Comparison

1. **Dispatch:** Post the same JSON to Claude, Gemini, Perplexity chat inputs.
2. **Capture:** Each service must be instructed to reply with:

```json
{ "response": "<text>", "metadata": { … } }
```

3. **Validation \& Comparison:**
    - After all three responses arrive, compare key fields (e.g., length, sentiment, keyword coverage).
    - If any result fails pre-defined checks, automatically spawn a refinement loop:

```json
{ 
  "phase": "service_refine",
  "failed_services": ["perplexity"],
  "feedback": "Missing analysis of X"
}
```

4. **Final Synthesis:** Once all pass, display a merged summary in JSON:

```json
{ 
  "claude": { "response": "…", "ok": true },
  "gemini": { … },
  "perplexity": { … }
}
```


## 5. Implementation Checklist

1. **UI**
    - [ ] Three-tab navigation only
    - [ ] Service status checkboxes in Multi-Service Hub
    - [ ] Hide all deprecated tabs
2. **Backend**
    - [ ] `/api/services/status` endpoint
    - [ ] Health-check routine every 30 s
    - [ ] Proxy routes to chat windows (SeleniumBase or API-driven)
3. **Local Companion (Phi-3-Mini)**
    - [ ] JSON schema enforcement on both input \& output
    - [ ] ConversationMemory + Persona modules
4. **Chat Orchestration**
    - [ ] Uniform JSON prompt patterns for all phases
    - [ ] Automatic dispatch + capture + validation logic
5. **Error Handling \& Refine Loop**
    - [ ] Detect service timeouts/invalid JSON → trigger refinement
    - [ ] Show user minimal error messages in JSON

**By adhering strictly to this simplified three-tab design and structured JSON prompt pipeline, Samay v3 will deliver a coherent companion experience, secure private research, and robust multi-service orchestration—maximizing efficiency, token savings, and user clarity.**

<div style="text-align: center">⁂</div>

[^1]: 26July.md

[^2]: Research_Report1.md

[^3]: CURRENT_ISSUES_ANALYSIS.md


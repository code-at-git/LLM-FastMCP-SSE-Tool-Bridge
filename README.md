# 🔌 Local Ollama Model & FastMCP SSE Tool Bridge

A lightweight, production-ready Python orchestration script that dynamically hooks a local **Ollama** model up to a **Model Context Protocol (MCP)** server over a Server-Sent Events (SSE) connection. 

This bridge dynamically auto-discovers all 8 available tools from your local FastMCP server, maps their JSON schemas to the Ollama execution format, handles parallel tool execution, and returns the serialized results back to the LLM for final synthesis.

---

## ✨ Features

* **Zero Hardcoding**: Dynamically fetches and transforms schemas (`inputSchema`) for all 8 server tools on startup.
* **Ollama Compatibility**: Converts Pydantic or dictionary tool schemas into the standard function-calling array required by Ollama.
* **Asynchronous & Memory-Safe**: Uses `asyncio` and `fastmcp.Client` to maintain a non-blocking SSE stream.
* **Robust Serialization**: Handles nested `content` block wrappers returned by FastMCP and cleanly processes them into plain strings for the LLM.

---

## 🛠️ System Prerequisites

Ensure you have the following installed and running locally:

1. **Ollama**: Download and install from [ollama.com](https://ollama.com).
2. **Target Model**: Pull the lightweight model configured in the script:
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Active FastMCP Server**: Your custom MCP server must be running and listening for SSE connections at:
   ```text
   http://127.0.0.1:8080/sse
   ```

---

## 🚀 Quick Start

### 1. Installation

Clone your repository or save the scripts locally, then install the required dependencies:

```bash
pip install ollama fastmcp
```

### 2. Run the MCP Server

Open a separate terminal window and start the MCP server script so the automated 8-tool resources are available:

```bash
python mcp_server.py
```

### 3. Verify Your Configuration

Open your client script (`mcp_ollama_client.py`) and ensure the configuration constants match your local setup:

```python
OLLAMA_MODEL = "llama3.2:3b"
MCP_SERVER_URL = "http://127.0.0.1:8080/sse"
```

### 4. Execute the Orchestrator

Switch back to your main terminal window and run the client bridge script to kick off the automated 8-tool sequence validation pipeline:

```bash
python mcp_ollama_client.py
```

---

## 📦 Verified Tool Test Pipeline

The script runs an automated sequence testing all 8 native server capabilities:

| # | Tool Name | Test Query Sample |
|---|---|---|
| 1 | `greet` | "Greet a user named Sarah." |
| 2 | `add` | "Add the numbers 350 and 420 together." |
| 3 | `multiply` | "Multiply 12.5 by 4.0." |
| 4 | `get_time` | "What is the current time right now?" |
| 5 | `get_weather` | "Check the weather data for Tokyo." |
| 6 | `save_note` | "Save a note titled 'Meeting' with the content..." |
| 7 | `list_notes` | "List all my saved notes from the folder." |
| 8 | `search_users` | "Search our system for a user named Alice." |

---

## 🧠 Architectural Workflow

```text
[ User Prompt ]
       │
       ▼
[ MCPToolBridge ] ──(Fetches Tools via SSE)──> [ FastMCP Server ]
       │                                              │
(Maps JSON Schema)                                    │
       │                                              │
       ▼                                              │
   [ Ollama ] ──(Requests Tool Execution)             │
       │                                              │
       ▼                                              │
[ MCPToolBridge ] ──(Executes `.call_tool()`)─────────┘
       │
 (Serializes Result)
       │
       ▼
   [ Ollama ] ──(Synthesizes Final Answer)──> [ Console Output ]
```

---

## 🛡️ Error & Safety Controls

* **Ollama Handlers**: Wrapped in strict try/except structures to catch dropped local connections gracefully without crashing the pipeline execution loop.
* **Fallback Serialization**: If a custom tool spits out data that doesn't natively map to a text block, the pipeline falls back to a clean string formatting array (`json.dumps`), avoiding runtime type crashes.
* **Server Verification**: The script explicitly performs an upfront handshake check to verify the exact payload size array before attempting to forward prompt arguments.

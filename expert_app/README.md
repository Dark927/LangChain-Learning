# Elite Architecture Core 🧠⚡

An ultra-advanced, local AI architecture orchestration application. Powered by FastAPI, LangChain, and Groq, this interface summons a top-5% engineering expert designed to deliver esoteric, deep-dive architectural insights for complex software patterns, agents, and systems.

## ✨ Core Features

*   **Neon Glassmorphism Interface**: A stunning, responsive web UI with built-in Light/Dark mode themes and seamless Markdown rendering.
*   **Dual Report Generation**: Automatically distills complex AI responses into professional, standalone `.html` and `.md` documentation files.
*   **Dynamic Data Visualization**: Bypasses traditional Mermaid bugs by dynamically writing and executing raw Python `matplotlib` scripts in the background, embedding the resulting diagrams directly into your reports.
*   **Background Retroactive Reports**: Instantly convert any existing chat response into a beautifully formatted document via asynchronous AJAX fetch requests (zero page reloads).
*   **Production-Grade Markdown**: Fully customized `Pygments` (Monokai) syntax highlighting, intelligent language badge injection, and responsive, scrollable horizontal data tables.
*   **Live Token Telemetry**: Monitors and displays exact Prompt, Completion, and Total token usage from the Groq API on every invocation.

## 🛠️ Architecture Stack

*   **Backend**: FastAPI, Uvicorn, Python
*   **Agent Orchestration**: LangChain `init_chat_model`
*   **LLM Provider**: Groq (`groq:openai/gpt-oss-120b`)
*   **Generative Visualization**: Python Subprocess + Matplotlib
*   **Frontend**: Jinja2, Vanilla JS, CSS3 Variables, Python Markdown + Pygments

## 🚀 Setup & Execution

### 1. Requirements
Ensure you are in the root directory and install all dependencies:
```bash
pip install -r expert_app/requirements.txt
```

### 2. Environment Configuration
The application strictly enforces secure secrets management. Ensure a `.env` file exists in the root directory (one level above `expert_app`) containing your API keys:
```env
GROQ_API_KEY=your_secure_api_key_here
```

### 3. Ignition
Launch the FastAPI server using the module flag from the root directory:
```bash
python -m expert_app.main
```

### 4. Access
Navigate your web browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## 📂 Directory Structure
```text
expert_app/
├── reports/                 # Auto-generated HTML & MD reports (Git ignored)
├── static/
│   └── style.css            # Glassmorphism, Pygments, and core UI styles
├── templates/
│   └── index.html           # Jinja2 template and async frontend logic
├── agent.py                 # Core LangChain agent definition and system prompts
├── config.py                # Type-safe environment and directory configuration
├── main.py                  # FastAPI routes, Markdown parsers, and Matplotlib execution
├── tools.py                 # File generation and IO operations
└── requirements.txt         # Project dependencies
```

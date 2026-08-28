"""FastAPI Application Server."""

import sys
import markdown
import re
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, SystemMessage

from .config import TEMPLATES_DIR, STATIC_DIR, REPORTS_DIR, PORT, HOST, UTF8, WINDOWS_OS
from .agent import get_expert_llm, SYSTEM_PROMPT
from .tools import format_markdown, create_report_files
from .mcp_client import load_all_mcp_tools
from langgraph.prebuilt import create_react_agent

# --- CONSTANTS ---
# Ensure UTF-8 Console logging for Windows
if sys.platform == WINDOWS_OS:
    try:
        sys.stdout.reconfigure(encoding=UTF8)
        sys.stderr.reconfigure(encoding=UTF8)
    except Exception:
        pass

app = FastAPI(title="AI Architecture Expert Interface")

# Mount static and reports directories
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))





@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main Neon chat interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"response": None}
    )

@app.post("/chat", response_class=HTMLResponse)
async def chat_endpoint(
    request: Request, 
    user_input: str = Form(...), 
    generate_html: bool = Form(False)
):
    """Handle user chat submissions."""
    
    enhanced_prompt = user_input
    if generate_html:
        enhanced_prompt += "\n\n[USER INSTRUCTION: I have explicitly checked the 'Generate HTML Report with Visualizations' box. YOU MUST call the generate_architecture_plot MCP tool if relevant and embed the result.]"
        
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=enhanced_prompt)
    ]
    
    try:
        # Load MCP tools via exit stack to ensure cleanup
        all_tools, exit_stack = await load_all_mcp_tools()
        
        async with exit_stack:
            # Create LangGraph ReAct agent
            expert_llm = get_expert_llm()
            agent_executor = create_react_agent(expert_llm, all_tools)
            
            # Invoke the agent
            result = await agent_executor.ainvoke({"messages": messages})
            
            # Extract final message and token usage
            final_message = result["messages"][-1]
            ai_text = str(final_message.content)
            
            token_data = None
            if hasattr(final_message, "response_metadata") and final_message.response_metadata:
                token_usage = final_message.response_metadata.get("token_usage", {})
                if token_usage:
                    token_data = {
                        "prompt": token_usage.get("prompt_tokens", 0),
                        "completion": token_usage.get("completion_tokens", 0),
                        "total": token_usage.get("total_tokens", 0)
                    }

        formatted_html = format_markdown(ai_text)
        
        if generate_html:
            # Generate Title strictly from user question (truncate if too long)
            title = user_input.strip()
            if len(title) > 60:
                title = title[:57] + "..."
                
            html_url, md_url = create_report_files(title, formatted_html, "", ai_text)
            
            formatted_html += f"""
            <div class='tool-output' style='display:flex; gap: 15px; align-items:center;'>
                <strong>[SYSTEM EVENT]: Reports generated!</strong>
                <a href='{html_url}' target='_blank' style='color: #fff; background: var(--neon-orange); padding: 5px 10px; border-radius: 4px; font-weight:bold; text-decoration:none;'>VIEW HTML</a>
                <a href='{md_url}' download style='color: var(--neon-orange); border: 1px solid var(--neon-orange); padding: 5px 10px; border-radius: 4px; font-weight:bold; text-decoration:none;'>DOWNLOAD .MD</a>
            </div>
            """

            
    except Exception as e:
        formatted_html = f"<p style='color:red;'>SYSTEM ERROR: {str(e)}</p>"
        token_data = None
        ai_text = ""
        
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "user_input": user_input,
            "response": formatted_html,
            "raw_text": ai_text,
            "token_data": token_data
        }
    )

@app.post("/retro_report")
async def retro_report(original_prompt: str = Form(...), response_text: str = Form(...)):
    """Background endpoint to generate a report from existing text without page reload."""
    try:
        # Since we removed manual extract_plot_code, we just use the text natively.
        formatted_html = format_markdown(response_text)
        
        # Title exclusively from the original prompt
        title = original_prompt.strip()
        if len(title) > 60:
            title = title[:57] + "..."
            
        html_url, md_url = create_report_files(title, formatted_html, "", response_text)
        
        msg = f"""Reports generated: 
        <a href='{html_url}' target='_blank' style='color:#fff; text-decoration:underline;'>View HTML</a> | 
        <a href='{md_url}' download style='color:#fff; text-decoration:underline;'>Download .MD</a>"""
        
        return JSONResponse({"status": "success", "message": msg})
        
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print(f"Starting Elite AI Server on http://{HOST}:{PORT}")
    uvicorn.run("expert_app.main:app", host=HOST, port=PORT, reload=True)

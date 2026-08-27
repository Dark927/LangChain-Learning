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
from .agent import expert_llm, SYSTEM_PROMPT
from .tools import create_report_files

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

def extract_mermaid(text: str) -> tuple[str, str]:
    """Extracts the mermaid block from the AI's response if it exists."""
    mermaid_code = ""
    cleaned_text = text
    
    match = re.search(r':::MERMAID:::\s*(.*?)\s*:::END_MERMAID:::', text, re.DOTALL)
    if match:
        mermaid_code = match.group(1).strip()
        cleaned_text = text[:match.start()] + text[match.end():]
        
    return cleaned_text.strip(), mermaid_code

def format_markdown(text: str) -> str:
    """Converts markdown text to HTML securely with syntax highlighting."""
    html = markdown.markdown(text, extensions=[
        'pymdownx.superfences',
        'pymdownx.highlight',
        'tables'
    ])
    
    # pymdownx generates: <div class="highlight"><pre><span>...
    # It also attaches the language class if specified, e.g. <div class="highlight language-python">
    # Let's map it to our CSS class and extract the language for the badge
    html = html.replace('class="highlight', 'class="codehilite')
    
    # Inject data-language attribute based on the language-XYZ class
    def inject_lang(match):
        lang = match.group(1).replace('language-', '')
        return f'<div class="codehilite {match.group(1)}" data-language="{lang}">'
    
    html = re.sub(r'<div class="codehilite ([^"]+)">', inject_lang, html)
    
    # Fallback for code blocks without a specified language
    html = html.replace('<div class="codehilite">', '<div class="codehilite" data-language="code">')
    
    # Wrap tables in a responsive scrolling container
    html = html.replace('<table>', '<div style="overflow-x: auto; width: 100%; margin: 1.5rem 0; border-radius: var(--border-radius-sm); border: 1px solid var(--glass-border);"><table style="margin: 0; border: none;">')
    html = html.replace('</table>', '</table></div>')
    
    return html

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
        enhanced_prompt += "\n\n[USER INSTRUCTION: I have explicitly checked the 'Generate HTML Report with Visualizations' box. YOU MUST append a :::MERMAID::: block at the end of your response for the visualization.]"
        
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=enhanced_prompt)
    ]
    
    try:
        response_msg = expert_llm.invoke(messages)
        ai_text = str(response_msg.content)
        
        token_data = None
        if hasattr(response_msg, "response_metadata") and response_msg.response_metadata:
            token_usage = response_msg.response_metadata.get("token_usage", {})
            if token_usage:
                token_data = {
                    "prompt": token_usage.get("prompt_tokens", 0),
                    "completion": token_usage.get("completion_tokens", 0),
                    "total": token_usage.get("total_tokens", 0)
                }

        text_content, mermaid_code = extract_mermaid(ai_text)
        formatted_html = format_markdown(text_content)
        
        if generate_html or mermaid_code:
            # Generate Title strictly from user question (truncate if too long)
            title = user_input.strip()
            if len(title) > 60:
                title = title[:57] + "..."
                
            html_url, md_url = create_report_files(title, formatted_html, mermaid_code, text_content)
            
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
        prompt = f"Given this architectural text:\n\n{response_text[:2000]}\n\nGenerate ONLY a :::MERMAID::: block representing this architecture. Do not output anything else."
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
        llm_resp = expert_llm.invoke(messages)
        
        _, mermaid_code = extract_mermaid(str(llm_resp.content))
        
        formatted_html = format_markdown(response_text)
        
        # Title exclusively from the original prompt
        title = original_prompt.strip()
        if len(title) > 60:
            title = title[:57] + "..."
            
        html_url, md_url = create_report_files(title, formatted_html, mermaid_code, response_text)
        
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

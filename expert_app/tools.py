"""Tools and File Generators for the Expert AI App."""

import uuid
from datetime import datetime
from .config import REPORTS_DIR, UTF8

# --- CONSTANTS ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        // Inherit theme from main app
        if (localStorage.getItem('app-theme') === 'light') {{
            document.documentElement.setAttribute('data-theme', 'light');
        }}
        mermaid.initialize({{startOnLoad:true, theme: localStorage.getItem('app-theme') === 'light' ? 'default' : 'dark'}});
    </script>
</head>
<body class="report-body">
    <div class="report-container">
        <header class="neon-header" style="text-align:center; border-bottom: 1px solid var(--glass-border); padding-bottom: 2rem; margin-bottom: 2rem;">
            <h1 style="color: var(--neon-orange); font-family: var(--font-mono);">{title}</h1>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Generated on {timestamp}</p>
        </header>
        
        <main class="report-content">
            {content_html}
        </main>
        
        {visuals_html}
    </div>
</body>
</html>
"""

VISUALS_TEMPLATE = """
        <section class="visuals-section" style="margin-top: 3rem; background: var(--glass-bg); padding: 2rem; border-radius: var(--border-radius-lg); border: 1px solid var(--glass-border);">
            <h2 style="color: var(--text-main); font-family: var(--font-sans);">Architecture Visualization</h2>
            <div class="mermaid" style="background: rgba(0,0,0,0.4); padding: 2rem; border-radius: var(--border-radius-sm); display: flex; justify-content: center; margin-top: 1.5rem;">
{mermaid_code}
            </div>
        </section>
"""

def create_report_files(title: str, content_html: str, mermaid_code: str, raw_markdown: str) -> tuple[str, str]:
    """Generates styled HTML and MD report files.
    Returns (html_url, md_url).
    """
    visuals = ""
    # Strip ALL backticks aggressively to fix Mermaid 11.17.2 errors
    import re
    if mermaid_code:
        clean_mermaid = re.sub(r'```(?:mermaid)?', '', mermaid_code)
        clean_mermaid = clean_mermaid.strip()
        visuals = VISUALS_TEMPLATE.format(mermaid_code=clean_mermaid)
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_html = HTML_TEMPLATE.format(
        title=title,
        timestamp=now,
        content_html=content_html,
        visuals_html=visuals
    )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())[:8]
    html_filename = f"report_{file_id}.html"
    md_filename = f"report_{file_id}.md"
    
    html_filepath = REPORTS_DIR / html_filename
    md_filepath = REPORTS_DIR / md_filename
    
    # Write HTML
    with open(html_filepath, "w", encoding=UTF8) as f:
        f.write(full_html)
        
    # Write MD
    md_content = f"# {title}\n*Generated on {now}*\n\n{raw_markdown}\n\n"
    if mermaid_code:
        clean_mermaid = re.sub(r'```(?:mermaid)?', '', mermaid_code).strip()
        md_content += f"## Architecture Visualization\n\n```mermaid\n{clean_mermaid}\n```\n"
        
    with open(md_filepath, "w", encoding=UTF8) as f:
        f.write(md_content)
        
    return f"/reports/{html_filename}", f"/reports/{md_filename}"

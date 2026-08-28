"""Tools and File Generators for the Expert AI App."""

import uuid
import markdown
import re
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
    <script>
        // Inherit theme from main app
        if (localStorage.getItem('app-theme') === 'light') {{
            document.documentElement.setAttribute('data-theme', 'light');
        }}
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
            <div style="background: rgba(0,0,0,0.4); padding: 2rem; border-radius: var(--border-radius-sm); display: flex; justify-content: center; margin-top: 1.5rem;">
                <img src="{plot_image_path}" alt="Generated Visualization" style="max-width: 100%; border-radius: 4px;">
            </div>
        </section>
"""

def create_report_files(title: str, content_html: str, plot_image_path: str, raw_markdown: str) -> tuple[str, str]:
    """Generates styled HTML and MD report files.
    Returns (html_url, md_url).
    """
    visuals = ""
    if plot_image_path:
        visuals = VISUALS_TEMPLATE.format(plot_image_path=plot_image_path)

        
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
    
    # Write HTML - safely strip carriage returns to avoid \r\r\n corruption on Windows
    with open(html_filepath, "wb") as f:
        f.write(full_html.replace('\r', '').encode(UTF8))
        
    # Write MD
    md_content = f"# {title}\n*Generated on {now}*\n\n{raw_markdown}\n\n"
    if plot_image_path:
        md_content += f"## Architecture Visualization\n\n![Generated Visualization]({plot_image_path})\n"
        
    with open(md_filepath, "wb") as f:
        f.write(md_content.replace('\r', '').encode(UTF8))
        
    return f"/reports/{html_filename}", f"/reports/{md_filename}"

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

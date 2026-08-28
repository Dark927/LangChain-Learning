import sys
import uuid
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ExpertPlotterMCP")

# Resolve reports directory relative to this script
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

import asyncio

@mcp.tool()
async def generate_architecture_plot(plot_code: str) -> str:
    """
    Executes matplotlib Python code to generate an architecture visualization.
    Returns the web-accessible path to the generated PNG image.
    The plot_code MUST NOT contain plt.show(). It MUST use the PLOT_PATH variable to save the file.
    Example: plt.savefig(PLOT_PATH)
    """
    if not plot_code:
        return "Error: No plot code provided."
    
    plot_id = str(uuid.uuid4())[:8]
    img_filename = f"plot_{plot_id}.png"
    img_filepath = REPORTS_DIR / img_filename
    script_filepath = REPORTS_DIR / f"temp_{plot_id}.py"
    
    # Inject the PLOT_PATH variable securely
    injected_code = f'PLOT_PATH = r"{str(img_filepath.absolute())}"\n' + plot_code
    
    with open(script_filepath, "w", encoding="utf-8") as f:
        f.write(injected_code)
        
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(script_filepath),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.wait()
        
        if process.returncode != 0:
            return f"Plot execution failed (return code {process.returncode})."
            
        return f"/reports/{img_filename}"
    except Exception as e:
        return f"Plot execution failed with exception: {str(e)}"
    finally:
        try:
            script_filepath.unlink(missing_ok=True)
        except Exception:
            pass

if __name__ == "__main__":
    mcp.run()

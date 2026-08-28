import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ExpertFilesystemMCP")

@mcp.tool()
def read_local_file(filepath: str) -> str:
    """Reads the contents of a local file. Useful for analyzing source code."""
    try:
        path = Path(filepath)
        if not path.exists():
            return f"Error: File {filepath} does not exist."
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def list_directory(dir_path: str) -> str:
    """Lists files and directories in the given path. Useful for understanding project structure."""
    try:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            return f"Error: Directory {dir_path} does not exist."
        items = [str(p.name) for p in path.iterdir()]
        return "Contents of " + dir_path + ":\n- " + "\n- ".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

if __name__ == "__main__":
    mcp.run()

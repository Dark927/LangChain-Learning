import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from pathlib import Path

FS_SERVER_PATH = Path(__file__).parent / "mcp_servers" / "fs_mcp" / "server.py"
PLOTTER_SERVER_PATH = Path(__file__).parent / "mcp_servers" / "plotter_mcp" / "server.py"

async def load_all_mcp_tools():
    """Starts the MCP servers and returns their bound tools along with the exit stack.
    The caller MUST manage the AsyncExitStack (e.g., using it in an async with block or closing it manually).
    """
    stack = AsyncExitStack()
    
    try:
        # 1. Start Filesystem Server
        fs_params = StdioServerParameters(command=sys.executable, args=[str(FS_SERVER_PATH)])
        fs_read, fs_write = await stack.enter_async_context(stdio_client(fs_params))
        fs_session = await stack.enter_async_context(ClientSession(fs_read, fs_write))
        await fs_session.initialize()
        fs_tools = await load_mcp_tools(fs_session)
        
        # 2. Start Plotter Server
        plotter_params = StdioServerParameters(command=sys.executable, args=[str(PLOTTER_SERVER_PATH)])
        plotter_read, plotter_write = await stack.enter_async_context(stdio_client(plotter_params))
        plotter_session = await stack.enter_async_context(ClientSession(plotter_read, plotter_write))
        await plotter_session.initialize()
        plotter_tools = await load_mcp_tools(plotter_session)
        
        return fs_tools + plotter_tools, stack
    except Exception as e:
        await stack.aclose()
        raise e

import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from observability.logger import logger


class MCPClient:

    def __init__(self, server_script: str):
        """
        server_script → path to MCP server script
        """
        self.server_script = server_script
        self.session        = None
        self._context       = None

    async def __aenter__(self):
        """Start MCP server as subprocess and connect."""
        server_params = StdioServerParameters(
            command = "python",
            args    = [self.server_script]
        )

        self._context = stdio_client(server_params)
        read, write   = await self._context.__aenter__()

        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

        logger.info("MCP client connected to server")
        return self

    async def __aexit__(self, *args):
        """Disconnect from MCP server."""
        if self.session:
            await self.session.__aexit__(*args)
        if self._context:
            await self._context.__aexit__(*args)
        logger.info("MCP client disconnected")

    async def call_tool(self, name: str, arguments: dict = {}) -> str:
        """Call a tool on the MCP server."""
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text

    async def list_tools(self) -> list:
        """List available tools on the MCP server."""
        result = await self.session.list_tools()
        return [t.name for t in result.tools]
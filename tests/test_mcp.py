import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def test_real_mcp_client(tmp_path):
    async def exercise():
        params = StdioServerParameters(command=sys.executable,
            args=["-m", "second_draft.server", "--database", str(tmp_path / "mcp.db")],
            env=dict(os.environ))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert {t.name for t in tools} == {"archive_project", "search_projects", "get_project", "update_project", "prepare_remix"}
                result = await session.call_tool("archive_project", {"title": "Demo", "description": "Fictional project", "pause_reason": "Scope grew"})
                assert not result.isError
                saved = json.loads(result.content[0].text)
                result = await session.call_tool("get_project", {"project_id": saved["id"]})
                assert not result.isError
                assert json.loads(result.content[0].text)["title"] == "Demo"
                result = await session.call_tool("get_project", {"project_id": "missing"})
                assert result.isError
    asyncio.run(exercise())

def test_http_app_configuration(tmp_path):
    from second_draft.server import create_server
    server = create_server(tmp_path / "http.db", port=8123)
    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 8123
    assert any(getattr(route, "path", None) == "/mcp" for route in server.streamable_http_app().routes)

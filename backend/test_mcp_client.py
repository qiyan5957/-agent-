# backend/test_mcp_client.py
"""
用 mcp 官方 SDK 直接连接本机 stdio 的 todo server，列出并调用工具。

运行方式（在 backend 目录下，用 venv 的 python）：
    D:/PythonProject/个人事务助手agent/venv/Scripts/python.exe test_mcp_client.py

说明：todo_mcp_server.py 是 transport="stdio" 的子进程，不是 HTTP 服务，
所以不能用 httpx 连，要用 mcp.client.stdio 的 stdio_client 拉起子进程通信。
"""
import asyncio
import os
import sys

# Windows 控制台默认 GBK，emoji 会触发 UnicodeEncodeError，这里强制 stdout 用 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 用绝对路径，避免子进程工作目录不确定（和服务器里 DB_PATH 的做法一致）
SERVER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo_mcp_server.py")


async def main():
    params = StdioServerParameters(
        command=sys.executable,  # 用当前解释器（venv 的 python）拉起子进程
        args=[SERVER_FILE],
        env={"PYTHONUTF8": "1"},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. 初始化握手
            await session.initialize()
            print("✅ 已连接 todo server\n")

            # 2. 列出工具（这就是你说的"获取工具"）
            tools_result = await session.list_tools()
            print(f"共 {len(tools_result.tools)} 个工具：")
            for t in tools_result.tools:
                # t.inputSchema 是参数的 JSON Schema
                params_schema = getattr(t, "inputSchema", None) or {}
                props = params_schema.get("properties", {})
                print(f"  🔧 {t.name}({', '.join(props.keys())}) — {t.description}")

            # 3. 实际调用一个工具
            print("\n── 调用 list_todos(filter='all') ──")
            result = await session.call_tool("list_todos", {"filter": "all"})
            for block in result.content:
                print("  📋", block.text)


if __name__ == "__main__":
    asyncio.run(main())

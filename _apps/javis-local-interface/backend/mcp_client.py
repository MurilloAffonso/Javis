"""mcp_client.py — Javis consome o ecossistema de tools MCP (Model Context Protocol).

Conceito minerado do PraisonAI: em vez de reescrever integrações, o Javis conecta
em servidores MCP (config em data/mcp_servers.json) e usa as tools deles. Read-only
de config; conexão stdio por subprocesso (uvx/npx). Sem segredo em log.

API: list_servers() (sync), list_tools(id) e call_tool(id, tool, args) (async).
"""
from __future__ import annotations
import os
import json
from pathlib import Path

import safe_config

_CFG = Path(__file__).resolve().parents[1] / "data" / "mcp_servers.json"


def _servers() -> dict:
    try:
        return json.loads(_CFG.read_text(encoding="utf-8")).get("servers", {})
    except Exception:
        return {}


def list_servers() -> list[dict]:
    return [{"id": k, "command": v.get("command"), "descricao": v.get("descricao", "")}
            for k, v in _servers().items()]


async def _connect(cfg):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(
        command=cfg["command"], args=cfg.get("args", []),
        env={**os.environ, **(cfg.get("env") or {})},
    )
    return stdio_client, ClientSession, params


async def list_tools(server_id: str) -> dict:
    if not safe_config.mcp_enabled():
        return safe_config.disabled_response("mcp", safe_config.JAVIS_ENABLE_MCP)
    cfg = _servers().get(server_id)
    if not cfg:
        return {"server": server_id, "error": "servidor desconhecido"}
    try:
        stdio_client, ClientSession, params = await _connect(cfg)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                return {"server": server_id, "tools": [
                    {"name": t.name, "description": (t.description or "")[:200]} for t in tools
                ]}
    except Exception as e:
        return {"server": server_id, "error": str(e)[:300]}


async def call_tool(server_id: str, tool: str, arguments: dict | None = None) -> dict:
    if not safe_config.mcp_enabled():
        return safe_config.disabled_response("mcp", safe_config.JAVIS_ENABLE_MCP)
    cfg = _servers().get(server_id)
    if not cfg:
        return {"status": "error", "message": "servidor desconhecido"}
    try:
        stdio_client, ClientSession, params = await _connect(cfg)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(tool, arguments or {})
                texto = ""
                for c in (res.content or []):
                    texto += getattr(c, "text", "") or ""
                return {"status": "ok", "server": server_id, "tool": tool, "result": texto[:4000]}
    except Exception as e:
        return {"status": "error", "message": str(e)[:300]}

# -*- coding: utf-8 -*-
"""
Prepara el entorno de demostración en c:/Users/mapog/Documents/cursor_mcp_demo
para grabar el Vídeo 03 (Fix Cursor MCP Server Errors: The ENOENT Fix).
"""

import json
import sqlite3
from pathlib import Path

DEMO_DIR = Path(r"c:\Users\mapog\Documents\cursor_mcp_demo")
CURSOR_DIR = DEMO_DIR / ".cursor"
CURSOR_DIR.mkdir(parents=True, exist_ok=True)

# 1. Crear base de datos SQLite de prueba
db_path = DEMO_DIR / "test.db"
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, role TEXT)")
conn.execute("DELETE FROM users")
conn.execute("INSERT INTO users (name, role) VALUES ('Alice', 'Admin'), ('Bob', 'Engineer')")
conn.commit()
conn.close()

# 2. Crear .cursor/mcp.json con la configuración inicial que lanza el error ENOENT
mcp_broken = {
    "mcpServers": {
        "sqlite": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
        }
    }
}
mcp_path = CURSOR_DIR / "mcp.json"
mcp_path.write_text(json.dumps(mcp_broken, indent=2) + "\n", encoding="utf-8")

print(f"Entorno demo listo en: {DEMO_DIR}")
print(f"  - Base de datos: {db_path}")
print(f"  - Configuración MCP: {mcp_path}")

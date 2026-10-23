# Metadata de Publicación — Video 03: Fix Cursor MCP Server Errors (The ENOENT Fix)

Documento oficial de empaque y metadatos para YouTube según las directivas de `PUBLICACION.md`, `PRODUCCION_VIDEO_03.md` y `GEMINI.md`.

---

## 1. Ficha Técnica del Vídeo Master

| Parámetro | Valor Medido / Especificación | Estado |
|---|---|---|
| **Archivo Master** | `output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4` | Generado |
| **Duración Exacta** | **53.04 s** (00:53.04 / Formato horizontal 16:9 largo) | Cumple |
| **Resolución & Aspecto** | **1920 × 1080** (16:9 exacto) | Verificado |
| **Tasa de Cuadros** | **60.0 fps** constante (`r_frame_rate=60/1`) | Verificado |
| **Sonoridad Integrada** | **-14.02 LUFS** (EBU R128 para YouTube) | Objetivo: -14.0 LUFS |
| **Pista de Voz (TTS)** | `nova` en `gpt-4o-mini-tts` (tono conversacional dinámico) | Aprobado |
| **Cama Musical** | `musica.mp3` a **-18.0 dB relativo** (ganancia 0.11601) con fade-in 1.5s y fade-out 2.5s | ADR-004 |
| **Sincronización de Cortes** | Remate exacto de **1.10s** tras la última palabra hablada en cada tramo | Regla 11 bis / ADR-002 |
| **Subtítulos Sincronizados** | `assets/videos/cursor_mcp_enoent_fix/subtitulos_video_03.srt` | Whisper + Alineación |

---

## 2. Título Oficial para YouTube

### Opción Principal Elegida (46 caracteres):
**`Fix Cursor MCP Server Error: spawn ENOENT Fix`**

- **Front-loading:** `Fix Cursor MCP Server Error` en los primeros 27 caracteres + el error literal `spawn ENOENT Fix`.
- **Recuento de keywords en la locución (§2 `PUBLICACION.md`):**
  - *Cursor:* Tramo 01 (2 veces), Tramo 02 (1 vez) — Total: 3 menciones.
  - *MCP server:* Tramo 01, Tramo 03 — Total: 2 menciones (+ `mcp.json` en Tramo 02).
  - *spawn ENOENT / error:* Tramo 01 (*"fails with a red 'spawn ENOENT' error"*).
  - *Fix:* Tramo 02 (*"The fix takes ten seconds"*), Tramo 03 (*"zero-fluff dev fixes"*).

### Opciones Alternativas (41–55 caracteres):
1. `Fix Cursor MCP Server Errors: The ENOENT Fix` (44 caracteres)
2. `Fix Cursor MCP spawn ENOENT Error (uvx & npx Fix)` (51 caracteres)
3. `How to Fix Cursor MCP Server Connection Errors` (46 caracteres)

---

## 3. Miniatura Oficial (Thumbnail)

- **Archivo Oficial:** `assets/videos/cursor_mcp_enoent_fix/thumbnail.jpg`
- **Dimensiones:** `1280 × 720` (16:9 exacto).
- **Peso:** **150.5 KB** (Límite estricto de YouTube: 2048 KB).
- **Texto:** `FIX CURSOR MCP` (3 palabras, tipografía limpia bold en blanco `#FFFFFF` y verde esmeralda `#3ECF8E`).
- **Composición e Identidad Visual:**
  - Estilo técnico artesanal directo (cero *AI slop*): capturas reales del IDE Cursor `3.19.7` a la izquierda comparando el estado en rojo (`Needs Attention 1` / `Error - MCP error -32000: Connection closed` / `spawn ENOENT`) frente al estado conectado en verde (`Connected 1` / `6 tools, 1 resource enabled`).
  - A la derecha, el icono oficial de Cursor y la ventana `.cursor/mcp.json` mostrando el diff exacto (`- "command": "uvx"` vs `+ "command": "C:\\Tools\\uv\\uvx.exe"`).
  - Test de legibilidad a **120 px de ancho** superado e iluminación perimetral esmeralda contra el modo oscuro de YouTube (`#0f0f0f`).

---

## 4. Descripción Oficial de YouTube (SEO Optimizada)

```text
Getting a red "spawn uvx ENOENT", "spawn npx ENOENT", or "MCP error -32000: Connection closed" in Cursor? Here is the 10-second fix when your Cursor MCP server is not working on Windows or Mac, even though the exact same command runs fine in your terminal.

Why does this happen? Cursor is a standalone desktop GUI app—it often fails to inherit your terminal's shell PATH environment variable (breaking uvx, Node, Python, or NVM), and on Windows it cannot spawn batch wrappers like npx.cmd directly without an extension or cmd /c.

Instead of watching a 30-minute tutorial to find a 10-second path fix, here is the exact step-by-step solution to get your Cursor Model Context Protocol (MCP) servers connected in green:

1. Find the full executable path in your terminal:
In Windows PowerShell, run "where.exe uvx" or "where.exe npx" (always include the .exe extension in PowerShell so it runs the system binary instead of the Where-Object alias). On macOS or Linux, run "which uvx" or "which npx".

2. Update your .cursor/mcp.json configuration file:
Paste the full absolute executable path into the "command" field of your .cursor/mcp.json file using double backslashes on Windows (for example, pointing directly to uvx.exe or npx.cmd), or wrap Windows batch scripts using "cmd" with "/c" and "npx" inside your args array.

3. Reload your MCP Server in Cursor Settings:
Save your mcp.json config, open Cursor Settings (Customize > MCPs), and click Reload. Your MCP server will immediately switch from "Error - Show Output" / "MCP error -32000: Connection closed" to Connected (Green) with all tools loaded and ready for your AI coding agent.

Errors covered and resolved in this video:
- Cursor MCP spawn uvx ENOENT / spawn npx ENOENT
- Cursor MCP error -32000: Connection closed
- Cursor MCP Client closed / Failed to create client
- Cursor MCP server red dot / Error - Show Output in Cursor 3.19+
- PowerShell where vs where.exe PATH resolution for astral uv and Node NVM

#Cursor #MCP #ModelContextProtocol #CursorAI #AICoding #CodingTips #WebDevelopment #DevTools #WindowsDev #SoftwareEngineering
```

---

## 5. Etiquetas / Tags (Casilla de Etiquetas de YouTube Studio — 488/500 caracteres)

```text
cursor mcp error, fix cursor mcp server, cursor spawn enoent, spawn uvx enoent, spawn npx enoent, mcp error -32000 connection closed, cursor mcp not working, cursor mcp client closed, cursor mcp failed to create client, cursor mcp.json windows, cursor mcp red dot, where.exe uvx, where.exe npx, model context protocol cursor, cursor ide mcp setup, cursor mcp server error fix, mcp-server-sqlite cursor
```

---

## 6. Checklist Previo a Publicación (§8 `PUBLICACION.md`)

- [x] **Video Render:** 1080p60 exacto (`53.04 s`), sin caídas de framerate ni artefactos visuales.
- [x] **Jump-Cut Quirúrgico:** Eliminado el tramo `24.5s–47.0s` de `clip_02`, empalmando limpiamente con la ruta absoluta en `mcp.json`.
- [x] **Normalización de Audio:** `-14.02 LUFS` EBU R128 (`-c:v copy`).
- [x] **Música de fondo:** `-18.0 dB` relativo a la voz con fade-in de 1.5s y fade-out de 2.5s.
- [x] **Sincronización:** Cada tramo cierra exactamente `1.10 s` tras la última palabra hablada (Regla 11 bis).
- [x] **Subtítulos:** Archivo `.srt` sincronizado por Whisper y alineado 100% con el guion oficial.
- [x] **Miniatura:** `1280x720`, `< 2048 KB` (`150.5 KB`), legible a `120 px`, bordes iluminados contra `#0f0f0f`.
- [x] **Seguridad (Regla 12):** Cero nombres de usuario, cero rutas personales (`C:\Tools\uv\uvx.exe` y prompt limpio `PS cursor_mcp_demo>`), cero claves API.

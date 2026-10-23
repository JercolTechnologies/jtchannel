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

### Opción Principal (Recomendada — 44 caracteres):
**`Fix Cursor MCP Server Errors: The ENOENT Fix`**

- **Front-loading:** `Fix Cursor MCP Server Errors` en los primeros 28 caracteres.
- **Recuento de keywords en la locución (§2 `PUBLICACION.md`):**
  - *Cursor:* Tramo 01 (2 veces), Tramo 02 (1 vez) — Total: 3 menciones.
  - *MCP server:* Tramo 01, Tramo 03 — Total: 2 menciones (+ `mcp.json` en Tramo 02).
  - *ENOENT / error:* Tramo 01 (*"fails with a red 'spawn ENOENT' error"*).
  - *Fix:* Tramo 02 (*"The fix takes ten seconds"*), Tramo 03 (*"zero-fluff dev fixes"*).

### Opciones Alternativas (41–55 caracteres):
1. `Cursor MCP spawn ENOENT Error: 10-Second Fix` (44 caracteres)
2. `How to Fix Cursor MCP Server Connection Errors` (46 caracteres)
3. `Fix Cursor MCP Server Red Error (uvx & npx)` (43 caracteres)

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

## 4. Descripción Oficial de YouTube

```text
Getting a red "spawn uvx ENOENT", "spawn npx ENOENT", or "MCP error -32000: Connection closed" when adding an MCP server in Cursor? Here is the exact 10-second fix for Windows and Mac.

Even when uvx or npx works fine in your integrated terminal, Cursor is a desktop GUI application—meaning it often fails to inherit your shell's PATH or tries to spawn Windows .cmd wrappers without an extension.

---
⚡ STEP 1: FIND THE FULL EXECUTABLE PATH
In Windows PowerShell (make sure to include .exe so PowerShell doesn't trigger the Where-Object alias):
where.exe uvx
where.exe npx

On macOS / Linux:
which uvx
which npx

---
🛠️ STEP 2: UPDATE .cursor/mcp.json WITH DOUBLE BACKSLASHES
Replace the bare command name with the full absolute path (using double backslashes \\ on Windows):

{
  "mcpServers": {
    "sqlite": {
      "command": "C:\\Tools\\uv\\uvx.exe",
      "args": [
        "mcp-server-sqlite",
        "--db-path",
        "./test.db"
      ]
    }
  }
}

Save the file, click Reload in Cursor Settings > MCP, and your server will immediately light up green with all tools loaded.

---
🧰 VERSIONS TESTED:
• Cursor IDE 3.19.7
• uv / uvx 0.13.5 (mcp-server-sqlite)
• Windows 11 PowerShell

#Cursor #MCP #ModelContextProtocol #AI #Coding #CursorAI #WebDev #DevTools
```

---

## 5. Etiquetas / Tags (Indexador de YouTube)

```text
cursor mcp error, cursor spawn enoent, fix cursor mcp server, mcp error -32000 connection closed, cursor uvx enoent, cursor npx enoent, model context protocol cursor, cursor mcp.json windows, cursor mcp not working, where.exe uvx, cursor ide mcp setup, mcp-server-sqlite cursor, ai coding agent, cursor 2026 tutorial
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

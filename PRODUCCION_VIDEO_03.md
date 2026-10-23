# PRODUCCION_VIDEO_03.md — Especificación de Montaje y Guion

Este documento contiene la **especificación completa, guion de narración y directivas técnicas verificadas (22/10/2026)** para montar el tercer vídeo del canal.

---

## ⚠️ DIRECTIVA DE CARPETAS PARA EL AGENTE ENSAMBLADOR

Siguiendo el estándar de nomenclatura descriptiva establecido en el proyecto, todos los assets de este vídeo deben alojarse en carpetas con el slug `cursor_mcp_enoent_fix`:

```text
clips/
└── cursor_mcp_enoent_fix/       # Grabaciones de pantalla de este vídeo (clip_01 a clip_03)

output/
└── cursor_mcp_enoent_fix/       # Renders temporales y master final

assets/videos/
└── cursor_mcp_enoent_fix/       # thumbnail.jpg (<2048 KB), subtitulos_video_03.srt y metadata.md

scripts/
└── cursor_mcp_enoent_fix/       # Scripts de montaje específicos para este vídeo
```

---

## 1. Ficha Técnica y Empaque

- **Título Oficial (44 caracteres):**  
  `Fix Cursor MCP Server Errors: The ENOENT Fix`  
  *(Cumple regla de front-loading estricto: `Fix Cursor MCP Server Errors` al inicio).*
- **Texto de Miniatura (3 palabras):**  
  `FIX CURSOR MCP`  
  *(Concepto visual artesanal: A la izquierda, panel real de Cursor MCP con el punto rojo y `spawn ENOENT`; a la derecha, el bloque de código limpio de `mcp.json` con la ruta absoluta / `cmd /c` convirtiendo el indicador en verde esmeralda `#3ECF8E`).*
- **Formato:** Horizontal 16:9 (`1920x1080`, 60 fps).
- **Versiones verificadas en grabación (22/10/2026):**
  - **Cursor:** `3.19.7` (configuración oficial mediante `.cursor/mcp.json`).
  - **uv / uvx:** `0.13.5` (`astral-sh.uv`).
  - **Node / npx:** `npx.cmd` vía NVM for Windows.
- **Voz TTS:** `nova` en `gpt-4o-mini-tts`.
- **Evolución sonora:**
  - Narración masterizada a **`-14.0 LUFS`** (EBU R128) con doble pasada de `loudnorm` en FFmpeg (`-c:v copy`).
  - Música de fondo a **`-18.0 dB` relativo** a la voz con fade-in y fade-out (según ADR-004).
- **Corte dinámico:** Remate de vídeo entre **1.0 y 1.2 segundos** tras la última palabra hablada (según ADR-002 y Regla 11 bis de `GEMINI.md`).

---

## 2. Configuración Exacta a Mostrar en Pantalla

### A. El Error en Cursor (`Cursor Settings > MCP` + `.cursor/mcp.json`)
Configuración inicial que falla con punto rojo (`spawn uvx ENOENT` o `spawn npx ENOENT`):
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### B. El Comando en PowerShell para Extraer la Ruta Exacta
En la terminal integrada (PowerShell), evitando la trampa del alias `where` (`Where-Object`):
```powershell
where.exe uvx
where.exe npx
```

### C. La Doble Corrección Definitiva en `.cursor/mcp.json`
1. **Para ejecutables como `uvx.exe` (o en Mac/Linux con `which`):** Pegar la ruta absoluta escapando las barras `\\`.
2. **Para paquetes `npx` en Windows (donde `npx` es un script `.cmd`):** Usar la ruta completa a `npx.cmd` o envolver con `cmd /c`:
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "C:\\Users\\dev\\AppData\\Local\\Microsoft\\WinGet\\Links\\uvx.exe",
      "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
    },
    "memory": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```
Al guardar `mcp.json` y refrescar en el panel MCP de Cursor, ambos servidores pasan inmediatamente a **verde (`Enabled / Connected`)** con todas las herramientas cargadas.

---

## 3. Desglose de Tramos y Guion de Narración (`nova`)

### Tramo 01: El Fallo Visual y la Paradoja de la Terminal (The Hook)
- **Duración estimada:** ~18 segundos.
- **Acción visual en pantalla (Miguel):**  
  Abre Cursor mostrando la ventana dividida: a la izquierda el panel **Cursor Settings > MCP** con el servidor en rojo (`Failed to connect: spawn ENOENT`) y a la derecha el archivo `.cursor/mcp.json`. En la terminal inferior escribe `uvx --version` (o `npx --version`) y responde al instante con la versión instalada.
- **Texto de locución TTS (Inglés):**  
  > *"You just added an MCP server to Cursor, and it immediately fails with a red 'spawn ENOENT' error. Yet when you run the exact same command in your terminal, it works fine. Why does Cursor think it doesn't exist?"*

---

### Tramo 02: La Causa Raíz, `where.exe` y el Fix en `mcp.json`
- **Duración estimada:** ~30 segundos.
- **Acción visual en pantalla (Miguel):**  
  En la terminal PowerShell, ejecuta `where.exe uvx` y `where.exe npx`. Selecciona la ruta completa de `uvx.exe`, la pega en `"command"` dentro de `mcp.json` con doble barra `\\`, y en el servidor de `npx` añade `"command": "cmd"` con `"/c", "npx"` en `"args"`. Guarda el archivo (`Ctrl+S`).
- **Texto de locución TTS (Inglés):**  
  > *"Cursor is a desktop GUI app—it often fails to inherit your terminal's shell PATH, and on Windows it can't spawn batch scripts like npx directly. The fix takes ten seconds. In PowerShell, run 'where.exe uvx'—don't forget the dot-exe—or 'which' on Mac, and paste the full path into mcp.json. And for npx on Windows, just wrap it with 'cmd /c'."*

---

### Tramo 03: Reconexión en Verde y Verificación de Herramientas
- **Duración estimada:** ~20 segundos.
- **Acción visual en pantalla (Miguel):**  
  En el panel MCP de Cursor hace clic en el botón de refrescar. El indicador rojo cambia inmediatamente a **verde brillante** mostrando las herramientas cargadas (*tools enabled*).
- **Texto de locución TTS (Inglés):**  
  > *"Save your config, hit refresh, and boom: your MCP servers light up green with all tools loaded and ready for your agent. If this saved your build, drop a like and subscribe for more zero-fluff dev fixes."*

---

## 4. Checklist de Seguridad y Producción (Regla 12 de `GEMINI.md`)

- [x] **Cero secretos:** Este vídeo no utiliza claves de API ni bases de datos en la nube.
- [x] **Privacidad de ruta en Windows:** Si en la ruta absoluta aparece el usuario local (`C:\Users\mapog\...`), sanitizar con `drawbox` en FFmpeg (según ADR-005) o usar una variable/ruta limpia (`C:\Tools\uv\uvx.exe` + prompt `PS cursor_mcp_demo>`).
- [x] **Desinstalación post-grabación:** Una vez aprobado el máster del vídeo, desinstalar `Anysphere.Cursor` y `astral-sh.uv` vía `winget uninstall`.

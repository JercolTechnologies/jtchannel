# -*- coding: utf-8 -*-
"""
Generación de audios TTS para Video 03:
Fix Cursor MCP Server Errors: The ENOENT Fix (cursor_mcp_enoent_fix)

Modelo: gpt-4o-mini-tts
Voz: nova
"""

import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AUDIOS_DIR = Path("output/cursor_mcp_enoent_fix/audios")
AUDIOS_DIR.mkdir(parents=True, exist_ok=True)

TRAMOS = [
    {
        "id": "tramo_01",
        "title": "El Fallo Visual y la Paradoja de la Terminal",
        "text": (
            "You just added an MCP server to Cursor, and it immediately fails with a red "
            "'spawn ENOENT' error. Yet when you run the exact same command in your terminal, "
            "it works fine. Why does Cursor think it doesn't exist?"
        ),
    },
    {
        "id": "tramo_02",
        "title": "La Causa Raíz, where.exe y el Fix en mcp.json",
        "text": (
            "Cursor is a desktop GUI app—it often fails to inherit your terminal's PATH, "
            "or tries to spawn Windows dot-cmd wrappers like npx without an extension. "
            "The fix takes ten seconds. In PowerShell, run 'where.exe uvx' or 'where.exe npx'—"
            "don't forget the dot-exe—then paste the full executable path into mcp.json "
            "with double backslashes."
        ),
    },
    {
        "id": "tramo_03",
        "title": "Reconexión en Verde y Verificación de Herramientas",
        "text": (
            "Save your config, hit Reload, and boom: your MCP server lights up green "
            "with all six tools loaded and ready for your agent. If this saved your build, "
            "drop a like and subscribe for more zero-fluff dev fixes."
        ),
    },
]

# Mantenemos exactamente las mismas instrucciones de tono que en Video 01 y Video 02 para consistencia de canal
INSTRUCCIONES_TONO = (
    "Speak in an enthusiastic, cheerful, friendly, and energetic conversational tone like talking with developer friends. "
    "Natural upbeat pacing with clear pauses, engaging and relatable, no stiff or monotone lecture."
)


def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def generar_todos():
    client = OpenAI()
    print("=" * 60)
    print("GENERACIÓN DE AUDIOS TTS — VIDEO 03 (gpt-4o-mini-tts / nova)")
    print("=" * 60)

    resultados = []
    duracion_total = 0.0

    for tramo in TRAMOS:
        ruta_mp3 = AUDIOS_DIR / f"{tramo['id']}.mp3"
        print(f"Generando [{tramo['id']}] {tramo['title']}...", end=" ", flush=True)

        resp = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=tramo["text"],
            instructions=INSTRUCCIONES_TONO,
            response_format="mp3",
        )
        resp.write_to_file(ruta_mp3)

        dur = medir_duracion(ruta_mp3)
        duracion_total += dur
        print(f"OK ({dur:.2f} s)")

        resultados.append({
            "id": tramo["id"],
            "title": tramo["title"],
            "path": str(ruta_mp3),
            "duration": dur,
            "text": tramo["text"],
        })

    print("-" * 60)
    print(f"Duración total de locución: {duracion_total:.2f} s ({duracion_total/60:.2f} min)")
    print("=" * 60)

    manifest_path = AUDIOS_DIR / "manifest_audios.json"
    manifest_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifiesto guardado en: {manifest_path}")


if __name__ == "__main__":
    generar_todos()

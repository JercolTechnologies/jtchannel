# -*- coding: utf-8 -*-
"""
Edición preliminar del Tramo 04 (Clip 05 sin TTS):
1. Corta Parte 1: [02.0s -> 22.0s] (Supabase: proyectos -> YT Demos -> Database -> Schema Visualizer).
2. Salta los 4s muertos de búsqueda [22.0s -> 26.0s].
3. Corta Parte 2: [26.0s -> 41.5s] (Antigravity mostrando datos y esquema + regreso a Supabase antes de OBS).
4. Concatena a 1080p60 en 'output/tramo_04_editado.mp4' para que Miguel lo revise antes del TTS.
"""

import subprocess
from pathlib import Path

CLIP_05 = Path("clips/05_showing_the_schema_created.mp4")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_EDITADO = OUTPUT_DIR / "tramo_04_editado.mp4"

TEMP_DIR = OUTPUT_DIR / "temp_tramo_04"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

part1_mp4 = TEMP_DIR / "p1.mp4"
part2_mp4 = TEMP_DIR / "p2.mp4"
concat_txt = TEMP_DIR / "concat.txt"

print("\n--- Cortando Parte 1 (Supabase Schema Visualizer) [2.0s -> 22.0s] ---")
cmd_p1 = [
    "ffmpeg", "-y", "-v", "error",
    "-ss", "2.0",
    "-i", str(CLIP_05),
    "-t", "20.0",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-r", "60", "-pix_fmt", "yuv420p",
    "-an",
    str(part1_mp4),
]
subprocess.run(cmd_p1, check=True)

print("--- Cortando Parte 2 (Antigravity match + vuelta a Supabase) [26.0s -> 41.5s] ---")
cmd_p2 = [
    "ffmpeg", "-y", "-v", "error",
    "-ss", "26.0",
    "-i", str(CLIP_05),
    "-t", "15.5",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-r", "60", "-pix_fmt", "yuv420p",
    "-an",
    str(part2_mp4),
]
subprocess.run(cmd_p2, check=True)

concat_txt.write_text(
    f"file '{part1_mp4.resolve().as_posix()}'\nfile '{part2_mp4.resolve().as_posix()}'\n",
    encoding="utf-8"
)

print(f"--- Concatenando en {VIDEO_EDITADO.name} ---")
cmd_concat = [
    "ffmpeg", "-y", "-v", "error",
    "-f", "concat", "-safe", "0",
    "-i", str(concat_txt),
    "-c:v", "copy",
    str(VIDEO_EDITADO),
]
subprocess.run(cmd_concat, check=True)

# Limpieza temporales
part1_mp4.unlink(missing_ok=True)
part2_mp4.unlink(missing_ok=True)
concat_txt.unlink(missing_ok=True)
TEMP_DIR.rmdir()

# Medir duración
cmd_dur = [
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    str(VIDEO_EDITADO),
]
r = subprocess.run(cmd_dur, capture_output=True, text=True, check=True)
dur = float(r.stdout.strip())

print(f"\n[ÉXITO] Vídeo editado listo: {VIDEO_EDITADO} (duración: {dur:.2f} s)")

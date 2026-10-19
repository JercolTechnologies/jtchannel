# -*- coding: utf-8 -*-
"""
Montaje completo del Tramo 01 — Video 02:
Raw Supabase Vector Search: The Hook (LangChain Bloat Deletion)

1. Edita el clip_01.mp4 con sincronización exacta al guion:
   - 0.00s a 9.50s: Código sobrecargado de LangChain visible ("Every AI influencer... complete hype... Postgres").
   - 9.50s a 12.00s: Selección Ctrl+A en azul ("Today we're doing raw vector search in Supabase...").
   - 12.00s a 16.80s: Borrado con Backspace a editor limpio ("...with zero frameworks and just four lines of code").
   - Remate a 16.80s: Exactamente 1.14s tras la última palabra hablada (15.66s), cumpliendo Regla 11 bis.
2. Muxea con el audio TTS (tramo_01.mp3).
3. Normaliza con doble pasada de loudnorm a -14.0 LUFS con -c:v copy.
4. Ficha técnica verificada con ffprobe.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

CLIP_ENTRADA = Path("clips/raw_supabase_vector_search/clip_01.mp4")
AUDIO_ENTRADA = Path("output/raw_supabase_vector_search/audios/tramo_01.mp3")
OUT_DIR = Path("output/raw_supabase_vector_search")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_EDITADO = OUT_DIR / "tramo_01_editado_temp.mp4"
VIDEO_MUX = OUT_DIR / "tramo_01_mux_temp.mp4"
VIDEO_FINAL = OUT_DIR / "tramo_01_completo.mp4"

DUR_TOTAL = 16.80

def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def editar_video():
    print(f"\n1. Editando vídeo base desde {CLIP_ENTRADA.name}...")
    
    # Segmento 0: 0.8s a 3.5s (2.7s de código original) + 6.8s pad = 9.5s
    # Segmento 1: 3.5s a 5.5s (2.0s de Ctrl+A) ajustado a 2.5s (9.5s a 12.0s)
    # Segmento 2: 5.6s a 9.3s (3.7s de editor limpio) + 1.1s pad = 4.8s (12.0s a 16.8s)
    filter_complex = (
        "[0:v]trim=start=0.8:end=3.5,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=6.8[v0];"
        "[0:v]trim=start=3.5:end=5.5,setpts=(PTS-STARTPTS)*1.25[v1];"
        "[0:v]trim=start=5.6:end=9.3,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[vout]"
    )
    
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(CLIP_ENTRADA),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-r", "60",
        "-pix_fmt", "yuv420p",
        "-an",
        str(VIDEO_EDITADO),
    ]
    subprocess.run(cmd, check=True)
    dur = medir_duracion(VIDEO_EDITADO)
    print(f"   Vídeo editado OK: {dur:.2f} s")

def mux_audio():
    print("\n2. Muxeando vídeo con locución TTS...")
    # Pad audio con silencio hasta 16.80s
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(VIDEO_EDITADO),
        "-i", str(AUDIO_ENTRADA),
        "-filter_complex", f"[1:a]apad=whole_dur={DUR_TOTAL}[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        str(VIDEO_MUX),
    ]
    subprocess.run(cmd, check=True)
    print(f"   Mux inicial completado.")

def normalizar_loudnorm():
    print("\n3. Normalizando audio a -14.0 LUFS (EBU R128)...")
    filtro_base = "loudnorm=I=-14.0:LRA=7.0:TP=-1.5:print_format=json"
    
    # Pasada 1: Medición
    cmd_medir = [
        "ffmpeg", "-v", "error",
        "-i", str(VIDEO_MUX),
        "-af", filtro_base,
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd_medir, capture_output=True, text=True)
    salida = res.stderr
    ini = salida.find("{")
    fin = salida.rfind("}")
    
    if ini == -1 or fin == -1:
        print("   [AVISO] No se pudo parsear JSON de loudnorm, usando pasada simple.")
        filtro_aplicar = filtro_base
    else:
        datos = json.loads(salida[ini:fin + 1])
        filtro_aplicar = (
            f"{filtro_base}:measured_I={datos['input_i']}:measured_LRA={datos['input_lra']}:"
            f"measured_TP={datos['input_tp']}:measured_thresh={datos['input_thresh']}:"
            f"offset={datos['target_offset']}:linear=true"
        )
    
    # Pasada 2: Aplicación con -c:v copy
    cmd_aplicar = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(VIDEO_MUX),
        "-c:v", "copy",
        "-af", filtro_aplicar,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        str(VIDEO_FINAL),
    ]
    subprocess.run(cmd_aplicar, check=True)
    print(f"   Master normalizado guardado en: {VIDEO_FINAL.name}")

def verificar():
    print("\n" + "=" * 60)
    print(" VERIFICACIÓN TÉCNICA DEL TRAMO 01 (ffprobe)")
    print("=" * 60)
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size",
        "-show_streams", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames",
        "-of", "json",
        str(VIDEO_FINAL),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(res.stdout)
    
    # Limpiar temporales
    VIDEO_EDITADO.unlink(missing_ok=True)
    VIDEO_MUX.unlink(missing_ok=True)

if __name__ == "__main__":
    editar_video()
    mux_audio()
    normalizar_loudnorm()
    verificar()

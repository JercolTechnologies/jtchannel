# -*- coding: utf-8 -*-
"""
Montaje de Tramos 02, 03, 04 y 05 — Video 02:
Raw Supabase Vector Search

Alineación exacta de tiempos según Rule 11 bis (1.0s - 1.2s de cola):
- Tramo 02: Duración 15.05s (Voz termina en 13.92s -> Cola de 1.13s)
- Tramo 03: Duración 11.20s (Voz termina en 10.08s -> Cola de 1.12s)
- Tramo 04: Duración 20.20s (Voz termina en 19.06s -> Cola de 1.14s)
- Tramo 05: Duración 17.50s (Voz termina en 16.40s -> Cola de 1.10s)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

OUT_DIR = Path("output/raw_supabase_vector_search")
AUDIOS_DIR = OUT_DIR / "audios"

CLIPS = {
    "clip_02": Path("clips/raw_supabase_vector_search/clip_02.mp4"),
    "clip_02_b": Path("clips/raw_supabase_vector_search/clip_02_b.mp4"),
    "clip_03": Path("clips/raw_supabase_vector_search/clip_03.mp4"),
}

def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def normalizar_loudnorm(video_in: Path, video_out: Path):
    filtro_base = "loudnorm=I=-14.0:LRA=7.0:TP=-1.5:print_format=json"
    cmd_medir = [
        "ffmpeg", "-i", str(video_in),
        "-af", filtro_base,
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd_medir, capture_output=True, text=True)
    salida = res.stderr
    ini = salida.find("{")
    fin = salida.rfind("}")
    
    if ini == -1 or fin == -1:
        filtro_aplicar = filtro_base
    else:
        datos = json.loads(salida[ini:fin + 1])
        filtro_aplicar = (
            f"{filtro_base}:measured_I={datos['input_i']}:measured_LRA={datos['input_lra']}:"
            f"measured_TP={datos['input_tp']}:measured_thresh={datos['input_thresh']}:"
            f"offset={datos['target_offset']}:linear=true"
        )
    
    cmd_aplicar = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_in),
        "-c:v", "copy",
        "-af", filtro_aplicar,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        str(video_out),
    ]
    subprocess.run(cmd_aplicar, check=True)

# -------------------------------------------------------------
# TRAMO 02: Supabase Setup (SQL Editor)
# -------------------------------------------------------------
def montar_tramo_02():
    print("\n--- Montando Tramo 02: Supabase Setup ---")
    clip = CLIPS["clip_02"]
    audio = AUDIOS_DIR / "tramo_02.mp3"
    video_edit = OUT_DIR / "tramo_02_edit_temp.mp4"
    video_mux = OUT_DIR / "tramo_02_mux_temp.mp4"
    video_final = OUT_DIR / "tramo_02_completo.mp4"
    dur_total = 15.05

    # 1.0s a 8.6s (7.6s) -> ajustado a 10.5s con tpad
    # 8.6s a 12.5s (3.9s) -> ajustado a 4.55s con tpad
    filter_complex = (
        "[0:v]trim=start=1.0:end=8.6,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2.9[v0];"
        "[0:v]trim=start=8.6:end=12.5,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.65[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[vout]"
    )
    
    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", "60", "-pix_fmt", "yuv420p", "-an",
        str(video_edit)
    ]
    subprocess.run(cmd_v, check=True)

    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_edit),
        "-i", str(audio),
        "-filter_complex", f"[1:a]apad=whole_dur={dur_total}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", str(video_mux)
    ]
    subprocess.run(cmd_mux, check=True)

    normalizar_loudnorm(video_mux, video_final)
    video_edit.unlink(missing_ok=True)
    video_mux.unlink(missing_ok=True)
    print(f"Tramo 02 listo: {video_final.name} ({medir_duracion(video_final):.2f}s)")

# -------------------------------------------------------------
# TRAMO 03: Seeded Data Bridge (Table Editor)
# -------------------------------------------------------------
def montar_tramo_03():
    print("\n--- Montando Tramo 03: Seeded Data Bridge ---")
    clip = CLIPS["clip_02_b"]
    audio = AUDIOS_DIR / "tramo_03.mp3"
    video_edit = OUT_DIR / "tramo_03_edit_temp.mp4"
    video_mux = OUT_DIR / "tramo_03_mux_temp.mp4"
    video_final = OUT_DIR / "tramo_03_completo.mp4"
    dur_total = 11.20

    # 0.7s a 4.5s (3.8s) navega a Table Editor -> setpts / 1.08 = 3.5s
    # 4.5s a 12.2s (7.7s) muestra tabla con datos y vectores -> 7.7s
    filter_complex = (
        "[0:v]trim=start=0.7:end=4.5,setpts=(PTS-STARTPTS)/1.08[v0];"
        "[0:v]trim=start=4.5:end=12.2,setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[vout]"
    )

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", "60", "-pix_fmt", "yuv420p", "-an",
        str(video_edit)
    ]
    subprocess.run(cmd_v, check=True)

    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_edit),
        "-i", str(audio),
        "-filter_complex", f"[1:a]apad=whole_dur={dur_total}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", str(video_mux)
    ]
    subprocess.run(cmd_mux, check=True)

    normalizar_loudnorm(video_mux, video_final)
    video_edit.unlink(missing_ok=True)
    video_mux.unlink(missing_ok=True)
    print(f"Tramo 03 listo: {video_final.name} ({medir_duracion(video_final):.2f}s)")

# -------------------------------------------------------------
# TRAMO 04: Python & Cosine Distance Operator
# -------------------------------------------------------------
def montar_tramo_04():
    print("\n--- Montando Tramo 04: Python & Cosine Distance ---")
    clip = CLIPS["clip_03"]
    audio = AUDIOS_DIR / "tramo_04.mp3"
    video_edit = OUT_DIR / "tramo_04_edit_temp.mp4"
    video_mux = OUT_DIR / "tramo_04_mux_temp.mp4"
    video_final = OUT_DIR / "tramo_04_completo.mp4"
    dur_total = 20.20

    # 0.7s a 12.0s (11.3s) recorrido del código Python -> setpts * 1.59 = 18.0s
    # 12.0s a 13.0s (1.0s) enter en terminal -> setpts * 2.2 = 2.2s
    filter_complex = (
        "[0:v]trim=start=0.7:end=12.0,setpts=(PTS-STARTPTS)*1.59[v0];"
        "[0:v]trim=start=12.0:end=13.0,setpts=(PTS-STARTPTS)*2.20[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[vout]"
    )

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", "60", "-pix_fmt", "yuv420p", "-an",
        str(video_edit)
    ]
    subprocess.run(cmd_v, check=True)

    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_edit),
        "-i", str(audio),
        "-filter_complex", f"[1:a]apad=whole_dur={dur_total}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", str(video_mux)
    ]
    subprocess.run(cmd_mux, check=True)

    normalizar_loudnorm(video_mux, video_final)
    video_edit.unlink(missing_ok=True)
    video_mux.unlink(missing_ok=True)
    print(f"Tramo 04 listo: {video_final.name} ({medir_duracion(video_final):.2f}s)")

# -------------------------------------------------------------
# TRAMO 05: Result, Digital Terminal Zoom & Outro
# -------------------------------------------------------------
def montar_tramo_05():
    print("\n--- Montando Tramo 05: Result, Terminal Zoom & Outro ---")
    clip = CLIPS["clip_03"]
    audio = AUDIOS_DIR / "tramo_05.mp3"
    video_edit = OUT_DIR / "tramo_05_edit_temp.mp4"
    video_mux = OUT_DIR / "tramo_05_mux_temp.mp4"
    video_final = OUT_DIR / "tramo_05_completo.mp4"
    dur_total = 17.50

    # In clip_03, 23.8s is right when "Top Match: Tesla Model 3" prints.
    # 23.8s to 34.5s (10.7s useful clean footage showing output).
    # Choreography:
    # Seg 0: 23.8s to 29.8s (6.0s) -> Con zoom digital a la terminal (crop en terminal escalado a 1080p)
    # Terminal crop en 1920x1080: terminal prompt y Top Match están en x: 0..1200, y: 550..1080
    # Zoom de 1.25x en x=0, y=250 escalado a 1920x1080
    # Seg 1: 29.8s a 34.5s (4.7s) + 6.8s pad = 11.5s -> Plano general limpio para tarjetas de YouTube (Outro)
    filter_complex = (
        "[0:v]trim=start=23.8:end=29.8,setpts=PTS-STARTPTS,"
        "crop=w=1536:h=864:x=0:y=216,scale=1920:1080:flags=bicubic[v_zoom];"
        "[0:v]trim=start=29.8:end=34.5,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=6.8[v_full];"
        "[v_zoom][v_full]concat=n=2:v=1:a=0[vout]"
    )

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", "60", "-pix_fmt", "yuv420p", "-an",
        str(video_edit)
    ]
    subprocess.run(cmd_v, check=True)

    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_edit),
        "-i", str(audio),
        "-filter_complex", f"[1:a]apad=whole_dur={dur_total}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", str(video_mux)
    ]
    subprocess.run(cmd_mux, check=True)

    normalizar_loudnorm(video_mux, video_final)
    video_edit.unlink(missing_ok=True)
    video_mux.unlink(missing_ok=True)
    print(f"Tramo 05 listo: {video_final.name} ({medir_duracion(video_final):.2f}s)")

if __name__ == "__main__":
    montar_tramo_02()
    montar_tramo_03()
    montar_tramo_04()
    montar_tramo_05()

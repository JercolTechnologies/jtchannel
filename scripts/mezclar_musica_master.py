# -*- coding: utf-8 -*-
"""
Mezcla de la cama musical (The_Iron_Grove / musica.mp3) sobre el máster de vídeo
(tutorial_supabase_mcp_completo.mp4) siguiendo los principios de assembler.py (ADR-016):

1. La voz es el ancla: se mide la sonoridad percibida (LUFS) de la voz del máster.
2. Se mide la pista de música en LUFS.
3. Se calcula la ganancia exacta para que la música quede 'DEBAJO_DB' por debajo de la voz (default: -18 dB).
4. Si el vídeo es más largo que la música (153.7s vs 151.1s), se loopea la música para cubrir los últimos segundos.
5. Se aplican fundidos: Fade-in suave de 1.5s y Fade-out de 2.5s al final.
6. Se mezcla con 'amix' (sin atenuar la voz) y se normaliza el máster final en doble pasada con 'loudnorm'
   (-14.0 LUFS, -1.5 dBTP, ganancia lineal) manteniendo el vídeo intacto (-c:v copy).
"""

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

VIDEO_MASTER = Path("output/tutorial_supabase_mcp_completo.mp4")
MUSICA_PISTA = Path("assets/videos/video_01/musica.mp3")
OUTPUT_MASTER = Path("output/tutorial_supabase_mcp_con_musica.mp4")

DEBAJO_DB = 18.0       # Decibelios que la música queda por debajo de la narración
FADE_IN_S = 1.5        # Duración del fade-in de música al inicio
FADE_OUT_S = 2.5       # Duración del fade-out de música al final
TARGET_LUFS = -14.0    # Estándar YouTube
TARGET_TP = -1.5       # Techo de picos (True Peak)
TARGET_LRA = 7.0


def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def medir_lufs(ruta: Path) -> Optional[float]:
    """Mide la sonoridad integrada en LUFS de un archivo de audio o vídeo."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(ruta),
        "-vn",
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not m:
        return None
    try:
        data = json.loads(m[-1])
        v = float(data["input_i"])
        return None if v < -70 else v
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def calcular_ganancia(voz_lufs: float, mus_lufs: float, debajo_db: float) -> Tuple[float, float]:
    """
    Calcula el multiplicador lineal de ganancia y el objetivo en LUFS.
    objetivo = voz_lufs - debajo_db
    ganancia = 10 ** ((objetivo - mus_lufs) / 20.0)
    """
    objetivo = voz_lufs - debajo_db
    ganancia = 10 ** ((objetivo - mus_lufs) / 20.0)
    return objetivo, ganancia


def medir_loudnorm_mezcla(
    video_path: Path,
    musica_path: Path,
    duracion_video: float,
    ganancia_musica: float,
) -> Optional[Dict[str, str]]:
    """
    Ejecuta la Pasada 1 de loudnorm sobre la mezcla en vivo de voz + música atenuada
    para obtener las estadísticas exactas de sonoridad y picos.
    """
    st_fadeout = max(0.0, duracion_video - FADE_OUT_S)
    filter_complex = (
        f"[0:a]aformat=channel_layouts=stereo[vox];"
        f"[1:a]atrim=0:{duracion_video:.3f},"
        f"afade=t=in:ss=0:d={FADE_IN_S},"
        f"afade=t=out:st={st_fadeout:.3f}:d={FADE_OUT_S},"
        f"volume={ganancia_musica:.6f},"
        f"aformat=channel_layouts=stereo[mus];"
        f"[vox][mus]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[mix];"
        f"[mix]loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}:print_format=json"
    )

    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(musica_path),
        "-filter_complex", filter_complex,
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not m:
        return None
    try:
        return json.loads(m[-1])
    except Exception:
        return None


def mezclar_y_normalizar(
    video_path: Path,
    musica_path: Path,
    output_path: Path,
    duracion_video: float,
    ganancia_musica: float,
    medidas_pasada1: Optional[Dict[str, str]],
):
    """
    Ejecuta la Pasada 2 aplicando la mezcla de audio, la normalización lineal EBU R128
    y el empaquetado del vídeo con -c:v copy.
    """
    st_fadeout = max(0.0, duracion_video - FADE_OUT_S)
    
    if medidas_pasada1:
        loudnorm_str = (
            f"loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}"
            f":measured_I={medidas_pasada1['input_i']}"
            f":measured_LRA={medidas_pasada1['input_lra']}"
            f":measured_TP={medidas_pasada1['input_tp']}"
            f":measured_thresh={medidas_pasada1['input_thresh']}"
            f":offset={medidas_pasada1['target_offset']}"
            f":linear=true:print_format=summary"
        )
    else:
        print("  [AVISO] Pasada 1 no disponible. Aplicando loudnorm dinámico en una pasada.")
        loudnorm_str = f"loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}"

    filter_complex = (
        f"[0:a]aformat=channel_layouts=stereo[vox];"
        f"[1:a]atrim=0:{duracion_video:.3f},"
        f"afade=t=in:ss=0:d={FADE_IN_S},"
        f"afade=t=out:st={st_fadeout:.3f}:d={FADE_OUT_S},"
        f"volume={ganancia_musica:.6f},"
        f"aformat=channel_layouts=stereo[mus];"
        f"[vox][mus]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[mix];"
        f"[mix]{loudnorm_str}[aout]"
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "info",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(musica_path),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] FFmpeg falló en la mezcla final:")
        print(res.stderr[-500:])
        sys.exit(1)


def main():
    print("\n" + "=" * 65)
    print(" MEZCLA DE MÚSICA MASTER & NORMALIZACIÓN LUFS (ADR-016)")
    print("=" * 65)

    if not VIDEO_MASTER.exists():
        print(f"[ERROR] No existe el vídeo máster: {VIDEO_MASTER}")
        sys.exit(1)
    if not MUSICA_PISTA.exists():
        print(f"[ERROR] No existe la pista de música: {MUSICA_PISTA}")
        sys.exit(1)

    dur_video = medir_duracion(VIDEO_MASTER)
    dur_musica = medir_duracion(MUSICA_PISTA)
    print(f"Vídeo máster:    {VIDEO_MASTER.name} ({dur_video:.2f} s)")
    print(f"Pista de música: {MUSICA_PISTA.name} ({dur_musica:.2f} s)")

    if dur_musica < dur_video:
        print(f"  -> La música es {dur_video - dur_musica:.2f} s más corta que el vídeo.")
        print(f"  -> Se aplicará bucle continuo (-stream_loop) hasta el final ({dur_video:.2f} s).")

    # Medición de sonoridad de la voz y música
    print("\n--- 1. Midiendo sonoridades (LUFS) ---")
    voz_lufs = medir_lufs(VIDEO_MASTER)
    mus_lufs = medir_lufs(MUSICA_PISTA)

    if voz_lufs is None or mus_lufs is None:
        print(f"[ERROR] No se pudo medir la sonoridad. voz={voz_lufs}, musica={mus_lufs}")
        sys.exit(1)

    print(f"  Sonoridad de la voz:   {voz_lufs:.2f} LUFS")
    print(f"  Sonoridad de la música:{mus_lufs:.2f} LUFS")

    # Cálculo de ganancia
    objetivo_lufs, ganancia = calcular_ganancia(voz_lufs, mus_lufs, DEBAJO_DB)
    ganancia_db = 20 * math.log10(ganancia)
    print(f"\n--- 2. Cálculo de atenuación de la música ---")
    print(f"  Objetivo de la música: {objetivo_lufs:.2f} LUFS ({DEBAJO_DB:.1f} dB por debajo de la voz)")
    print(f"  Ganancia calculada:    x{ganancia:.4f} ({ganancia_db:+.2f} dB)")
    print(f"  Fade In: {FADE_IN_S:.1f}s | Fade Out: {FADE_OUT_S:.1f}s (termina exactamente con el vídeo)")

    # Pasada 1: Medición de la mezcla
    print("\n--- 3. Pasada 1: Midiendo sonoridad de la mezcla (loudnorm) ---")
    medidas_p1 = medir_loudnorm_mezcla(VIDEO_MASTER, MUSICA_PISTA, dur_video, ganancia)
    if medidas_p1:
        print(f"  Mezcla preliminar: {medidas_p1.get('input_i')} LUFS | Pico: {medidas_p1.get('input_tp')} dBTP")
    else:
        print("  [AVISO] No se obtuvieron métricas de Pasada 1, usando fallback lineal.")

    # Pasada 2: Renderizado final con -c:v copy
    print(f"\n--- 4. Pasada 2: Generando {OUTPUT_MASTER.name} (-c:v copy) ---")
    mezclar_y_normalizar(VIDEO_MASTER, MUSICA_PISTA, OUTPUT_MASTER, dur_video, ganancia, medidas_p1)

    # Verificación final
    if not OUTPUT_MASTER.exists():
        print(f"[ERROR] No se generó {OUTPUT_MASTER}")
        sys.exit(1)

    dur_final = medir_duracion(OUTPUT_MASTER)
    lufs_final = medir_lufs(OUTPUT_MASTER)
    tam_mb = OUTPUT_MASTER.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 65)
    print(" VERIFICACIÓN TÉCNICA DEL MÁSTER FINAL CON MÚSICA")
    print("=" * 65)
    print(f"Archivo:          {OUTPUT_MASTER.resolve()}")
    print(f"Tamaño:           {tam_mb:.2f} MB")
    print(f"Duración vídeo:   {dur_final:.2f} s (coincidencia con original: {abs(dur_final - dur_video) < 0.05})")
    print(f"Sonoridad final:  {lufs_final:.2f} LUFS (Objetivo YouTube: {TARGET_LUFS:.1f} LUFS)")
    print("Video stream:     COPIADO SIN PÉRDIDA (-c:v copy)")
    print("Audio stream:     AAC 192k estéreo normalizado EBU R128")
    print("=" * 65)


if __name__ == "__main__":
    main()

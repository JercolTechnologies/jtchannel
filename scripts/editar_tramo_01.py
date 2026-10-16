# -*- coding: utf-8 -*-
"""
Monta el tramo 01 editado de prueba:
1. Elimina OBS al inicio (antes de 2.5s) y al final (después de 99.5s).
2. Elimina la pausa estática de lectura de permisos (54.0s a 70.5s).
3. Aplica aceleración moderada y fluida (1.3x) al rellenar el formulario.
4. Mantiene 1080p60 exacto.
"""

import subprocess
import sys
from pathlib import Path


def main():
    clip_entrada = Path("clips/01_generando_token_supabase.mp4")
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    clip_salida = out_dir / "tramo_01_editado.mp4"

    if not clip_entrada.exists():
        print(f"[ERROR] No existe el clip: {clip_entrada}")
        sys.exit(1)

    print(f"\nEditando '{clip_entrada.name}' -> '{clip_salida.name}'...")

    # Filtro complejo de ffmpeg:
    # Seg 0: 2.5s a 16.0s (1.0x) - Navegación a Tokens
    # Seg 1: 16.0s a 54.0s (1.33x) - Relleno de formulario y selección de permisos
    # (Se descarta el rango de 54.0s a 70.5s por ser pausa estática de 16s)
    # Seg 2: 70.5s a 91.0s (1.1x) - Clic en Create token, copiar clave, confirmar y Done
    # Seg 3: 91.0s a 99.5s (1.0x) - Token en lista y apertura de Antigravity
    filter_complex = (
        "[0:v]trim=start=2.5:end=16.0,setpts=PTS-STARTPTS[v0];"
        "[0:v]trim=start=16.0:end=54.0,setpts=(PTS-STARTPTS)/1.33[v1];"
        "[0:v]trim=start=70.5:end=91.0,setpts=(PTS-STARTPTS)/1.1[v2];"
        "[0:v]trim=start=91.0:end=97.5,setpts=PTS-STARTPTS[v3];"
        "[v0][v1][v2][v3]concat=n=4:v=1:a=0[vout]"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip_entrada),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-r", "60",
        "-pix_fmt", "yuv420p",
        "-an",  # Sin audio por ahora según lo pedido
        str(clip_salida),
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Edición completada con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error al procesar con ffmpeg: {e}")
        sys.exit(1)

    # Verificación técnica con ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "json",
        str(clip_salida),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print("\nFicha técnica del tramo editado:")
    print(res.stdout)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Monta el tramo 02 editado:
1. Toma el segmento inicial del prompt (2.0s a 13.0s).
2. Salta los 5 minutos y medio de espera.
3. Toma el segmento final con la respuesta estructurada (363.0s a 381.0s).
4. Corta antes de que aparezca OBS al final.
5. Exporta a 1080p60 limpio en 'output/tramo_02_editado.mp4'.
"""

import subprocess
import sys
from pathlib import Path


def main():
    clip_entrada = Path("clips/02_giving_the_token_to_agy_and_seting_it_up.mp4")
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    clip_salida = out_dir / "tramo_02_editado.mp4"

    if not clip_entrada.exists():
        print(f"[ERROR] No existe el clip: {clip_entrada}")
        sys.exit(1)

    print(f"\nEditando '{clip_entrada.name}' -> '{clip_salida.name}'...")

    # Seg 0: 2.0s a 13.0s (11.0s) - Prompt y clic en enviar
    # Seg 1: 363.0s a 381.0s (18.0s) - Respuesta estructurada con la configuración completa
    filter_complex = (
        "[0:v]trim=start=2.0:end=13.0,setpts=PTS-STARTPTS[v0];"
        "[0:v]trim=start=363.0:end=378.0,setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[vout]"
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
        "-an",
        str(clip_salida),
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Edición del tramo 02 completada con éxito.")
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
    print("\nFicha técnica del tramo 02 editado:")
    print(res.stdout)


if __name__ == "__main__":
    main()

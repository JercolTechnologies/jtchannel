# -*- coding: utf-8 -*-
"""
Aplica el parche mate de seguridad (Regla 12 de GEMINI.md) en los tramos donde aparece Antigravity IDE:
Oculta la lista de proyectos y carpetas privadas mediante un recorte rectangular
con el color de fondo nativo '#161616' (x: 0..330, y: 275..905).

- Tramo 01: Antigravity aparece a partir de t = 64.9s hasta el final.
- Tramo 02: Antigravity durante todo el tramo (0s a 25.0s).
- Tramo 03: Antigravity durante todo el tramo (0s a 26.0s).
- Tramo 04: Antigravity aparece a partir de t = 20.0s hasta el final.
"""

import os
import subprocess
import sys
from pathlib import Path

OUTPUT_DIR = Path("output")

TRAMOS_CONFIG = [
    {
        "input": OUTPUT_DIR / "tramo_01_completo.mp4",
        "filter": "drawbox=enable='gte(t, 64.9)':x=0:y=275:w=330:h=630:color=0x161616:t=fill",
        "desc": "Tramo 01 (Antigravity desde 64.9s hasta el final)",
    },
    {
        "input": OUTPUT_DIR / "tramo_02_completo.mp4",
        "filter": "drawbox=x=0:y=275:w=330:h=630:color=0x161616:t=fill",
        "desc": "Tramo 02 (Antigravity en todo el tramo)",
    },
    {
        "input": OUTPUT_DIR / "tramo_03_completo.mp4",
        "filter": "drawbox=x=0:y=275:w=330:h=630:color=0x161616:t=fill",
        "desc": "Tramo 03 (Antigravity en todo el tramo)",
    },
    {
        "input": OUTPUT_DIR / "tramo_04_completo.mp4",
        "filter": "drawbox=enable='gte(t, 20.0)':x=0:y=275:w=330:h=630:color=0x161616:t=fill",
        "desc": "Tramo 04 (Antigravity desde 20.0s hasta el final)",
    },
]


def sanitizar_tramo(cfg: dict):
    in_file = cfg["input"]
    if not in_file.exists():
        print(f"[ERROR] No existe {in_file}")
        sys.exit(1)

    temp_file = in_file.with_name(in_file.stem + "_sanitized.mp4")
    print(f"\n--- Sanitizando {in_file.name} ---")
    print(f"  Detalle: {cfg['desc']}")
    print(f"  Filtro: {cfg['filter']}")

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(in_file),
        "-vf", cfg["filter"],
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(temp_file),
    ]
    subprocess.run(cmd, check=True)

    # Reemplazo atómico del archivo original
    os.replace(str(temp_file), str(in_file))
    print(f"  [OK] {in_file.name} sanitizado y protegido con éxito.")


def main():
    print("=" * 65)
    print(" SANITIZACIÓN DE SEGURIDAD DE PROYECTOS PRIVADOS (REGLA 12)")
    print("=" * 65)

    for cfg in TRAMOS_CONFIG:
        sanitizar_tramo(cfg)

    print("\n" + "=" * 65)
    print(" [ÉXITO] Todos los tramos han sido sanitizados correctamente.")
    print("=" * 65)


if __name__ == "__main__":
    main()

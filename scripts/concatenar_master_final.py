# -*- coding: utf-8 -*-
"""
Concatenación final del tutorial completo (Tramos 01 a 04):
Une los 4 tramos ya aprobados y normalizados en el master final:
'output/tutorial_supabase_mcp_completo.mp4'.
"""

import json
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("output")
TRAMOS = [
    OUTPUT_DIR / "tramo_01_completo.mp4",
    OUTPUT_DIR / "tramo_02_completo.mp4",
    OUTPUT_DIR / "tramo_03_completo.mp4",
    OUTPUT_DIR / "tramo_04_completo.mp4",
]
MASTER_FINAL = OUTPUT_DIR / "tutorial_supabase_mcp_completo.mp4"


def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def main():
    print("\n" + "=" * 60)
    print(" CONCATENACIÓN DEL MÁSTER FINAL COMPLETO")
    print("=" * 60)

    for t in TRAMOS:
        if not t.exists():
            print(f"[ERROR] Falta el tramo: {t}")
            return
        dur = medir_duracion(t)
        print(f"  - {t.name}: {dur:.2f} s")

    concat_txt = OUTPUT_DIR / "lista_tramos.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for t in TRAMOS:
            f.write(f"file '{t.resolve().as_posix()}'\n")

    print(f"\n--- Generando {MASTER_FINAL.name} ---")
    cmd_concat = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(MASTER_FINAL),
    ]
    subprocess.run(cmd_concat, check=True)
    concat_txt.unlink(missing_ok=True)

    dur_master = medir_duracion(MASTER_FINAL)
    mins = int(dur_master // 60)
    segs = dur_master % 60
    print(f"\n[ÉXITO] Máster final generado: {MASTER_FINAL.name}")
    print(f"Duración total del tutorial: {dur_master:.2f} s ({mins} min {segs:.1f} seg)")

    # Verificación técnica ffprobe
    print("\n" + "=" * 60)
    print(" VERIFICACIÓN TÉCNICA (ffprobe)")
    print("=" * 60)
    cmd_info = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,duration,sample_rate,channels",
        "-of", "json",
        str(MASTER_FINAL),
    ]
    res = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
    print(res.stdout)

    # Medir LUFS final
    cmd_lufs = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(MASTER_FINAL),
        "-vn",
        "-af", "loudnorm=I=-14:LRA=7:TP=-1.5:print_format=json",
        "-f", "null", "-",
    ]
    r_lufs = subprocess.run(cmd_lufs, capture_output=True, text=True)
    out_l = r_lufs.stderr or ""
    i1, i2 = out_l.rfind("{"), out_l.rfind("}")
    if i1 != -1 and i2 != -1:
        d_lufs = json.loads(out_l[i1:i2 + 1])
        print(f"Sonoridad global del máster: {d_lufs.get('input_i')} LUFS (Target: -14.0 LUFS)")


if __name__ == "__main__":
    main()

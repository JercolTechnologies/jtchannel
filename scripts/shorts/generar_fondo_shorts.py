# -*- coding: utf-8 -*-
"""
Generador del Fondo Animado Base para YouTube Shorts (1080x1920 @ 60fps).
Crea un bucle perfecto (seamless loop) de 6.0 segundos con rejilla técnica en movimiento
y luz volumétrica perimetral (#3ECF8E esmeralda y #00F5FF cian) sobre fondo #090D14.

Se ejecuta una sola vez y guarda el resultado en:
assets/shorts/shorts_bg_loop.mp4
"""

import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT_PATH = Path("assets/shorts/shorts_bg_loop.mp4")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 6.0
TOTAL_FRAMES = int(FPS * DURATION)
CELL = 60          # Tamaño de celda en píxeles (en 6s desplaza 60px en X y 120px en Y -> loop exacto)
MAJOR = 240        # Cada 4 celdas hay línea principal y nodo luminoso


def construir_capas_estaticas():
    """Construye la capa base de iluminación volumétrica y la viñeta."""
    base = Image.new("RGBA", (W, H), (9, 13, 20, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    # Luz volumétrica superior (esmeralda/cian detrás del Hook Banner)
    gdraw.ellipse((140, -120, 940, 520), fill=(0, 245, 255, 42))
    # Luz volumétrica central-derecha (esmeralda detrás del visor y subtítulos)
    gdraw.ellipse((420, 680, 1240, 1580), fill=(62, 207, 142, 48))
    # Luz volumétrica inferior-izquierda
    gdraw.ellipse((-180, 1100, 560, 1850), fill=(0, 195, 255, 36))

    glow = glow.filter(ImageFilter.GaussianBlur(95))
    base = Image.alpha_composite(base, glow)
    return np.asarray(base.convert("RGB"), dtype=np.uint8)


def generar_video_fondo():
    print(f"Generando fondo animado 9:16 ({W}x{H} @ {FPS}fps, {DURATION}s loop)...")
    base_rgb = construir_capas_estaticas()

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        str(OUT_PATH),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Pre-calcular coordenadas Y y X
    yy = np.arange(H, dtype=np.int32)[:, None]
    xx = np.arange(W, dtype=np.int32)[None, :]

    for f in range(TOTAL_FRAMES):
        t = f / FPS
        # Desplazamiento exacto: 10 px/s en X (60px en 6s), 20 px/s en Y (120px en 6s)
        dx = int(round(t * 10.0))
        dy = int(round(t * 20.0))

        frame = base_rgb.copy()

        gx = (xx + dx) % CELL
        gy = (yy + dy) % CELL
        mx = (xx + dx) % MAJOR
        my = (yy + dy) % MAJOR

        # Líneas secundarias de la rejilla (1px)
        mask_minor = (gx == 0) | (gy == 0)
        frame[mask_minor] = np.clip(frame[mask_minor].astype(np.int16) + np.array([14, 24, 36], dtype=np.int16), 0, 255).astype(np.uint8)

        # Líneas principales cada 240px
        mask_major = (mx <= 1) | (my <= 1)
        frame[mask_major] = np.clip(frame[mask_major].astype(np.int16) + np.array([18, 42, 38], dtype=np.int16), 0, 255).astype(np.uint8)

        # Nodos brillantes en las intersecciones de la rejilla principal (3x3 px)
        mask_nodes = (mx <= 2) & (my <= 2)
        # Pulso suave sinusoidal en el brillo de los nodos (2 ciclos en 6s -> seamless)
        pulso = int(45 + 25 * np.sin(2.0 * np.pi * (t / 3.0)))
        frame[mask_nodes] = np.clip(frame[mask_nodes].astype(np.int16) + np.array([10, pulso, int(pulso * 0.8)], dtype=np.int16), 0, 255).astype(np.uint8)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("Error al codificar shorts_bg_loop.mp4")

    size_kb = OUT_PATH.stat().st_size / 1024.0
    print(f"Fondo animado listo: {OUT_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    generar_video_fondo()

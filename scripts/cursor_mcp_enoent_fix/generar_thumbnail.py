# -*- coding: utf-8 -*-
"""
Generador de Miniatura Artesanal (Zero AI Slop) — Video 03:
Fix Cursor MCP Server Errors: The ENOENT Fix (cursor_mcp_enoent_fix)

Especificación de PUBLICACION.md §1 y PRODUCCION_VIDEO_03.md:
- 1280x720 exacto (16:9), < 2048 KB.
- Texto (3 palabras): FIX CURSOR MCP (blanco puro #FFFFFF + verde esmeralda #3ECF8E).
- Composición artesanal con capturas reales del IDE Cursor (error rojo vs fix en verde + mcp.json real)
  y el icono oficial de Cursor extraído de la instalación local.
- Iluminación perimetral sutil para no fundirse con el modo oscuro de YouTube (#0f0f0f).
"""

import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

BASE_DIR = Path(".")
CLIPS_DIR = BASE_DIR / "clips" / "cursor_mcp_enoent_fix"
ASSETS_DIR = BASE_DIR / "assets" / "videos" / "cursor_mcp_enoent_fix"
BRAIN_DIR = Path(r"C:\Users\mapog\.gemini\antigravity\brain\35231b7d-c3a4-42d6-b1df-647ca759de4d")

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
THUMB_OUT = ASSETS_DIR / "thumbnail.jpg"
PREVIEW_120 = BRAIN_DIR / "v03_thumb_120px.png"
PREVIEW_FULL = BRAIN_DIR / "v03_thumb_1280x720.jpg"


def extraer_frame(video_path: Path, timestamp: float, out_png: Path):
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{timestamp:.2f}",
        "-i", str(video_path),
        "-frames:v", "1",
        str(out_png),
    ]
    subprocess.run(cmd, check=True)


def crear_miniatura():
    clips = sorted(CLIPS_DIR.glob("*.mp4"))
    clip_02 = clips[1]
    clip_03 = clips[2]

    frame_err = BRAIN_DIR / "scratch_v03_err.png"
    frame_fix = BRAIN_DIR / "scratch_v03_fix.png"
    frame_green = BRAIN_DIR / "scratch_v03_green.png"

    # Extraer frames reales a 1920x1080
    extraer_frame(clip_03, 3.2, frame_err)     # Modal abierto con MCP Server Error: -32000 Connection closed y botón Reload
    extraer_frame(clip_02, 50.0, frame_fix)    # mcp.json limpio con C:\\Tools\\uv\\uvx.exe y terminal where.exe
    extraer_frame(clip_03, 9.0, frame_green)   # Modal Configure sqlite con punto verde y las 6 tools en verde

    W, H = 1280, 720
    canvas = Image.new("RGBA", (W, H), (14, 17, 23, 255))

    # 1. Fondo general: vista real de Cursor (mcp.json + terminal + panel MCP)
    img_fix = Image.open(frame_fix).convert("RGBA")
    bg_crop = img_fix.crop((240, 40, 1680, 850)).resize((W, H), Image.Resampling.LANCZOS)
    bg_crop = ImageEnhance.Contrast(bg_crop).enhance(1.15)
    bg_crop = ImageEnhance.Brightness(bg_crop).enhance(0.65)
    canvas.paste(bg_crop, (0, 0))

    # Oscurecer suavemente para que las tarjetas en primer plano y la tipografía tengan contraste extremo
    grad = Image.new("RGBA", (W, H), (10, 13, 19, 175))
    canvas = Image.alpha_composite(canvas, grad)

    # 2. Luz volumétrica perimetral (rojo alerta arriba-izquierda, verde esmeralda #3ECF8E derecha y abajo)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gldraw = ImageDraw.Draw(glow)
    gldraw.ellipse((-80, 20, 520, 340), fill=(255, 65, 65, 60))
    gldraw.ellipse((640, 140, 1360, 780), fill=(62, 207, 142, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas = Image.alpha_composite(canvas, glow)

    font_path_bold = r"C:\Windows\Fonts\segoeuib.ttf"
    font_path_mono = r"C:\Windows\Fonts\consolab.ttf"
    f_badge = ImageFont.truetype(font_path_mono, 23)

    # 3. Tarjeta superior izquierda: El Error Rojo real de Cursor (clip_03 @ 3.2s)
    img_err = Image.open(frame_err).convert("RGBA")
    # En 1920x1080 @ 3.2s:
    # - Bloque 1: "Needs Attention 1 / sqlite / Error - Show Output" con punto rojo (x=415..705, y=240..360)
    # - Bloque 2: "Local / Error - MCP error -32000: Connection closed" (x=725..1205, y=555..635)
    err_top = img_err.crop((415, 240, 705, 360)).resize((310, 128), Image.Resampling.LANCZOS)
    err_bot = img_err.crop((725, 555, 1205, 635)).resize((540, 90), Image.Resampling.LANCZOS)

    card_err_box = Image.new("RGBA", (556, 244), (0, 0, 0, 0))
    cdraw1 = ImageDraw.Draw(card_err_box)
    cdraw1.rounded_rectangle((0, 0, 555, 243), radius=14, fill=(22, 22, 24, 255), outline=(255, 75, 75, 255), width=3)
    card_err_box.paste(ImageEnhance.Contrast(err_top).enhance(1.25), (12, 10))
    card_err_box.paste(ImageEnhance.Contrast(err_bot).enhance(1.25), (8, 144))

    # Píldora roja en la esquina superior derecha de la tarjeta de error
    cdraw1.rounded_rectangle((318, 22, 540, 66), radius=8, fill=(220, 38, 38, 255))
    cdraw1.ellipse((330, 36, 346, 52), fill=(255, 255, 255, 255))
    cdraw1.text((356, 30), "spawn ENOENT", font=f_badge, fill=(255, 255, 255, 255))

    canvas.alpha_composite(card_err_box, (34, 34))

    # 4. Tarjeta inferior izquierda: El estado Connected en VERDE + 6 tools activas (clip_03 @ 9.0s)
    img_grn = Image.open(frame_green).convert("RGBA")
    # - Bloque 1: "Connected 1 / sqlite / 6 tools, 1 resource enabled" con punto verde (x=415..705, y=240..360)
    # - Bloque 2: Lista de Tools con toggles verdes (x=725..1205, y=575..785)
    grn_top = img_grn.crop((415, 240, 705, 360)).resize((310, 128), Image.Resampling.LANCZOS)
    grn_bot = img_grn.crop((725, 575, 1205, 785)).resize((540, 236), Image.Resampling.LANCZOS)

    card_grn_box = Image.new("RGBA", (556, 396), (0, 0, 0, 0))
    cdraw2 = ImageDraw.Draw(card_grn_box)
    cdraw2.rounded_rectangle((0, 0, 555, 395), radius=14, fill=(22, 22, 24, 255), outline=(62, 207, 142, 255), width=3)
    card_grn_box.paste(ImageEnhance.Contrast(grn_top).enhance(1.25), (12, 10))
    card_grn_box.paste(ImageEnhance.Contrast(grn_bot).enhance(1.25), (8, 146))

    # Píldora verde brillante en la esquina superior derecha de la tarjeta verde (sin tapar las tools)
    cdraw2.rounded_rectangle((318, 22, 540, 66), radius=8, fill=(16, 185, 129, 255))
    cdraw2.ellipse((330, 36, 346, 52), fill=(10, 25, 18, 255))
    cdraw2.text((356, 30), "6 TOOLS READY", font=f_badge, fill=(10, 25, 18, 255))

    canvas.alpha_composite(card_grn_box, (34, 294))

    # 5. Tipografía Gigante a la derecha: "FIX CURSOR" (Blanco) / "MCP" (Esmeralda #3ECF8E)
    draw = ImageDraw.Draw(canvas)
    f_title_1 = ImageFont.truetype(font_path_bold, 92)
    f_title_2 = ImageFont.truetype(font_path_bold, 128)

    for dx, dy in [(-3, 4), (3, 4), (0, 6)]:
        draw.text((624 + dx, 32 + dy), "FIX CURSOR", font=f_title_1, fill=(0, 0, 0, 220))
        draw.text((624 + dx, 134 + dy), "MCP", font=f_title_2, fill=(0, 0, 0, 220))

    draw.text((624, 32), "FIX CURSOR", font=f_title_1, fill=(255, 255, 255, 255))
    draw.text((624, 134), "MCP", font=f_title_2, fill=(62, 207, 142, 255))

    # 6. Icono Oficial de Cursor (al lado derecho de "MCP", sin solapar "FIX CURSOR")
    ico_path = Path(r"C:\Users\mapog\AppData\Local\Programs\cursor\resources\app\resources\win32\code.ico")
    if ico_path.exists():
        ico_img = Image.open(ico_path).convert("RGBA").resize((124, 124), Image.Resampling.LANCZOS)
        ico_bg = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
        ibdraw = ImageDraw.Draw(ico_bg)
        ibdraw.rounded_rectangle((0, 0, 139, 139), radius=28, fill=(24, 30, 40, 245), outline=(62, 207, 142, 230), width=3)
        ico_bg.alpha_composite(ico_img, (8, 8))
        canvas.alpha_composite(ico_bg, (1088, 152))

    # 7. Ventana de código limpia en la parte inferior derecha mostrando el fix real (.cursor/mcp.json)
    code_w, code_h = 604, 368
    code_card = Image.new("RGBA", (code_w, code_h), (0, 0, 0, 0))
    cdraw3 = ImageDraw.Draw(code_card)
    cdraw3.rounded_rectangle((0, 0, code_w - 1, code_h - 1), radius=16, fill=(18, 21, 28, 250), outline=(62, 207, 142, 230), width=3)
    # Barra superior estilo editor
    cdraw3.rounded_rectangle((3, 3, code_w - 4, 46), radius=13, fill=(28, 33, 43, 255))
    cdraw3.ellipse((20, 16, 34, 30), fill=(255, 95, 86, 255))
    cdraw3.ellipse((44, 16, 58, 30), fill=(255, 189, 46, 255))
    cdraw3.ellipse((68, 16, 82, 30), fill=(39, 201, 63, 255))

    f_tab = ImageFont.truetype(font_path_mono, 20)
    cdraw3.text((105, 13), ".cursor/mcp.json", font=f_tab, fill=(190, 205, 225, 255))

    f_code = ImageFont.truetype(font_path_mono, 24)
    f_code_bold = ImageFont.truetype(font_path_mono, 25)

    # Bloque comparativo directo: línea rota tachada en rojo vs ruta absoluta en verde brillante
    cdraw3.text((24, 64), '{ "mcpServers": {', font=f_code, fill=(170, 180, 195, 255))
    cdraw3.text((48, 102), '"sqlite": {', font=f_code, fill=(125, 207, 255, 255))

    # Fondo rojo sutil para la línea que falla
    cdraw3.rounded_rectangle((42, 142, code_w - 22, 186), radius=6, fill=(95, 24, 32, 190))
    cdraw3.text((54, 150), '- "command": "uvx",', font=f_code, fill=(255, 130, 130, 255))

    # Fondo verde esmeralda sutil para la línea que lo arregla
    cdraw3.rounded_rectangle((42, 196, code_w - 22, 244), radius=6, fill=(18, 82, 56, 220), outline=(62, 207, 142, 180), width=1)
    cdraw3.text((54, 206), '+ "command": "C:\\\\Tools\\\\uv\\\\uvx.exe",', font=f_code_bold, fill=(110, 255, 175, 255))

    cdraw3.text((54, 258), '  "args": ["mcp-server-sqlite"]', font=f_code, fill=(210, 220, 235, 255))
    cdraw3.text((48, 294), '}', font=f_code, fill=(125, 207, 255, 255))
    cdraw3.text((24, 326), '}}', font=f_code, fill=(170, 180, 195, 255))

    canvas.alpha_composite(code_card, (634, 326))

    # 8. Borde interior de luz sutil (1px) para separar del fondo #0f0f0f de YouTube Dark Mode
    bdraw = ImageDraw.Draw(canvas)
    bdraw.rectangle((0, 0, W - 1, H - 1), outline=(62, 207, 142, 95), width=2)

    final_rgb = canvas.convert("RGB")
    final_rgb.save(THUMB_OUT, "JPEG", quality=93, optimize=True)
    final_rgb.save(PREVIEW_FULL, "JPEG", quality=93, optimize=True)

    # Generar preview a 120px de ancho (§1 PUBLICACION.md)
    thumb_120 = final_rgb.resize((120, 68), Image.Resampling.LANCZOS)
    thumb_120.save(PREVIEW_120, "PNG")

    size_kb = THUMB_OUT.stat().st_size / 1024.0
    print(f"Miniatura generada: {THUMB_OUT} ({size_kb:.1f} KB, 1280x720)")


if __name__ == "__main__":
    crear_miniatura()

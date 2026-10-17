# -*- coding: utf-8 -*-
"""
Composición de assets gráficos oficiales para YouTube (v2 refinada):
1. Avatar oficial (800x800 px, 1:1 circular ready).
2. Banner oficial (2560x1440 px, zona segura 1546x423 px perfectamente centrada para móvil/desktop/TV).
3. Miniatura Vídeo 01 (1280x720 px, 16:9, < 2MB, texto de alto contraste legible a 120px con icono vectorial).
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BRANDING_DIR = Path("assets/branding")

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_IMPACT = r"C:\Windows\Fonts\impact.ttf"
FONT_CONSOLAS = r"C:\Windows\Fonts\consola.ttf"


def crear_avatar():
    print("--- 1. Creando Avatar Oficial (800x800) ---")
    src = BRANDING_DIR / "avatar_base.jpg"
    img = Image.open(src).convert("RGBA")
    img_800 = img.resize((800, 800), Image.Resampling.LANCZOS)

    out_path = BRANDING_DIR / "youtube_avatar_800x800.png"
    img_800.save(out_path, format="PNG", optimize=True)
    print(f"Avatar guardado en: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


def crear_banner():
    """
    Especificación YouTube:
    - Tamaño total: 2560 x 1440 px
    - Zona Segura (visible en todos los dispositivos: móvil, tablet, desktop, TV):
      Ancho: 1546 px, Alto: 423 px, Centrado
      X: (2560 - 1546) / 2 = 507 px a 2053 px
      Y: (1440 - 423) / 2 = 508 px a 931 px (Centro Y = 720 px)
    """
    print("\n--- 2. Creando Banner Oficial (2560x1440 con Safe Area 1546x423) ---")
    src = BRANDING_DIR / "banner_bg.jpg"
    bg = Image.open(src).convert("RGBA")
    banner = bg.resize((2560, 1440), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(banner)

    # Tipografías
    font_main = ImageFont.truetype(FONT_BOLD, 110)
    font_sub = ImageFont.truetype(FONT_BOLD, 42)
    font_pill = ImageFont.truetype(FONT_CONSOLAS, 26)

    # Medidas
    title_text = "JERCOL TECH"
    bbox_t = draw.textbbox((0, 0), title_text, font=font_main)
    tw, th = bbox_t[2] - bbox_t[0], bbox_t[3] - bbox_t[1]

    tagline = "AGENTIC AI IN MINUTES"
    bbox_sub = draw.textbbox((0, 0), tagline, font=font_sub)
    sw, sh = bbox_sub[2] - bbox_sub[0], bbox_sub[3] - bbox_sub[1]

    chips = "MCP PROTOCOLS  •  AUTONOMOUS AGENTS  •  FAST DEV TUTORIALS"
    bbox_chip = draw.textbbox((0, 0), chips, font=font_pill)
    cw, ch = bbox_chip[2] - bbox_chip[0], bbox_chip[3] - bbox_chip[1]

    # Distribución vertical en el centro exacto del Safe Area (Y=720)
    espacio_1 = 30
    espacio_2 = 35
    altura_total = th + espacio_1 + sh + espacio_2 + ch
    start_y = 720 - (altura_total // 2) - 10

    # 1. Título Canal
    tx = (2560 - tw) // 2
    ty = start_y
    for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (4, 0)]:
        draw.text((tx + ox, ty + oy), title_text, font=font_main, fill=(0, 0, 0, 240))
    draw.text((tx, ty), title_text, font=font_main, fill=(255, 255, 255, 255))

    # 2. Tagline
    sx = (2560 - sw) // 2
    sy = ty + th + espacio_1
    for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3)]:
        draw.text((sx + ox, sy + oy), tagline, font=font_sub, fill=(0, 0, 0, 220))
    draw.text((sx, sy), tagline, font=font_sub, fill=(62, 207, 142, 255))  # Esmeralda Supabase

    # 3. Pills / Chips
    cx = (2560 - cw) // 2
    cy = sy + sh + espacio_2
    pad_x, pad_y = 28, 12
    pill_box = (cx - pad_x, cy - pad_y, cx + cw + pad_x, cy + ch + pad_y)
    draw.rounded_rectangle(pill_box, radius=16, fill=(10, 15, 26, 230), outline=(0, 245, 255, 200), width=2)
    draw.text((cx, cy), chips, font=font_pill, fill=(226, 232, 240, 255))

    out_path = BRANDING_DIR / "youtube_banner_2560x1440.png"
    banner.save(out_path, format="PNG", optimize=True)
    print(f"Banner guardado en: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


def crear_miniatura_video_01():
    """
    Especificación YouTube:
    - 1280 x 720 px, 16:9 exacto, < 2048 KB
    - Palabras clave gigantes legibles a 120px de ancho
    """
    print("\n--- 3. Creando Miniatura Vídeo 01 (1280x720) ---")
    src = BRANDING_DIR / "thumbnail_01_bg.jpg"
    bg = Image.open(src).convert("RGBA")
    thumb = bg.resize((1280, 720), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(thumb)

    # Tipografías
    font_badge = ImageFont.truetype(FONT_BOLD, 26)
    font_title = ImageFont.truetype(FONT_IMPACT, 114)
    font_tag = ImageFont.truetype(FONT_CONSOLAS, 32)

    # 1. Badge superior con icono rayo vectorial
    badge_text = "2-MIN SETUP • OFFICIAL MCP"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox_b[2] - bbox_b[0], bbox_b[3] - bbox_b[1]
    bx, by = 96, 60

    # Dibujar pill background
    pill_box = (50, by - 10, bx + bw + 20, by + bh + 10)
    draw.rounded_rectangle(pill_box, radius=12, fill=(10, 15, 26, 240), outline=(0, 245, 255, 255), width=3)

    # Rayo vectorial amarillo/cian
    bolt_pts = [(70, by + 2), (80, by + 2), (75, by + 12), (84, by + 12), (68, by + 28), (73, by + 16), (67, by + 16)]
    draw.polygon(bolt_pts, fill=(255, 225, 53, 255))
    draw.text((bx, by), badge_text, font=font_badge, fill=(0, 245, 255, 255))

    # 2. Texto Principal Línea 1: "ANTIGRAVITY"
    t1_text = "ANTIGRAVITY"
    t1_x, t1_y = 50, 145
    for ox, oy in [(-5, -5), (5, -5), (-5, 5), (5, 5), (0, 7), (7, 0), (7, 7)]:
        draw.text((t1_x + ox, t1_y + oy), t1_text, font=font_title, fill=(0, 0, 0, 255))
    draw.text((t1_x, t1_y), t1_text, font=font_title, fill=(255, 255, 255, 255))

    # 3. Texto Principal Línea 2: "+ SUPABASE"
    t2_text = "+ SUPABASE"
    t2_x, t2_y = 50, 270
    for ox, oy in [(-5, -5), (5, -5), (-5, 5), (5, 5), (0, 7), (7, 0), (7, 7)]:
        draw.text((t2_x + ox, t2_y + oy), t2_text, font=font_title, fill=(0, 0, 0, 255))
    draw.text((t2_x, t2_y), t2_text, font=font_title, fill=(62, 207, 142, 255))  # Esmeralda

    # 4. Monospace Sub-tag: "> LIVE POSTGRES SCHEMA"
    sub_text = "> LIVE POSTGRES SCHEMA"
    sx, sy = 55, 415
    bbox_s = draw.textbbox((0, 0), sub_text, font=font_tag)
    sw, sh = bbox_s[2] - bbox_s[0], bbox_s[3] - bbox_s[1]
    draw.rounded_rectangle((sx - 14, sy - 6, sx + sw + 14, sy + sh + 6), radius=8, fill=(15, 23, 42, 230), outline=(100, 116, 139, 150), width=1)
    draw.text((sx, sy), sub_text, font=font_tag, fill=(241, 245, 249, 255))

    out_path = BRANDING_DIR / "thumbnail_video_01_1280x720.png"
    thumb.save(out_path, format="PNG", optimize=True)
    size_kb = out_path.stat().st_size / 1024
    print(f"Miniatura guardada en: {out_path} ({size_kb:.1f} KB)")

    # 5. Prueba de reducción a 120px de ancho según PUBLICACION.md
    test_120 = thumb.resize((120, int(120 * 720 / 1280)), Image.Resampling.LANCZOS)
    test_path = BRANDING_DIR / "thumbnail_120px_test.png"
    test_120.save(test_path, format="PNG")
    print(f"Prueba de reducción 120px guardada en: {test_path}")


def main():
    crear_avatar()
    crear_banner()
    crear_miniatura_video_01()
    print("\n[ÉXITO] Assets actualizados.")


if __name__ == "__main__":
    main()

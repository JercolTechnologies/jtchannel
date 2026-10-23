# -*- coding: utf-8 -*-
"""
Motor Minimalista de YouTube Shorts v2 (9:16 — 1080x1920 @ 60fps).
Mejoras aplicadas tras revisión con Miguel:
1. Cero bordes redondeados y cero barra falsa de Mac:
   - El vídeo original flota directamente sobre la rejilla en movimiento con ángulos rectos de 90°
     y una sombra negra difusa profunda (drop-shadow 3D) por detrás.
   - El Hook superior flota libre sobre la rejilla con sombra dura, sin cajas que lo encierren.
2. Movimiento inmediato en los primeros 3 segundos (Flash-Forward de acción + zoom dinámico) para detonar retención.
3. Seamless Loop (Bucle Infinito) real:
   - Guion terminado en conector abierto ("...because that's literally how" -> "You can wire...").
   - Corte al milímetro tras la última palabra (+0.08s) y retorno al plano visual de apertura.
4. Música The_Iron_Grove.mp3 arrancando siempre en 00:00:14.0 a -18.0 dB relativo, masterizado a -14.0 LUFS (-c:v copy).
"""

import json
import os
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import whisper

load_dotenv()

W, H = 1080, 1920
FPS = 60

# Coordenadas exactas del visor flotante a 90 grados (sin barra Mac, 100% interfaz original)
VIEW_X = 40
VIEW_Y = 360
VIEW_W = 1000
VIEW_H = 860

BG_LOOP_PATH = Path("assets/shorts/shorts_bg_loop.mp4")
DEFAULT_MUSIC_PATH = Path("assets/shorts/music/The_Iron_Grove.mp3")
DEFAULT_MUSIC_START_S = 14.0
DEBAJO_DB = 18.0
TARGET_LUFS = -14.0
TARGET_TP = -1.5
TARGET_LRA = 7.0

INSTRUCCIONES_TONO_SHORT = (
    "Speak in a fast-paced, punchy, confident, and energetic developer tone. "
    "Hook the listener immediately in the first two seconds, keep crisp articulation with minimal pauses, "
    "and leave the final word 'how' slightly suspended as if continuing the sentence."
)

KEYWORDS_EMERALD = {
    "ai", "agent", "agents", "supabase", "mcp", "postgres", "postgresql", "pgvector",
    "schema", "tables", "seconds", "live", "vector", "vectors", "sql",
    "python", "cursor", "green", "connected", "tools", "autonomous", "database",
    "openai", "cosine", "semantic",
}
KEYWORDS_YELLOW = {
    "boom", "never", "stop", "error", "enoent", "bloat", "langchain",
    "foreign", "keys", "instant", "zero", "fix", "two", "minutes", "no",
    "twenty", "eight-line",
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


def medir_lufs(ruta: Path) -> float:
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
        return -14.0
    data = json.loads(m[-1])
    return float(data["input_i"])


def asegurar_audio_tts(audio_path: Path, texto: str, regenerar: bool = False) -> Path:
    """Genera el audio TTS con gpt-4o-mini-tts (nova) si no existe o si se pide regenerar."""
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if audio_path.exists() and not regenerar:
        print(f"Reutilizando audio TTS existente: {audio_path.name}")
        return audio_path

    print(f"Generando audio TTS para Short ({len(texto)} caracteres)...", end=" ", flush=True)
    client = OpenAI()
    resp = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="nova",
        input=texto,
        instructions=INSTRUCCIONES_TONO_SHORT,
        response_format="mp3",
    )
    resp.write_to_file(audio_path)
    dur = medir_duracion(audio_path)
    print(f"OK ({dur:.2f}s)")
    return audio_path


def generar_overlays_flotantes(
    out_dir: Path,
    hook_top: str,
    hook_bottom: str,
    cta_text: str = "FULL 2-MIN SETUP BELOW",
) -> tuple[Path, Path]:
    """
    Genera dos capas PNG 1080x1920 sin bordes redondeados ni barras falsas:
    1. ui_shadow_and_hook.png:
       - Se pinta DEBAJO del vídeo recortado.
       - Lleva la sombra 3D difusa (drop-shadow) para que el vídeo a 90° flote sobre la rejilla,
         y el texto del Hook superior flotando libre con sombra profunda.
    2. ui_cta_sharp.png:
       - Bloque a 90 grados en la parte inferior izquierda (últimos 3.5s) apuntando al Related Video.
    """
    font_bold = r"C:\Windows\Fonts\segoeuib.ttf"

    # --- 1. SOMBRA 3D DEL VISOR + HOOK FLOTANTE ---
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Sombra negra profunda detrás del visor (x=40..1040, y=360..1220)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    # Rectángulo a 90 grados expandido y desplazado ligeramente hacia abajo (+14px) para efecto de elevación
    sdraw.rectangle(
        (VIEW_X - 12, VIEW_Y - 6, VIEW_X + VIEW_W + 12, VIEW_Y + VIEW_H + 22),
        fill=(0, 0, 0, 235),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    layer = Image.alpha_composite(layer, shadow)

    # Texto del Hook flotando libre (sin caja), centrado y con sombra dura
    draw = ImageDraw.Draw(layer)
    f_top = ImageFont.truetype(font_bold, 68)
    f_bot = ImageFont.truetype(font_bold, 74)

    bbox1 = draw.textbbox((0, 0), hook_top, font=f_top)
    x1 = (W - (bbox1[2] - bbox1[0])) // 2

    bbox2 = draw.textbbox((0, 0), hook_bottom, font=f_bot)
    x2 = (W - (bbox2[2] - bbox2[0])) // 2

    # Sombra negra multicapa para que las letras floten sobre la rejilla
    for dx, dy in [(-4, 5), (4, 5), (0, 7), (-2, -2), (2, -2)]:
        draw.text((x1 + dx, 118 + dy), hook_top, font=f_top, fill=(0, 0, 0, 230))
        draw.text((x2 + dx, 206 + dy), hook_bottom, font=f_bot, fill=(0, 0, 0, 230))

    draw.text((x1, 118), hook_top, font=f_top, fill=(255, 255, 255, 255))
    draw.text((x2, 206), hook_bottom, font=f_bot, fill=(62, 207, 142, 255))

    ui_hook_path = out_dir / "ui_shadow_and_hook.png"
    layer.save(ui_hook_path, "PNG")

    # --- 2. CTA A 90 GRADOS (ÚLTIMOS 3.5s) ---
    cta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Sombra del CTA
    cta_sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    csdraw = ImageDraw.Draw(cta_sh)
    csdraw.rectangle((48, 1495, 650, 1580), fill=(0, 0, 0, 220))
    cta_sh = cta_sh.filter(ImageFilter.GaussianBlur(16))
    cta = Image.alpha_composite(cta, cta_sh)

    cdraw = ImageDraw.Draw(cta)
    # Bloque rectangular a 90 grados exactos con barra lateral verde esmeralda
    cdraw.rectangle((48, 1490, 642, 1570), fill=(14, 22, 30, 248))
    cdraw.rectangle((48, 1490, 62, 1570), fill=(62, 207, 142, 255))

    f_cta = ImageFont.truetype(font_bold, 36)
    cdraw.text((82, 1506), f"{cta_text}  ▼", font=f_cta, fill=(62, 207, 142, 255))

    ui_cta_path = out_dir / "ui_cta_sharp.png"
    cta.save(ui_cta_path, "PNG")

    return ui_hook_path, ui_cta_path


def _norm_token(p: str) -> str:
    s = p.lower()
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"[^a-z0-9]", "", s)


def _ass_time(segundos: float) -> str:
    segundos = max(0.0, float(segundos))
    total_cs = int(round(segundos * 100))
    h = total_cs // 360000
    total_cs %= 360000
    m = total_cs // 6000
    total_cs %= 6000
    s = total_cs // 100
    cs = total_cs % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _colorear_palabra_ass(palabra: str) -> str:
    limpia = _norm_token(palabra)
    if limpia in KEYWORDS_EMERALD:
        return f"{{\\c&H008ECF3E&}}{palabra}{{\\c&H00FFFFFF&}}"
    if limpia in KEYWORDS_YELLOW:
        return f"{{\\c&H0066D1FF&}}{palabra}{{\\c&H00FFFFFF&}}"
    return palabra


def generar_subtitulos_ass(audio_path: Path, guion_texto: str, duracion_mp3: float, out_ass: Path) -> tuple[Path, float]:
    """
    Transcribe con Whisper, alinea con el guion oficial y genera subtítulos .ASS en Piso 3 (y=1375).
    Devuelve la ruta del .ASS y el segundo exacto donde termina la última palabra hablada.
    """
    print("Sincronizando subtítulos quemados (.ASS) con Whisper...")
    model = whisper.load_model("base")
    res = model.transcribe(str(audio_path), word_timestamps=True, language="en")

    whisper_words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            whisper_words.append({
                "word": w["word"].strip(),
                "start": float(w["start"]),
                "end": float(w["end"]),
            })

    script_words = guion_texto.strip().split()
    norm_s = [_norm_token(w) for w in script_words]
    norm_w = [_norm_token(w["word"]) for w in whisper_words]

    matches = SequenceMatcher(None, norm_s, norm_w, autojunk=False).get_matching_blocks()
    s2w = {}
    for b in matches:
        for k in range(b.size):
            s2w[b.a + k] = b.b + k

    alineadas = []
    for idx, sw in enumerate(script_words):
        w_idx = s2w.get(idx)
        if w_idx is not None and w_idx < len(whisper_words):
            alineadas.append({
                "word": sw,
                "start": whisper_words[w_idx]["start"],
                "end": whisper_words[w_idx]["end"],
            })
        else:
            prev_end = alineadas[-1]["end"] if alineadas else 0.0
            alineadas.append({
                "word": sw,
                "start": prev_end,
                "end": min(duracion_mp3, prev_end + 0.22),
            })

    # Agrupar en bloques dinámicos de 2 a 3 palabras
    cues = []
    grupo = []
    ini_g = 0.0

    for item in alineadas:
        if not grupo:
            ini_g = item["start"]
        grupo.append(item["word"])

        cierra = item["word"].endswith((".", "!", "?", ",", ":", "—"))
        if cierra or len(grupo) >= 3:
            fin_g = max(ini_g + 0.24, item["end"])
            cues.append((ini_g, fin_g, grupo))
            grupo = []

    if grupo:
        cues.append((ini_g, alineadas[-1]["end"], grupo))

    last_speech_end = alineadas[-1]["end"] if alineadas else duracion_mp3

    cues_limpios = []
    for idx, (ini, fin, palabras) in enumerate(cues):
        if idx + 1 < len(cues):
            next_ini = cues[idx + 1][0]
            if fin > next_ini:
                fin = max(ini + 0.18, next_ini - 0.01)
            elif (next_ini - fin) < 0.85:
                fin = next_ini - 0.01
        else:
            fin = last_speech_end + 0.06
        cues_limpios.append((ini, fin, palabras))

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 1
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortSub,Segoe UI,76,&H00FFFFFF,&H000000FF,&H00080C12,&H96000000,-1,0,0,0,100,100,1,0,1,6,4,5,60,60,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    REEMPLAZOS_SUBS_VISUALES = {
        "WHERE-DOT-EXE": "WHERE.EXE",
        "MCP-DOT-JSON": "MCP.JSON",
        "DOT-CMD": ".CMD",
        "DOT-EXE": ".EXE",
    }

    lineas_eventos = []
    for ini, fin, palabras in cues_limpios:
        palabras_vis = [REEMPLAZOS_SUBS_VISUALES.get(p.upper().rstrip(".,!?:;"), p.upper()) + (p[-1] if p[-1] in ".,!?:;" and p.upper().rstrip(".,!?:;") in REEMPLAZOS_SUBS_VISUALES else "") for p in palabras]
        palabras_col = [_colorear_palabra_ass(p) for p in palabras_vis]
        texto_cue = " ".join(palabras_col)
        efecto_pop = r"{\pos(540,1375)\fscx110\fscy110\t(0,85,\fscx100\fscy100)}"
        lineas_eventos.append(
            f"Dialogue: 0,{_ass_time(ini)},{_ass_time(fin)},ShortSub,,0,0,0,,{efecto_pop}{texto_cue}"
        )

    out_ass.write_text(ass_header + "\n".join(lineas_eventos) + "\n", encoding="utf-8")
    return out_ass, last_speech_end


def construir_short(spec: dict) -> Path:
    slug = spec["slug"]
    out_dir = Path("output/shorts") / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_voz = Path(spec["audio_voz"])
    if spec.get("generar_tts", False):
        asegurar_audio_tts(audio_voz, spec["guion"], regenerar=spec.get("regenerar_tts", False))

    dur_mp3 = medir_duracion(audio_voz)

    # 1. Subtítulos .ASS y detección del fin exacto de la última palabra para el Seamless Loop
    ass_path = out_dir / "subs_short.ass"
    _, fin_voz_real = generar_subtitulos_ass(audio_voz, spec["guion"], dur_mp3, ass_path)

    # Para que el loop verbal sea continuo ("...literally how" -> "You can wire..."),
    # cortamos a solo +0.08s tras la última palabra hablada
    margen_cierre = float(spec.get("margen_cierre_s", 0.08))
    dur_total = round(min(dur_mp3, fin_voz_real + margen_cierre), 2)

    print("=" * 65)
    print(f"ENSAMBLANDO SHORT v2: {slug} ({dur_total:.2f}s | 1080x1920 @ 60fps)")
    print("=" * 65)

    # 2. Overlays flotantes (Sombra 3D bajo el vídeo a 90° + Hook libre arriba + CTA a 90° abajo)
    ui_hook_png, ui_cta_png = generar_overlays_flotantes(
        out_dir,
        spec["hook_top"],
        spec["hook_bottom"],
        spec.get("cta_text", "FULL 2-MIN SETUP BELOW"),
    )

    # 3. Ajustar proporcionalmente la duración de los planos visuales para que sumen exactamente dur_total
    shots = spec["shots"]
    suma_targets = sum(float(s["target_dur"]) for s in shots)
    escala_tiempo = dur_total / suma_targets

    segmentos_render = []
    for i, shot in enumerate(shots):
        seg_out = out_dir / f"shot_{i:02d}.mp4"
        clip_in = Path(shot["clip"])
        start = float(shot["start"])
        end = float(shot["end"])
        dur_raw = end - start
        dur_target = float(shot["target_dur"]) * escala_tiempo
        pts_factor = dur_target / dur_raw

        cx, cy, cw, ch = shot["crop"]
        vf_shot = (
            f"trim=start={start}:end={end},setpts=(PTS-STARTPTS)*{pts_factor:.6f},"
            f"crop=w={cw}:h={ch}:x={cx}:y={cy},"
            f"scale={VIEW_W}:{VIEW_H}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={VIEW_W}:{VIEW_H}:(ow-iw)/2:(oh-ih)/2:color=#141414"
        )
        cmd_shot = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(clip_in),
            "-vf", vf_shot,
            "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            "-r", str(FPS), "-pix_fmt", "yuv420p", "-an",
            str(seg_out),
        ]
        subprocess.run(cmd_shot, check=True)
        segmentos_render.append(seg_out)

    concat_list = out_dir / "shots_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in segmentos_render:
            f.write(f"file '{s.resolve().as_posix()}'\n")

    visor_mp4 = out_dir / "visor_central.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(visor_mp4),
    ], check=True)

    # 4. Composición vertical:
    #    Orden de capas:
    #    [0:v] Fondo rejilla animada
    #    [2:v] Sombra 3D + Hook flotante (va DEBAJO del vídeo para que la sombra rodee al vídeo sin pisarlo)
    #    [1:v] Vídeo original recortado a 90 grados (VIEW_X=40, VIEW_Y=360, 1000x860) flotando encima
    #    [3:v] CTA a 90 grados en los últimos 3.5s
    #    Subtítulos .ASS quemados encima
    video_sin_master = out_dir / f"{slug}_temp_video.mp4"
    cta_start = max(0.0, dur_total - 3.5)
    ass_escaped = ass_path.resolve().as_posix().replace(":", r"\:")

    filter_comp = (
        f"[0:v]trim=0:{dur_total},setpts=PTS-STARTPTS[bg];"
        f"[bg][2:v]overlay=x=0:y=0[bg_hook];"
        f"[1:v]tpad=stop_mode=clone:stop_duration=2.0,trim=0:{dur_total},setpts=PTS-STARTPTS[vis];"
        f"[bg_hook][vis]overlay=x={VIEW_X}:y={VIEW_Y}[v2];"
        f"[v2][3:v]overlay=x=0:y=0:enable='gte(t,{cta_start:.2f})'[v3];"
        f"[v3]ass='{ass_escaped}'[vout]"
    )

    print("Renderizando composición vertical 9:16 con vídeo flotante a 90°...")
    cmd_comp = [
        "ffmpeg", "-y", "-v", "error",
        "-stream_loop", "-1", "-i", str(BG_LOOP_PATH),
        "-i", str(visor_mp4),
        "-i", str(ui_hook_png),
        "-i", str(ui_cta_png),
        "-filter_complex", filter_comp,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-t", f"{dur_total:.3f}",
        str(video_sin_master),
    ]
    subprocess.run(cmd_comp, check=True)

    # 5. Mezclar Voz + Música (The_Iron_Grove.mp3 desde 00:00:14.0 a -18 dB relativo) y normalizar a -14 LUFS
    musica_path = Path(spec.get("musica_path", DEFAULT_MUSIC_PATH))
    music_start = float(spec.get("music_start_s", DEFAULT_MUSIC_START_S))

    lufs_voz = medir_lufs(audio_voz)
    lufs_mus = medir_lufs(musica_path)
    objetivo_mus = lufs_voz - DEBAJO_DB
    ganancia_mus = 10.0 ** ((objetivo_mus - lufs_mus) / 20.0)

    fade_out_st = max(0.0, dur_total - 1.2)
    music_end = music_start + dur_total

    mix_filter = (
        f"[1:a]aformat=channel_layouts=stereo,atrim=0:{dur_total:.3f},asetpts=PTS-STARTPTS[vox];"
        f"[2:a]atrim=start={music_start:.3f}:end={music_end:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:ss=0:d=0.6,"
        f"afade=t=out:st={fade_out_st:.3f}:d=1.2,"
        f"volume={ganancia_mus:.6f},"
        f"aformat=channel_layouts=stereo[mus];"
        f"[vox][mus]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[mix]"
    )

    cmd_p1 = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(video_sin_master),
        "-i", str(audio_voz),
        "-i", str(musica_path),
        "-filter_complex", f"{mix_filter};[mix]loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}:print_format=json",
        "-f", "null", "-",
    ]
    res_p1 = subprocess.run(cmd_p1, capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", res_p1.stderr, re.S)

    if m:
        data = json.loads(m[-1])
        loudnorm_params = (
            f"loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}:"
            f"measured_I={data['input_i']}:measured_LRA={data['input_lra']}:"
            f"measured_TP={data['input_tp']}:measured_thresh={data['input_thresh']}:"
            f"offset={data['target_offset']}:linear=true"
        )
    else:
        loudnorm_params = f"loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}"

    video_master = out_dir / f"{slug}_master.mp4"
    cmd_p2 = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_sin_master),
        "-i", str(audio_voz),
        "-i", str(musica_path),
        "-filter_complex", f"{mix_filter};[mix]{loudnorm_params}[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest",
        str(video_master),
    ]
    subprocess.run(cmd_p2, check=True)

    for s in segmentos_render:
        s.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)
    visor_mp4.unlink(missing_ok=True)
    video_sin_master.unlink(missing_ok=True)

    lufs_final = medir_lufs(video_master)
    dur_final = medir_duracion(video_master)
    print(f"Short Master v2 exportado: {video_master} ({dur_final:.2f}s | {lufs_final:.2f} LUFS)")
    return video_master


if __name__ == "__main__":
    # SHORT 01A (Vídeo 01 — Antigravity + Supabase MCP) con TTS dedicado y Seamless Loop
    spec_short_01a = {
        "slug": "short_01_antigravity_mcp",
        "hook_top": "CONNECT AI AGENTS TO",
        "hook_bottom": "YOUR DB IN 2 MINS",
        "cta_text": "FULL 2-MIN SETUP BELOW",
        "audio_voz": "output/shorts/short_01_antigravity_mcp/voz_short_01a.mp3",
        "generar_tts": True,
        "regenerar_tts": False,
        "margen_cierre_s": 0.08,
        "guion": (
            "You can wire an autonomous AI agent straight to your Supabase database in two minutes. "
            "No manual SQL migrations. You just drop an MCP access token into Antigravity, "
            "ask for a relational schema with users, projects, and tasks, "
            "and boom: in seconds it builds the tables, foreign keys, and live rows directly in Postgres. "
            "Check the full two-minute setup right here at the bottom, because that's literally how"
        ),
        "shots": [
            {
                # 1. HOOK VISUAL DE ACCIÓN (0.0s a 3.8s):
                # Arranca en el frame exacto 11.0s donde termina el Plano 5 para un loop de 0 píxeles de salto
                "clip": "output/antigravity_supabase/tramo_04_completo.mp4",
                "start": 11.0,
                "end": 16.0,
                "target_dur": 3.8,
                "crop": (360, 140, 1080, 860),
            },
            {
                # 2. TOKEN MCP EN SUPABASE (3.8s a 7.8s):
                # Encuadre exacto sobre el panel lateral derecho 'Generate token' sin cortar bordes
                "clip": "output/antigravity_supabase/tramo_01_completo.mp4",
                "start": 34.0,
                "end": 41.5,
                "target_dur": 4.0,
                "crop": (840, 130, 1000, 860),
            },
            {
                # 3. DISPARO DEL PROMPT EN ANTIGRAVITY (7.8s a 12.2s):
                # Muestra el prompt y el clic real en el botón azul de enviar
                "clip": "output/antigravity_supabase/tramo_03_completo.mp4",
                "start": 7.5,
                "end": 11.6,
                "target_dur": 4.4,
                "crop": (360, 340, 1040, 620),
            },
            {
                # 4. BOOM! TABLAS Y DATOS CREADOS EN SEGUNDOS (12.2s a 20.6s):
                # Scroll fluido mostrando el Schema Structure + las tablas Projects y Tasks pobladas
                "clip": "output/antigravity_supabase/tramo_04_completo.mp4",
                "start": 20.5,
                "end": 28.5,
                "target_dur": 8.4,
                "crop": (360, 110, 1040, 830),
            },
            {
                # 5. PUENTE VISUAL DE BUCLE INFINITO (20.6s a 24.82s):
                # Va de 7.8s a 11.0s en el Schema Visualizer, empalmando al frame exacto (11.0s) con el inicio del Plano 1
                "clip": "output/antigravity_supabase/tramo_04_completo.mp4",
                "start": 7.8,
                "end": 11.0,
                "target_dur": 4.22,
                "crop": (360, 140, 1080, 860),
            },
        ],
    }

    # SHORT 02 (Vídeo 02 — Stop Using LangChain: Raw Supabase Vector Search)
    spec_short_02 = {
        "slug": "short_02_stop_using_langchain",
        "hook_top": "STOP USING LANGCHAIN",
        "hook_bottom": "FOR VECTOR SEARCH",
        "cta_text": "FULL 8-LINE CODE BELOW",
        "audio_voz": "output/shorts/short_02_stop_using_langchain/voz_short_02.mp3",
        "generar_tts": True,
        "regenerar_tts": False,
        "margen_cierre_s": 0.08,
        "guion": (
            "Stop installing twenty LangChain packages just to run a basic vector search. "
            "You already have Postgres. Just enable pgvector in Supabase, "
            "generate your query embedding with OpenAI in two lines of Python, "
            "and query your table directly using the native cosine distance operator. "
            "You get sub-second semantic matches with zero framework bloat. "
            "Check the full eight-line script right below, because it's time to"
        ),
        "shots": [
            {
                # 1. HOOK VISUAL EN ACCIÓN (0.0s a 3.8s):
                # Arranca en 4.0s seleccionando las 20 líneas de imports pesados de LangChain y borrándolas de un plumazo
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 4.0,
                "end": 12.0,
                "target_dur": 3.8,
                "crop": (40, 40, 1000, 860),
            },
            {
                # 2. SQL EDITOR + PGVECTOR (3.8s a 8.4s):
                # Activando vector extension y creando la tabla documents con vector(1536) en Supabase
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 20.0,
                "end": 28.5,
                "target_dur": 4.6,
                "crop": (360, 155, 1000, 860),
            },
            {
                # 3. TABLE EDITOR CON EMBEDDINGS REALES (8.4s a 12.6s):
                # Mostrando Tesla Model 3 y iPhone 15 Pro con sus vectores de 1536 dimensiones
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 35.5,
                "end": 41.5,
                "target_dur": 4.2,
                "crop": (40, 155, 1000, 860),
            },
            {
                # 4A. PYTHON EN 8 LÍNEAS + OPERADOR NATIVO <=> (12.6s a 16.6s):
                # Código limpio search.py con OpenAI embedding y operador <=>
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 51.0,
                "end": 59.5,
                "target_dur": 4.0,
                "crop": (500, 40, 1050, 900),
            },
            {
                # 4B. EJECUCIÓN Y RESULTADO EN TERMINAL (16.6s a 20.8s):
                # python search.py -> Top Match: Tesla Model 3
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 60.5,
                "end": 68.0,
                "target_dur": 4.2,
                "crop": (30, 0, 1250, 1075),
            },
            {
                # 5. PUENTE VISUAL DE BUCLE INFINITO (20.8s a fin):
                # Va de 0.2s a 4.0s empezando a seleccionar el bloque de LangChain, empalmando al frame 4.0s con el Plano 1
                "clip": "output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4",
                "start": 0.2,
                "end": 4.0,
                "target_dur": 3.8,
                "crop": (40, 40, 1000, 860),
            },
        ],
    }

    # SHORT 03 (Vídeo 03 — Fix Cursor MCP Server Error: spawn ENOENT Fix)
    spec_short_03 = {
        "slug": "short_03_cursor_enoent_fix",
        "hook_top": "FIX CURSOR MCP ERROR",
        "hook_bottom": "SPAWN ENOENT IN 10S",
        "cta_text": "FULL WINDOWS & MAC FIX",
        "audio_voz": "output/shorts/short_03_cursor_enoent_fix/voz_short_03.mp3",
        "generar_tts": True,
        "regenerar_tts": False,
        "margen_cierre_s": 0.08,
        "guion": (
            "Your Cursor MCP server is throwing a red spawn ENOENT error even though the command works fine in your terminal. "
            "That happens because Cursor doesn't inherit your shell PATH or Windows dot-cmd wrappers. "
            "Just run where-dot-exe in PowerShell to grab the full executable path, "
            "paste it into mcp-dot-json with double backslashes, "
            "and hit Reload for an instant green light. "
            "Check the full fix right below, if you noticed"
        ),
        "shots": [
            {
                # 1. HOOK VISUAL EN ACCIÓN (0.00s a 11.50s):
                # Error rojo en Cursor (Needs Attention 1 / Error - Show Output) + uvx --version funcionando en terminal
                "clip": "output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4",
                "start": 2.5,
                "end": 11.0,
                "target_dur": 11.50,
                "crop": (380, 40, 1000, 860),
            },
            {
                # 2. WHERE.EXE UVX Y NPX EN POWERSHELL (11.50s a 16.85s):
                # Sincronizado con "Just run where.exe in PowerShell to grab the full executable path"
                "clip": "output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4",
                "start": 14.5,
                "end": 25.0,
                "target_dur": 5.35,
                "crop": (380, 40, 1000, 860),
            },
            {
                # 3. RUTA ABSOLUTA CON DOBLE BARRA EN MCP.JSON (16.85s a 19.75s):
                # Sincronizado con "paste it into mcp.json with double backslashes" ("command": "C:\\Tools\\uv\\uvx.exe")
                "clip": "output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4",
                "start": 35.5,
                "end": 38.8,
                "target_dur": 2.90,
                "crop": (880, 40, 1000, 860),
            },
            {
                # 4. RELOAD Y LUZ VERDE CON 6 TOOLS ACTIVAS (19.75s a 22.80s):
                # Sincronizado con "and hit Reload for an instant green light"
                "clip": "output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4",
                "start": 39.0,
                "end": 48.0,
                "target_dur": 3.05,
                "crop": (380, 40, 1000, 860),
            },
            {
                # 5. PUENTE VISUAL DE BUCLE INFINITO (22.80s a 25.16s):
                # Va de 0.0s a 2.5s mostrando el error rojo inicial, empalmando al fotograma exacto (2.5s) con el Plano 1
                "clip": "output/cursor_mcp_enoent_fix/tutorial_cursor_mcp_enoent_fix_master.mp4",
                "start": 0.0,
                "end": 2.5,
                "target_dur": 2.36,
                "crop": (380, 40, 1000, 860),
            },
        ],
    }
    construir_short(spec_short_03)

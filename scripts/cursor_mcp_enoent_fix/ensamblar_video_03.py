# -*- coding: utf-8 -*-
"""
Ensamblado Master Completo — Video 03:
Fix Cursor MCP Server Errors: The ENOENT Fix (cursor_mcp_enoent_fix)

1. Monta los 3 tramos con sincronización quirúrgica y Regla 11 bis (cola de 1.10s tras última palabra):
   - Tramo 01: 14.13s (voz termina en 13.03s -> cola 1.10s)
   - Tramo 02: 24.20s (voz termina en 23.10s -> cola 1.10s, con jump-cut limpio de 24.5s a 47.0s)
   - Tramo 03: 14.52s (voz termina en 13.42s -> cola 1.10s, Reload en verde exacto en "boom" 2.80s)
2. Concatena los 3 tramos en 1080p60 constante.
3. Mezcla la música de fondo (musica.mp3) a -18.0 dB relativo a la voz con fade-in (1.5s) y fade-out (2.5s) (ADR-004).
4. Masteriza el audio a -14.0 LUFS EBU R128 en doble pasada con -c:v copy.
5. Genera subtítulos .SRT sincronizados con Whisper y alineados con el guion oficial.
"""

import json
import re
import shutil
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import whisper

BASE_DIR = Path(".")
CLIPS_DIR = BASE_DIR / "clips" / "cursor_mcp_enoent_fix"
OUT_DIR = BASE_DIR / "output" / "cursor_mcp_enoent_fix"
AUDIOS_DIR = OUT_DIR / "audios"
ASSETS_DIR = BASE_DIR / "assets" / "videos" / "cursor_mcp_enoent_fix"

OUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Asegurar que musica.mp3 esté en assets/videos/cursor_mcp_enoent_fix/musica.mp3
MUSICA_ORIGEN = BASE_DIR / "assets" / "videos" / "raw_supabase_vector_search" / "musica.mp3"
MUSICA_PISTA = ASSETS_DIR / "musica.mp3"
if not MUSICA_PISTA.exists() and MUSICA_ORIGEN.exists():
    shutil.copy2(MUSICA_ORIGEN, MUSICA_PISTA)

_clips_disponibles = sorted(CLIPS_DIR.glob("*.mp4"))
CLIP_01 = _clips_disponibles[0]
CLIP_02 = _clips_disponibles[1]
CLIP_03 = _clips_disponibles[2]

TRAMO_01_FINAL = OUT_DIR / "tramo_01_completo.mp4"
TRAMO_02_FINAL = OUT_DIR / "tramo_02_completo.mp4"
TRAMO_03_FINAL = OUT_DIR / "tramo_03_completo.mp4"

VIDEO_CONCAT = OUT_DIR / "tutorial_cursor_mcp_enoent_fix_sin_musica.mp4"
VIDEO_MASTER = OUT_DIR / "tutorial_cursor_mcp_enoent_fix_master.mp4"
OUTPUT_SRT = ASSETS_DIR / "subtitulos_video_03.srt"

DEBAJO_DB = 18.0
FADE_IN_S = 1.5
FADE_OUT_S = 2.5
TARGET_LUFS = -14.0
TARGET_TP = -1.5
TARGET_LRA = 7.0

GUION_OFICIAL = [
    # Tramo 01
    "You just added an MCP server to Cursor, and it immediately fails with a red "
    "'spawn ENOENT' error. Yet when you run the exact same command in your terminal, "
    "it works fine. Why does Cursor think it doesn't exist?",
    # Tramo 02
    "Cursor is a desktop GUI app—it often fails to inherit your terminal's PATH, "
    "or tries to spawn Windows dot-cmd wrappers like npx without an extension. "
    "The fix takes ten seconds. In PowerShell, run 'where.exe uvx' or 'where.exe npx'—"
    "don't forget the dot-exe—then paste the full executable path into mcp.json "
    "with double backslashes.",
    # Tramo 03
    "Save your config, hit Reload, and boom: your MCP server lights up green "
    "with all six tools loaded and ready for your agent. If this saved your build, "
    "drop a like and subscribe for more zero-fluff dev fixes.",
]


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


def renderizar_tramo(nombre: str, clip_in: Path, audio_in: Path, filter_complex: str, dur_total: float, video_final: Path):
    print(f"\n--- Montando {nombre} (objetivo: {dur_total:.2f}s) ---")
    video_edit = OUT_DIR / f"{video_final.stem}_edit_temp.mp4"
    video_mux = OUT_DIR / f"{video_final.stem}_mux_temp.mp4"

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(clip_in),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-r", "60", "-pix_fmt", "yuv420p", "-an",
        str(video_edit),
    ]
    subprocess.run(cmd_v, check=True)

    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_edit),
        "-i", str(audio_in),
        "-filter_complex", f"[1:a]apad=whole_dur={dur_total}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", str(video_mux),
    ]
    subprocess.run(cmd_mux, check=True)

    normalizar_loudnorm(video_mux, video_final)
    video_edit.unlink(missing_ok=True)
    video_mux.unlink(missing_ok=True)
    print(f"{nombre} listo: {video_final.name} ({medir_duracion(video_final):.2f}s)")


def montar_todos_los_tramos():
    # TRAMO 01: 14.13s total (voz termina en 13.03s -> cola 1.10s)
    # 2.0s a 9.0s (7.0s raw -> 6.40s): señala error rojo en sqlite y "command": "uvx" en mcp.json
    # 9.0s a 16.6s (7.6s raw -> 3.40s): escribe uvx --version en terminal y pulsa Enter
    # 16.6s a 18.8s (2.2s raw + 2.13s tpad = 4.33s): muestra uvx 0.13.5 en terminal
    fc_tramo_01 = (
        "[0:v]trim=start=2.0:end=9.0,setpts=(PTS-STARTPTS)*0.914285[v0];"
        "[0:v]trim=start=9.0:end=16.6,setpts=(PTS-STARTPTS)*0.447368[v1];"
        "[0:v]trim=start=16.6:end=18.8,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2.13[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[vout]"
    )
    renderizar_tramo(
        "Tramo 01 (El Error y la Terminal)",
        CLIP_01,
        AUDIOS_DIR / "tramo_01.mp3",
        fc_tramo_01,
        14.13,
        TRAMO_01_FINAL,
    )

    # TRAMO 02: 24.20s total (voz termina en 23.10s -> cola 1.10s)
    # 1.0s a 18.0s (17.0s raw -> 16.80s): ejecuta where.exe uvx y where.exe npx en terminal
    # 18.0s a 24.5s (6.5s raw -> 2.20s): sube el ratón a mcp.json y selecciona "uvx"
    # [CORTE QUIRÚRGICO 24.5s a 47.0s ELIMINADO]
    # 47.0s a 54.5s (7.5s raw -> 5.20s): jump-cut limpio al path "C:\\Tools\\uv\\uvx.exe" y guardado Ctrl+S
    fc_tramo_02 = (
        "[0:v]trim=start=1.0:end=18.0,setpts=(PTS-STARTPTS)*0.988235[v0];"
        "[0:v]trim=start=18.0:end=24.5,setpts=(PTS-STARTPTS)*0.338461[v1];"
        "[0:v]trim=start=47.0:end=54.5,setpts=(PTS-STARTPTS)*0.693333[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[vout]"
    )
    renderizar_tramo(
        "Tramo 02 (where.exe y el Fix en mcp.json)",
        CLIP_02,
        AUDIOS_DIR / "tramo_02.mp3",
        fc_tramo_02,
        24.20,
        TRAMO_02_FINAL,
    )

    # TRAMO 03: 14.52s total (voz termina en 13.42s -> cola 1.10s)
    # 1.0s a 6.5s (5.5s raw -> 2.80s): abre sqlite, pulsa Reload y en 2.80s ("boom") se ilumina en verde
    # 6.5s a 20.8s (14.3s raw -> 11.72s): recorre las 6 tools activas en verde y muestra Connected 1
    fc_tramo_03 = (
        "[0:v]trim=start=1.0:end=6.5,setpts=(PTS-STARTPTS)*0.509091[v0];"
        "[0:v]trim=start=6.5:end=20.8,setpts=(PTS-STARTPTS)*0.819580[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[vout]"
    )
    renderizar_tramo(
        "Tramo 03 (Reconexión en Verde y 6 Tools)",
        CLIP_03,
        AUDIOS_DIR / "tramo_03.mp3",
        fc_tramo_03,
        14.52,
        TRAMO_03_FINAL,
    )


def concatenar_tramos() -> float:
    print("\n" + "=" * 60)
    print("PASO 2: CONCATENANDO LOS 3 TRAMOS")
    print("=" * 60)

    tramos = [TRAMO_01_FINAL, TRAMO_02_FINAL, TRAMO_03_FINAL]
    list_file = OUT_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for t in tramos:
            if not t.exists():
                print(f"[ERROR] No existe el tramo: {t}")
                sys.exit(1)
            f.write(f"file '{t.resolve().as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(VIDEO_CONCAT),
    ]
    subprocess.run(cmd, check=True)
    list_file.unlink(missing_ok=True)
    dur = medir_duracion(VIDEO_CONCAT)
    print(f"Vídeo concatenado: {VIDEO_CONCAT.name} ({dur:.2f} s | {dur/60:.2f} min)")
    return dur


def mezclar_musica_y_masterizar(duracion_video: float):
    print("\n" + "=" * 60)
    print("PASO 3: MEZCLA DE MÚSICA (-18 dB) Y MASTERIZACIÓN (-14 LUFS)")
    print("=" * 60)

    lufs_voz = medir_lufs(VIDEO_CONCAT)
    lufs_mus = medir_lufs(MUSICA_PISTA)
    print(f"  Voz master:   {lufs_voz:.2f} LUFS")
    print(f"  Música cruda: {lufs_mus:.2f} LUFS")

    objetivo_mus = lufs_voz - DEBAJO_DB
    ganancia_mus = 10.0 ** ((objetivo_mus - lufs_mus) / 20.0)
    print(f"  Objetivo música (-{DEBAJO_DB} dB relativo): {objetivo_mus:.2f} LUFS (factor: {ganancia_mus:.5f})")

    st_fadeout = max(0.0, duracion_video - FADE_OUT_S)

    mix_filter = (
        f"[0:a]aformat=channel_layouts=stereo[vox];"
        f"[1:a]atrim=0:{duracion_video:.3f},"
        f"afade=t=in:ss=0:d={FADE_IN_S},"
        f"afade=t=out:st={st_fadeout:.3f}:d={FADE_OUT_S},"
        f"volume={ganancia_mus:.6f},"
        f"aformat=channel_layouts=stereo[mus];"
        f"[vox][mus]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[mix]"
    )

    cmd_p1 = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(VIDEO_CONCAT),
        "-i", str(MUSICA_PISTA),
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
        print(f"  Medición completada (input_i: {data['input_i']} LUFS, offset: {data['target_offset']} dB)")
    else:
        loudnorm_params = f"loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}"

    cmd_p2 = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(VIDEO_CONCAT),
        "-i", str(MUSICA_PISTA),
        "-filter_complex", f"{mix_filter};[mix]{loudnorm_params}[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        str(VIDEO_MASTER),
    ]
    subprocess.run(cmd_p2, check=True)
    print(f"Master final exportado: {VIDEO_MASTER.name}")


def normalizar_palabra(p: str) -> str:
    s = p.lower()
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def formatear_tiempo_srt(segundos: float) -> str:
    miliseg = int(round(segundos * 1000))
    horas = miliseg // 3600000
    miliseg %= 3600000
    minutos = miliseg // 60000
    miliseg %= 60000
    segs = miliseg // 1000
    miliseg %= 1000
    return f"{horas:02d}:{minutos:02d}:{segs:02d},{miliseg:03d}"


def generar_subtitulos():
    print("\n" + "=" * 60)
    print("PASO 4: GENERANDO SUBTÍTULOS (.SRT) CON WHISPER + ALINEACIÓN")
    print("=" * 60)

    model = whisper.load_model("base")
    res = model.transcribe(str(VIDEO_MASTER), word_timestamps=True, language="en")

    whisper_words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            whisper_words.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
            })

    script_words = []
    for chunk in GUION_OFICIAL:
        tokens = chunk.strip().split()
        script_words.extend(tokens)

    norm_script = [normalizar_palabra(w) for w in script_words]
    norm_whisper = [normalizar_palabra(w["word"]) for w in whisper_words]

    matcher = SequenceMatcher(None, norm_script, norm_whisper)
    matches = matcher.get_matching_blocks()

    alineadas = []
    for s_idx, sw in enumerate(script_words):
        w_match = None
        for block in matches:
            if block.a <= s_idx < block.a + block.size:
                offset = s_idx - block.a
                matched_w = block.b + offset
                if matched_w < len(whisper_words):
                    w_match = whisper_words[matched_w]
                break

        if w_match:
            alineadas.append({
                "word": sw,
                "start": w_match["start"],
                "end": w_match["end"],
            })
        else:
            prev_t = alineadas[-1]["end"] if alineadas else 0.0
            alineadas.append({
                "word": sw,
                "start": prev_t,
                "end": prev_t + 0.30,
            })

    cues = []
    bloque_actual = []
    inicio_bloque = 0.0

    for item in alineadas:
        if not bloque_actual:
            inicio_bloque = item["start"]
        bloque_actual.append(item["word"])

        es_fin_frase = item["word"].endswith((".", "!", "?", ":"))
        longitud_ok = len(bloque_actual) >= 6

        if es_fin_frase or longitud_ok or len(bloque_actual) >= 8:
            fin_bloque = item["end"]
            cues.append({
                "start": inicio_bloque,
                "end": fin_bloque,
                "text": " ".join(bloque_actual),
            })
            bloque_actual = []

    if bloque_actual:
        cues.append({
            "start": inicio_bloque,
            "end": alineadas[-1]["end"],
            "text": " ".join(bloque_actual),
        })

    with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
        for i, cue in enumerate(cues, 1):
            f.write(f"{i}\n")
            f.write(f"{formatear_tiempo_srt(cue['start'])} --> {formatear_tiempo_srt(cue['end'])}\n")
            f.write(f"{cue['text']}\n\n")

    print(f"Subtítulos .SRT generados: {OUTPUT_SRT}")


def verificar_master():
    print("\n" + "=" * 60)
    print("PASO 5: VERIFICACIÓN TÉCNICA DEL MASTER (ffprobe)")
    print("=" * 60)
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size",
        "-show_streams",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json",
        str(VIDEO_MASTER),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(res.stdout)

    lufs_final = medir_lufs(VIDEO_MASTER)
    print(f"Sonoridad final master: {lufs_final:.2f} LUFS (Objetivo: {TARGET_LUFS} LUFS)")


def main():
    montar_todos_los_tramos()
    dur = concatenar_tramos()
    mezclar_musica_y_masterizar(dur)
    generar_subtitulos()
    verificar_master()


if __name__ == "__main__":
    main()

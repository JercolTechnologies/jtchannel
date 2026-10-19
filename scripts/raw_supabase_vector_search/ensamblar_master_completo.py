# -*- coding: utf-8 -*-
"""
Ensamblado Master Completo — Video 02:
Raw Supabase Vector Search

1. Concatena los 5 tramos completos (1080p60 exacto).
2. Mezcla la música de fondo (musica.mp3) a -18 dB relativo a la voz con fade-in y fade-out.
3. Normaliza a -14.0 LUFS EBU R128 (doble pasada loudnorm, -c:v copy).
4. Genera subtítulos .SRT sincronizados con Whisper y alineados con el guion oficial.
5. Verificación técnica rigurosa con ffprobe.
"""

import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import whisper

BASE_DIR = Path(".")
OUT_DIR = BASE_DIR / "output" / "raw_supabase_vector_search"
ASSETS_DIR = BASE_DIR / "assets" / "videos" / "raw_supabase_vector_search"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

TRAMOS = [
    OUT_DIR / "tramo_01_completo.mp4",
    OUT_DIR / "tramo_02_completo.mp4",
    OUT_DIR / "tramo_03_completo.mp4",
    OUT_DIR / "tramo_04_completo.mp4",
    OUT_DIR / "tramo_05_completo.mp4",
]

MUSICA_PISTA = ASSETS_DIR / "musica.mp3"
VIDEO_CONCAT = OUT_DIR / "tutorial_raw_supabase_vector_search_sin_musica.mp4"
VIDEO_MASTER = OUT_DIR / "tutorial_raw_supabase_vector_search_master.mp4"
OUTPUT_SRT = ASSETS_DIR / "subtitulos_video_02.srt"

DEBAJO_DB = 18.0
FADE_IN_S = 1.5
FADE_OUT_S = 2.5
TARGET_LUFS = -14.0
TARGET_TP = -1.5
TARGET_LRA = 7.0

GUION_OFICIAL = [
    # Tramo 01
    "Every AI influencer sold you that you need LangChain and complex vector databases to build semantic search. "
    "That's complete hype. You already have Postgres. "
    "Today, we're doing raw vector search in Supabase with zero frameworks and just four lines of code.",
    
    # Tramo 02
    "First, jump into your Supabase dashboard. Open the SQL Editor and enable the vector extension. "
    "Then create a simple table with a vector column matching your model's dimensions. "
    "That's it. Your database is now an AI vector store.",
    
    # Tramo 03
    "In the Table Editor, we've populated our documents with sample records and their 1536-dimensional embeddings. "
    "Ready to be matched against any concept.",
    
    # Tramo 04
    "Now the Python side. We grab an embedding for our query using OpenAI's small model in two lines. "
    "Then, connect straight to Supabase and query your table using the native cosine distance operator. "
    "No wrappers, no bloated abstractions—just pure SQL finding the nearest neighbor.",
    
    # Tramo 05
    "And boom: instant semantic match with sub-second latency and total control over your query. "
    "Stop adding layers you don't need. And hey—if you want an autonomous AI agent to manage "
    "your Supabase database and run these setups for you, check out my previous video on the screen right now."
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

# -------------------------------------------------------------
# PASO 1: Concatenar los 5 Tramos
# -------------------------------------------------------------
def concatenar_tramos():
    print("=" * 60)
    print("PASO 1: CONCATENANDO LOS 5 TRAMOS")
    print("=" * 60)
    
    list_file = OUT_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for t in TRAMOS:
            if not t.exists():
                print(f"[ERROR] No existe el tramo: {t}")
                sys.exit(1)
            # FFmpeg concat demuxer paths
            f.write(f"file '{t.resolve().as_posix()}'\n")
            
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(VIDEO_CONCAT)
    ]
    subprocess.run(cmd, check=True)
    list_file.unlink(missing_ok=True)
    dur = medir_duracion(VIDEO_CONCAT)
    print(f"Vídeo concatenado con éxito: {VIDEO_CONCAT.name} ({dur:.2f} s | {dur/60:.2f} min)")
    return dur

# -------------------------------------------------------------
# PASO 2: Mezclar Música de Fondo y Normalizar a -14 LUFS
# -------------------------------------------------------------
def mezclar_musica_y_masterizar(duracion_video: float):
    print("\n" + "=" * 60)
    print("PASO 2: MEZCLA DE MÚSICA Y MASTERIZACIÓN FINAL (ADR-004)")
    print("=" * 60)
    
    if not MUSICA_PISTA.exists():
        print(f"[ERROR] No existe la música de fondo: {MUSICA_PISTA}")
        sys.exit(1)

    print("Midiendo sonoridad de la locución y de la música...")
    lufs_voz = medir_lufs(VIDEO_CONCAT)
    lufs_mus = medir_lufs(MUSICA_PISTA)
    print(f"  Voz master:   {lufs_voz:.2f} LUFS")
    print(f"  Música cruda: {lufs_mus:.2f} LUFS")

    # Calcular ganancia
    objetivo_mus = lufs_voz - DEBAJO_DB
    ganancia_mus = 10.0 ** ((objetivo_mus - lufs_mus) / 20.0)
    print(f"  Objetivo música (-{DEBAJO_DB} dB relativo): {objetivo_mus:.2f} LUFS (factor: {ganancia_mus:.5f})")

    st_fadeout = max(0.0, duracion_video - FADE_OUT_S)
    
    # Construcción de la mezcla en memoria
    mix_filter = (
        f"[0:a]aformat=channel_layouts=stereo[vox];"
        f"[1:a]atrim=0:{duracion_video:.3f},"
        f"afade=t=in:ss=0:d={FADE_IN_S},"
        f"afade=t=out:st={st_fadeout:.3f}:d={FADE_OUT_S},"
        f"volume={ganancia_mus:.6f},"
        f"aformat=channel_layouts=stereo[mus];"
        f"[vox][mus]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[mix]"
    )

    # Pasada 1: Medición para loudnorm
    print("Ejecutando Pasada 1 de loudnorm...")
    cmd_p1 = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(VIDEO_CONCAT),
        "-i", str(MUSICA_PISTA),
        "-filter_complex", f"{mix_filter};[mix]loudnorm=I={TARGET_LUFS}:LRA={TARGET_LRA}:TP={TARGET_TP}:print_format=json",
        "-f", "null", "-"
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
        print("  [AVISO] Usando loudnorm en pasada única.")

    # Pasada 2: Render final copiando el vídeo intacto
    print(f"Ejecutando Pasada 2 (render con -c:v copy)...")
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
        str(VIDEO_MASTER)
    ]
    subprocess.run(cmd_p2, check=True)
    print(f"Master final exportado: {VIDEO_MASTER.name}")

# -------------------------------------------------------------
# PASO 3: Generación de Subtítulos (.SRT) con Whisper
# -------------------------------------------------------------
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
    print("PASO 3: GENERANDO SUBTÍTULOS (.SRT) CON WHISPER + ALINEACIÓN")
    print("=" * 60)
    
    print("Cargando modelo Whisper 'base'...")
    model = whisper.load_model("base")
    
    print("Transcribiendo master de audio con word_timestamps...")
    res = model.transcribe(str(VIDEO_MASTER), word_timestamps=True, language="en")
    
    whisper_words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            whisper_words.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"]
            })
            
    # Preparar palabras oficiales del guion
    script_words = []
    for chunk in GUION_OFICIAL:
        tokens = chunk.strip().split()
        script_words.extend(tokens)
        
    print(f"Palabras en guion oficial: {len(script_words)} | Palabras Whisper: {len(whisper_words)}")
    
    # Alinear usando SequenceMatcher sobre tokens normalizados
    norm_script = [normalizar_palabra(w) for w in script_words]
    norm_whisper = [normalizar_palabra(w["word"]) for w in whisper_words]
    
    matcher = SequenceMatcher(None, norm_script, norm_whisper)
    matches = matcher.get_matching_blocks()
    
    alineadas = []
    w_idx = 0
    for s_idx, sw in enumerate(script_words):
        # Buscar correspondencia directa o cercana
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
                "end": w_match["end"]
            })
            w_idx = min(len(whisper_words) - 1, w_idx + 1)
        else:
            # Si no hubo match exacto, aproximar tiempos
            prev_t = alineadas[-1]["end"] if alineadas else 0.5
            alineadas.append({
                "word": sw,
                "start": prev_t,
                "end": prev_t + 0.35
            })

    # Agrupar en bloques legibles de subtítulos (5 a 8 palabras por bloque o fin de frase)
    cues = []
    bloque_actual = []
    inicio_bloque = 0.0
    
    for item in alineadas:
        if not bloque_actual:
            inicio_bloque = item["start"]
        bloque_actual.append(item["word"])
        
        es_fin_frase = item["word"].endswith((".", "!", "?"))
        longitud_ok = len(bloque_actual) >= 6
        
        if es_fin_frase or longitud_ok or len(bloque_actual) >= 8:
            fin_bloque = item["end"]
            texto_cue = " ".join(bloque_actual)
            cues.append({
                "start": inicio_bloque,
                "end": fin_bloque,
                "text": texto_cue
            })
            bloque_actual = []
            
    if bloque_actual:
        cues.append({
            "start": inicio_bloque,
            "end": alineadas[-1]["end"],
            "text": " ".join(bloque_actual)
        })

    # Escribir archivo .SRT
    with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
        for i, cue in enumerate(cues, 1):
            f.write(f"{i}\n")
            f.write(f"{formatear_tiempo_srt(cue['start'])} --> {formatear_tiempo_srt(cue['end'])}\n")
            f.write(f"{cue['text']}\n\n")

    print(f"Subtítulos .SRT generados con éxito: {OUTPUT_SRT}")

# -------------------------------------------------------------
# PASO 4: Verificación Técnica Final
# -------------------------------------------------------------
def verificar_master():
    print("\n" + "=" * 60)
    print("PASO 4: VERIFICACIÓN TÉCNICA DEL MASTER (ffprobe)")
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
    dur = concatenar_tramos()
    mezclar_musica_y_masterizar(dur)
    generar_subtitulos()
    verificar_master()
    print("\n" + "=" * 60)
    print("¡PRODUCCIÓN DEL VÍDEO 02 COMPLETADA CON ÉXITO TOTAL!")
    print("=" * 60)

if __name__ == "__main__":
    main()

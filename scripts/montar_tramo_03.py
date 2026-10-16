# -*- coding: utf-8 -*-
"""
Montaje completo del Tramo 03 (Fusión Clip 03 + Clip 04):
1. Genera los 2 bloques de narración con 'gpt-4o-mini-tts' (voz 'nova') con tono amigable y enérgico.
2. Mide la duración exacta de cada bloque de audio.
3. Corta dinámicamente:
   - Parte 1 (Clip 03): Muestra el prompt, el audio explica la petición y termina justo al hacer click en enviar (15.3s).
   - Parte 2 (Clip 04): Jump cut al resultado en Supabase. El corte final termina exactamente a duración_audio + 1.0s de margen.
4. Concatena las dos partes de vídeo en 1080p60.
5. Mezcla las dos pistas de voz en sus cues sincronizados.
6. Muxea y aplica normalización de audio con doble pasada 'loudnorm' (-14 LUFS) con '-c:v copy'.
7. Limpia temporales dejando únicamente 'output/tramo_03_completo.mp4'.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

BLOQUES_GUION = [
    {
        "id": "b1_prompt",
        "cue_offset": 0.4,
        "text": (
            "Now let's put it to work. We ask the agent to create a project management schema "
            "with users, projects, and tasks, plus a few dummy rows so we can verify the data live."
        ),
    },
    {
        "id": "b2_output",
        "cue_offset": 0.3,
        "text": (
            "And boom! In seconds, the agent executes the migration via MCP, "
            "sets up all foreign keys, and seeds our test data directly into Postgres."
        ),
    },
]

INSTRUCCIONES_TONO = (
    "Speak in an enthusiastic, cheerful, friendly, and energetic conversational tone like talking with developer friends. "
    "Natural upbeat pacing with clear pauses, engaging and relatable, no stiff lecture monotone."
)

CLIP_03_RAW = Path("clips/03_asking_agy_for_create_an_schema.mp4")
CLIP_04_RAW = Path("clips/04_showing_agy_output_explainig_what_he_just_did_in_DB.mp4")


def medir_duracion(ruta: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def sintetizar_bloques(client: OpenAI, audio_dir: Path, regenerar: bool = False) -> list[dict]:
    audio_dir.mkdir(parents=True, exist_ok=True)
    bloques_generados = []

    print("\n--- 1. Generando audios TTS con gpt-4o-mini-tts (Voz: Nova) ---")
    for b in BLOQUES_GUION:
        ruta_mp3 = audio_dir / f"{b['id']}.mp3"

        if ruta_mp3.exists() and not regenerar:
            print(f"Reutilizando audio existente '{b['id']}'...", end=" ", flush=True)
        else:
            print(f"Sintetizando '{b['id']}'...", end=" ", flush=True)
            resp = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=b["text"],
                instructions=INSTRUCCIONES_TONO,
                response_format="mp3",
            )
            resp.write_to_file(ruta_mp3)

        dur = medir_duracion(ruta_mp3)
        print(f"OK ({dur:.2f} s)")
        bloques_generados.append({**b, "path": ruta_mp3, "duration": dur})

    return bloques_generados


def cortar_y_concatenar_video(dur_audio1: float, dur_audio2: float, salida_video: Path) -> tuple[float, float]:
    """
    Calcula los puntos de corte dinámicos para eliminar tiempos muertos.
    - Clip 03: Fin anclado en 15.3s (click de envío en 14.8s, 'Working' en 15.2s).
      Duración = dur_audio1 + 0.4s (cue) + 0.5s margen tras la voz.
    - Clip 04: Inicio en 02.0s (pantalla limpia sin OBS).
      Duración = 0.3s (cue) + dur_audio2 + 1.0s (margen de cierre dinámico sin silencios).
    """
    print("\n--- 2. Calculando cortes dinámicos de vídeo según duración de voz ---")

    # Parte 1 (Clip 03)
    p1_end = 15.3
    p1_dur = round(0.4 + dur_audio1 + 0.6, 2)  # voz empieza en 0.4s y termina ~0.6s antes del corte/click
    p1_start = round(p1_end - p1_dur, 2)
    if p1_start < 2.0:
        p1_start = 2.0
        p1_dur = round(p1_end - p1_start, 2)

    print(f"Parte 1 (Clip 03): corte [{p1_start:.2f}s -> {p1_end:.2f}s] (duración: {p1_dur:.2f}s)")
    print(f"  -> Voz 1 ({dur_audio1:.2f}s) empieza en +0.4s y termina en +{0.4 + dur_audio1:.2f}s. Click en +{14.8 - p1_start:.2f}s.")

    # Parte 2 (Clip 04)
    p2_start = 2.0
    # Margen de seguridad: 1.0 segundo después de terminar la voz
    p2_dur = round(0.3 + dur_audio2 + 1.0, 2)
    p2_end = round(p2_start + p2_dur, 2)

    print(f"Parte 2 (Clip 04): corte [{p2_start:.2f}s -> {p2_end:.2f}s] (duración: {p2_dur:.2f}s)")
    print(f"  -> Voz 2 ({dur_audio2:.2f}s) empieza en +0.3s y termina en +{0.3 + dur_audio2:.2f}s. Margen final limpio: 1.0s.")

    temp_dir = salida_video.parent / "temp_tramo_03"
    temp_dir.mkdir(parents=True, exist_ok=True)
    part1_mp4 = temp_dir / "part1.mp4"
    part2_mp4 = temp_dir / "part2.mp4"

    # Cortar Parte 1
    cmd_p1 = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(p1_start),
        "-i", str(CLIP_03_RAW),
        "-t", str(p1_dur),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-r", "60", "-pix_fmt", "yuv420p",
        "-an",
        str(part1_mp4),
    ]
    subprocess.run(cmd_p1, check=True)

    # Cortar Parte 2
    cmd_p2 = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(p2_start),
        "-i", str(CLIP_04_RAW),
        "-t", str(p2_dur),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-r", "60", "-pix_fmt", "yuv420p",
        "-an",
        str(part2_mp4),
    ]
    subprocess.run(cmd_p2, check=True)

    # Concat list
    concat_txt = temp_dir / "concat.txt"
    concat_txt.write_text(
        f"file '{part1_mp4.resolve().as_posix()}'\nfile '{part2_mp4.resolve().as_posix()}'\n",
        encoding="utf-8"
    )

    cmd_concat = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "copy",
        str(salida_video),
    ]
    subprocess.run(cmd_concat, check=True)

    dur_total = medir_duracion(salida_video)
    print(f"Vídeo editado combinado: {salida_video.name} ({dur_total:.2f} s)")

    # Limpiar trozos temporales
    part1_mp4.unlink(missing_ok=True)
    part2_mp4.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    temp_dir.rmdir()

    return p1_dur, p2_dur


def mezclar_pista_audio(bloques: list[dict], dur_parte1: float, dur_total_video: float, salida_audio: Path) -> None:
    print("\n--- 3. Mezclando pistas de voz sincronizadas con los cortes ---")
    cue1 = bloques[0]["cue_offset"]
    cue2 = dur_parte1 + bloques[1]["cue_offset"]

    print(f"Audio 1 inicia en t = {cue1:.2f} s")
    print(f"Audio 2 inicia en t = {cue2:.2f} s (justo tras el salto al resultado)")

    entradas = ["-i", str(bloques[0]["path"]), "-i", str(bloques[1]["path"])]
    delay1_ms = int(cue1 * 1000)
    delay2_ms = int(cue2 * 1000)

    filtro = (
        f"[0:a]adelay={delay1_ms}|{delay1_ms}[a0];"
        f"[1:a]adelay={delay2_ms}|{delay2_ms}[a1];"
        f"[a0][a1]amix=inputs=2:dropout_transition=0:normalize=0,"
        f"apad=whole_dur={dur_total_video}[aout]"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        *entradas,
        "-filter_complex", filtro,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(salida_audio),
    ]
    subprocess.run(cmd, check=True)
    dur_audio_final = medir_duracion(salida_audio)
    print(f"Pista de voz completa mezclada: {salida_audio.name} ({dur_audio_final:.2f} s)")


def normalizar_master_loudnorm(video_crudo: Path, video_final: Path) -> None:
    print("\n--- 4. Normalizando sonoridad del master (-14 LUFS, doble pasada) ---")
    filtro_base = "loudnorm=I=-14:LRA=7:TP=-1.5"

    cmd_medir = [
        "ffmpeg", "-hide_banner", "-nostats", "-y",
        "-i", str(video_crudo),
        "-vn",
        "-af", f"{filtro_base}:print_format=json",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd_medir, capture_output=True, text=True)
    salida = r.stderr or ""
    ini, fin = salida.rfind("{"), salida.rfind("}")
    if ini == -1 or fin == -1:
        print("[AVISO] Medición falló, aplicando pasada simple.")
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
        "-i", str(video_crudo),
        "-c:v", "copy",
        "-af", filtro_aplicar,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        str(video_final),
    ]
    subprocess.run(cmd_aplicar, check=True)
    print(f"Master normalizado con éxito: {video_final.name}")


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] Falta OPENAI_API_KEY en .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # 1. Audios
    audio_dir = Path("output/audios_tramo_03")
    bloques = sintetizar_bloques(client, audio_dir)

    dur_a1 = bloques[0]["duration"]
    dur_a2 = bloques[1]["duration"]

    # 2. Cortar y concatenar vídeo
    video_editado = Path("output/tramo_03_editado.mp4")
    dur_p1, dur_p2 = cortar_y_concatenar_video(dur_a1, dur_a2, video_editado)
    dur_total = medir_duracion(video_editado)

    # 3. Mezcla de audio
    pista_audio = Path("output/tramo_03_audio_mix.mp3")
    mezclar_pista_audio(bloques, dur_p1, dur_total, pista_audio)

    # 4. Muxing preliminar
    video_mux = Path("output/tramo_03_mux_temp.mp4")
    print("\n--- Uniendo vídeo con pista de voz ---")
    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_editado),
        "-i", str(pista_audio),
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        str(video_mux),
    ]
    subprocess.run(cmd_mux, check=True)

    # 5. Normalizar master a -14 LUFS
    video_final = Path("output/tramo_03_completo.mp4")
    normalizar_master_loudnorm(video_mux, video_final)

    # 6. Limpieza: borrar temporales para dejar solo el completo
    video_mux.unlink(missing_ok=True)
    video_editado.unlink(missing_ok=True)

    # 7. Verificación final ffprobe
    print("\n" + "=" * 60)
    print(" VERIFICACIÓN TÉCNICA DEL MASTER FINAL (ffprobe)")
    print("=" * 60)
    cmd_info = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,duration,sample_rate,channels",
        "-of", "json",
        str(video_final),
    ]
    res = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
    print(res.stdout)

    # Medir LUFS del vídeo final
    cmd_lufs = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(video_final),
        "-vn",
        "-af", "loudnorm=I=-14:LRA=7:TP=-1.5:print_format=json",
        "-f", "null", "-",
    ]
    r_lufs = subprocess.run(cmd_lufs, capture_output=True, text=True)
    out_l = r_lufs.stderr or ""
    i1, i2 = out_l.rfind("{"), out_l.rfind("}")
    if i1 != -1 and i2 != -1:
        d_lufs = json.loads(out_l[i1:i2 + 1])
        print(f"Sonoridad final alcanzada: {d_lufs.get('input_i')} LUFS (Target: -14.0 LUFS)")

    print(f"\n[ÉXITO] Archivo final listo en: {video_final}\n")


if __name__ == "__main__":
    main()

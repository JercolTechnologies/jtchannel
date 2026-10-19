# -*- coding: utf-8 -*-
"""
Montaje completo del Tramo 02:
1. Genera los 2 bloques de narración con 'gpt-4o-mini-tts' (voz 'nova') con tono enérgico y amigable.
2. Verifica duraciones contra las ventanas visuales.
3. Posiciona cada bloque de audio en su segundo exacto (0.5s y 12.0s).
4. Mezcla con el vídeo editado ('output/tramo_02_editado.mp4').
5. Normaliza el audio final con doble pasada de 'loudnorm' (-14 LUFS) con '-c:v copy'.
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
        "cue_sec": 0.5,
        "max_dur": 10.5,
        "text": "Now paste your token right into the chat and tell your agent to configure the Supabase MCP server. Just hit send, and let Antigravity do the heavy lifting behind the scenes.",
    },
    {
        "id": "b2_resultado",
        "cue_sec": 12.0,
        "max_dur": 16.0,
        "text": "And just like that, it's done! The agent configured the MCP server, authenticated via the CLI, and wired up our project credentials in the local env. Our database connection is officially live!",
    },
]

INSTRUCCIONES_TONO = (
    "Speak in an enthusiastic, cheerful, friendly, and energetic conversational tone like talking with developer friends. "
    "Natural upbeat pacing with clear pauses, engaging and relatable, no stiff lecture monotone."
)


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

    print("\n--- Procesando audios con gpt-4o-mini-tts (Voz: Nova) ---")
    for b in BLOQUES_GUION:
        ruta_mp3 = audio_dir / f"{b['id']}.mp3"

        if ruta_mp3.exists() and not regenerar:
            print(f"Reutilizando audio existente '{b['id']}'...", end=" ", flush=True)
        else:
            print(f"Generando bloque '{b['id']}'...", end=" ", flush=True)
            resp = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=b["text"],
                instructions=INSTRUCCIONES_TONO,
                response_format="mp3",
            )
            resp.write_to_file(ruta_mp3)

        dur = medir_duracion(ruta_mp3)
        print(f"OK ({dur:.2f} s | ventana max: {b['max_dur']} s)")

        if dur > b["max_dur"]:
            print(f"  [ERROR] El audio ({dur:.2f}s) excede la ventana visual ({b['max_dur']}s)!")
            sys.exit(1)

        bloques_generados.append({**b, "path": ruta_mp3, "duration": dur})

    return bloques_generados


def mezclar_pista_audio(bloques: list[dict], duracion_total: float, salida_audio: Path) -> None:
    entradas = []
    filtros = []
    for i, b in enumerate(bloques):
        entradas.extend(["-i", str(b["path"])])
        delay_ms = int(b["cue_sec"] * 1000)
        filtros.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    mezcla = "".join(f"[a{i}]" for i in range(len(bloques)))
    filtro_completo = f"{';'.join(filtros)};{mezcla}amix=inputs={len(bloques)}:dropout_transition=0:normalize=0,apad=whole_dur={duracion_total}[aout]"

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        *entradas,
        "-filter_complex", filtro_completo,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(salida_audio),
    ]
    subprocess.run(cmd, check=True)
    print(f"\nPista de audio completa generada: {salida_audio.name} ({medir_duracion(salida_audio):.2f} s)")


def normalizar_master_loudnorm(video_crudo: Path, video_final: Path) -> None:
    print("\n--- Normalizando sonoridad del master (doble pasada loudnorm) ---")
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

    video_editado = Path("output/tramo_02_editado.mp4")
    if not video_editado.exists():
        print(f"[ERROR] No existe el vídeo editado: {video_editado}")
        sys.exit(1)

    duracion_video = medir_duracion(video_editado)
    print(f"Vídeo editado: {video_editado.name} ({duracion_video:.2f} s)")

    audio_dir = Path("output/audios_tramo_02")
    bloques = sintetizar_bloques(client, audio_dir)

    pista_audio = Path("output/tramo_02_audio_mix.mp3")
    mezclar_pista_audio(bloques, duracion_video, pista_audio)

    # Mux vídeo con audio inicial
    video_mux = Path("output/tramo_02_mux_temp.mp4")
    print("\n--- Uniendo vídeo con pista de voz sincronizada ---")
    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_editado),
        "-i", str(pista_audio),
        "-vf", "drawbox=x=0:y=305:w=320:h=635:color=0x161616:t=fill",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-shortest",
        str(video_mux),
    ]
    subprocess.run(cmd_mux, check=True)

    # Normalizar audio a -14 LUFS
    video_final = Path("output/tramo_02_completo.mp4")
    normalizar_master_loudnorm(video_mux, video_final)

    video_mux.unlink(missing_ok=True)

    # Verificación final ffprobe
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
    print(f"\n[ÉXITO] Archivo final listo en: {video_final}\n")


if __name__ == "__main__":
    main()

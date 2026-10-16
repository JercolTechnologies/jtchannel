# -*- coding: utf-8 -*-
"""
Montaje completo del Tramo 01:
1. Genera 5 bloques de narración con 'gpt-4o-mini-tts' (voz 'nova') con tono enérgico y amigable.
2. Verifica duraciones contra las ventanas visuales.
3. Posiciona cada bloque de audio en su segundo de entrada exacto.
4. Mezcla con el vídeo editado ('output/tramo_01_editado.mp4').
5. Normaliza el audio final con doble pasada de 'loudnorm' (-14 LUFS) sobre el MP4 con '-c:v copy'.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Definición de bloques del guion para el Tramo 1
# Cada bloque tiene su texto y su tiempo de entrada (cue) en segundos
BLOQUES_GUION = [
    {
        "id": "b1_intro",
        "cue_sec": 0.5,
        "max_dur": 14.0,
        "text": "Connecting an autonomous agent to Supabase with MCP gives it superpowers over your database! Let's get started: head to your account settings and open Access Tokens.",
    },
    {
        "id": "b2_crear_token",
        "cue_sec": 15.0,
        "max_dur": 15.0,
        "text": "Click Generate new token and give it a name. Since we're just testing locally, let's keep it safe and set the expiration to 24 hours—always best to keep demo credentials tightly scoped.",
    },
    {
        "id": "b3_permisos",
        "cue_sec": 27.0,
        "max_dur": 12.0,
        "text": "Pick your organization, and select the Full access preset so our agent can inspect schemas, run migrations, and execute SQL without hitting permission walls.",
    },
    {
        "id": "b4_copiar_token",
        "cue_sec": 40.0,
        "max_dur": 13.0,
        "text": "Hit Create token, copy the key to your clipboard, and confirm. Treat this like gold—Supabase will only show you this secret once!",
    },
    {
        "id": "b5_antigravity",
        "cue_sec": 54.0,
        "max_dur": 14.0,
        "text": "Awesome, with our token ready, let's hop right into Antigravity to plug Supabase into our agent's workspace!",
    },
]

INSTRUCCIONES_TONO = (
    "Speak in an enthusiastic, cheerful, friendly, and energetic conversational tone like talking with developer friends. "
    "Natural upbeat pacing with clear pauses, engaging and relatable, no stiff or monotone lecture."
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
    """Construye una pista continua colocando cada bloque en su cue_sec."""
    # Filtro adelay en ffmpeg (milisegundos)
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
    """Aplica loudnorm en doble pasada con -c:v copy sobre el MP4 ya compuesto."""
    print("\n--- Normalizando sonoridad del master (doble pasada loudnorm) ---")
    filtro_base = "loudnorm=I=-14:LRA=7:TP=-1.5"

    # Pasada 1: Medición a null
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

    # Pasada 2: Aplicar filtro al audio copiando el vídeo intacto
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

    video_editado = Path("output/tramo_01_editado.mp4")
    if not video_editado.exists():
        print(f"[ERROR] No existe el vídeo editado: {video_editado}")
        sys.exit(1)

    duracion_video = medir_duracion(video_editado)
    print(f"Vídeo editado: {video_editado.name} ({duracion_video:.2f} s)")

    audio_dir = Path("output/audios_tramo_01")
    bloques = sintetizar_bloques(client, audio_dir)

    pista_audio = Path("output/tramo_01_audio_mix.mp3")
    mezclar_pista_audio(bloques, duracion_video, pista_audio)

    # Mux vídeo con audio inicial
    video_mux = Path("output/tramo_01_mux_temp.mp4")
    print("\n--- Uniendo vídeo con pista de voz sincronizada ---")
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

    # Normalizar audio a -14 LUFS (estándar YouTube)
    video_final = Path("output/tramo_01_completo.mp4")
    normalizar_master_loudnorm(video_mux, video_final)

    # Limpieza del temporal
    video_mux.unlink(missing_ok=True)

    # Verificación final
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

# -*- coding: utf-8 -*-
"""
Analiza un clip de grabación de pantalla usando Gemini 2.5 Flash:
1. Detecta marcas de tiempo de OBS al inicio y final.
2. Identifica el rango útil (útil = sin OBS).
3. Detecta tiempos muertos/esperas.
4. Genera una propuesta de narración técnica concisa en inglés.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


def analizar_video(ruta_clip: Path):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] No se encontró GEMINI_API_KEY en .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"\nSubiendo clip a Gemini API: {ruta_clip.name} ({ruta_clip.stat().st_size / (1024*1024):.2f} MB)...")
    video_file = client.files.upload(file=ruta_clip)

    try:
        print("Esperando procesamiento del vídeo...", end="", flush=True)
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            print(".", end="", flush=True)
            video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            print(f"\n[ERROR] Falló el procesamiento en Gemini: {video_file.error.message}")
            sys.exit(1)

        print(" ¡Listo!")

        prompt = """
You are an expert video editor and technical narrator for a fast-paced YouTube tech channel (1-3 min tutorials).
Analyze this screen recording clip and provide a JSON response with the following exact keys:

1. "obs_start_cut_seconds": Float. The exact second when the OBS Studio window disappears from screen and the actual tutorial workspace (browser, terminal, or IDE) becomes visible.
2. "obs_end_cut_seconds": Float. The exact second when the tutorial action finishes and the user brings up the OBS Studio window to stop recording.
3. "useful_start_seconds": Float (same as obs_start_cut_seconds).
4. "useful_end_seconds": Float (same as obs_end_cut_seconds).
5. "actions_summary": Brief summary in Spanish of what the user does in this clip.
6. "key_events": List of objects [{"timestamp": "MM:SS", "description": "short description in English"}].
7. "dead_times": List of objects [{"start_sec": float, "end_sec": float, "reason": "waiting for load / idle mouse / typing pause"}] indicating idle moments that can be sped up or trimmed.
8. "proposed_narration_en": A direct, punchy, concise English technical narration (1-3 sentences maximum) perfectly describing the key action without fluff or filler.

Output only valid JSON without markdown fences.
"""

        modelos_candidatos = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-flash-latest",
        ]

        response = None
        for mod in modelos_candidatos:
            print(f"Probando análisis con '{mod}'...")
            try:
                response = client.models.generate_content(
                    model=mod,
                    contents=[video_file, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                print(f"Éxito con el modelo '{mod}'!")
                break
            except Exception as e:
                print(f"  Fallo con '{mod}': {e}. Probando siguiente modelo...")
                time.sleep(2)

        if not response:
            print("\n[ERROR] No se pudo analizar el vídeo con ninguno de los modelos candidatos.")
            sys.exit(1)

        salida_json = response.text
        datos = json.loads(salida_json)

        ruta_guardado = ruta_clip.with_suffix(".json")
        ruta_guardado.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[OK] Análisis guardado en: {ruta_guardado.name}\n")
        return datos

    finally:
        # Limpieza del archivo remoto en Google Cloud
        try:
            client.files.delete(name=video_file.name)
            print(f"Archivo temporal remoto '{video_file.name}' eliminado correctamente.")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clip", type=str, required=True, help="Ruta al archivo .mp4")
    args = parser.parse_args()

    clip_path = Path(args.clip)
    if not clip_path.exists():
        print(f"[ERROR] No existe el archivo: {clip_path}")
        sys.exit(1)

    resultado = analizar_video(clip_path)
    print("=" * 60)
    print(" RESULTADO DEL ANÁLISIS DE GEMINI")
    print("=" * 60)
    print(f"Inicio útil (corte OBS):    {resultado.get('useful_start_seconds')} s")
    print(f"Fin útil (corte OBS):       {resultado.get('useful_end_seconds')} s")
    duracion_util = resultado.get('useful_end_seconds', 0) - resultado.get('useful_start_seconds', 0)
    print(f"Duración útil estimada:     {duracion_util:.2f} s")
    print("\nAcciones detectadas:")
    print(resultado.get("actions_summary"))
    print("\nTiempos muertos / esperas:")
    for dt in resultado.get("dead_times", []):
        print(f"  - {dt.get('start_sec')}s a {dt.get('end_sec')}s ({dt.get('reason')})")
    print("\nPropuesta de narración (Inglés):")
    print(f'"{resultado.get("proposed_narration_en")}"')
    print("=" * 60)


if __name__ == "__main__":
    main()

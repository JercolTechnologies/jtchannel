# -*- coding: utf-8 -*-
"""
Script para generar pruebas de voz con OpenAI TTS para el canal de trucos técnicos en inglés.
Permite comparar voces escuchando antes de fijar una para la producción.

Uso:
    python scripts/probar_voces.py
    python scripts/probar_voces.py --voces onyx,echo,alloy,nova --modelo tts-1-hd
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Modelos que aceptan el parámetro 'speed'
MODELOS_CON_SPEED = {"tts-1", "tts-1-hd"}

TEXTO_DEFECTO = (
    "In this tutorial, we are connecting an autonomous agent to Supabase "
    "using the Model Context Protocol. First, let's configure the environment variables."
)

PRECIOS_1K_CHARS = {
    "tts-1": 0.015,
    "tts-1-hd": 0.030,
}


def medir_duracion(ruta_archivo: Path) -> float:
    """Mide la duración exacta del audio con ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta_archivo),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Prueba de voces con OpenAI TTS")
    parser.add_argument(
        "--voces",
        type=str,
        default="onyx,echo,alloy,nova",
        help="Lista de voces separadas por coma",
    )
    parser.add_argument(
        "--modelo",
        type=str,
        default="tts-1-hd",
        help="Modelo de OpenAI (tts-1-hd, tts-1, gpt-4o-mini-tts)",
    )
    parser.add_argument(
        "--texto",
        type=str,
        default=TEXTO_DEFECTO,
        help="Texto a sintetizar",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Velocidad (solo aplicable a tts-1 y tts-1-hd)",
    )
    parser.add_argument(
        "--instructions",
        type=str,
        default=None,
        help="Instrucciones de estilo/ritmo para modelos basados en LLM",
    )
    parser.add_argument(
        "--salida",
        type=str,
        default="pruebas_audio",
        help="Directorio donde guardar los archivos de prueba",
    )

    args = parser.parse_args()

    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("\n[ERROR] Falta OPENAI_API_KEY en el entorno o en el archivo .env.")
        print("Por favor, abre el archivo .env y asigna tu clave antes de continuar.\n")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    voces = [v.strip() for v in args.voces.split(",") if v.strip()]
    out_dir = Path(args.salida)
    out_dir.mkdir(parents=True, exist_ok=True)

    longitud_texto = len(args.texto)
    tarifa_1k = PRECIOS_1K_CHARS.get(args.modelo, 0.030)
    coste_estimado_voz = (longitud_texto / 1000.0) * tarifa_1k
    coste_total_estimado = coste_estimado_voz * len(voces)

    print("\n" + "=" * 60)
    print(" PRUEBA DE VOCES — OpenAI TTS")
    print("=" * 60)
    print(f"Modelo:            {args.modelo}")
    print(f"Voces a probar:    {', '.join(voces)} ({len(voces)} llamadas)")
    print(f"Longitud texto:    {longitud_texto} caracteres")
    print(f"Coste estimado:    ${coste_total_estimado:.4f} USD")
    print("-" * 60)
    print(f'Texto: "{args.texto}"')
    print("-" * 60)

    # Parámetros extra según modelo
    extra_params = {}
    if args.modelo in MODELOS_CON_SPEED:
        extra_params["speed"] = args.speed
    elif args.instructions:
        extra_params["instructions"] = args.instructions

    resultados = []

    for voz in voces:
        nombre_archivo = f"{voz}_{args.modelo}.mp3"
        ruta_salida = out_dir / nombre_archivo
        print(f"Generando voz '{voz}'...", end=" ", flush=True)

        try:
            with client.audio.speech.with_streaming_response.create(
                model=args.modelo,
                voice=voz,
                input=args.texto,
                response_format="mp3",
                **extra_params,
            ) as response:
                response.stream_to_file(ruta_salida)

            duracion = medir_duracion(ruta_salida)
            tamano_kb = ruta_salida.stat().st_size / 1024.0
            print(f"OK ({duracion:.2f} s, {tamano_kb:.1f} KB)")
            resultados.append((voz, ruta_salida, duracion, tamano_kb))
        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(" RESUMEN DE PRUEBAS GENERADAS")
    print("=" * 60)
    for voz, ruta, dur, kb in resultados:
        print(f" - {voz.upper():<8} | {dur:5.2f} s | {kb:5.1f} KB | {ruta}")
    print("\nEscucha los archivos en la carpeta 'pruebas_audio/' para elegir la voz.\n")


if __name__ == "__main__":
    main()

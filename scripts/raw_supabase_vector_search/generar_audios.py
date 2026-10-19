# -*- coding: utf-8 -*-
"""
Generación de audios TTS para Video 02:
Raw Supabase Vector Search vs LangChain

Modelo: gpt-4o-mini-tts
Voz: nova
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AUDIOS_DIR = Path("output/raw_supabase_vector_search/audios")
AUDIOS_DIR.mkdir(parents=True, exist_ok=True)

TRAMOS = [
    {
        "id": "tramo_01",
        "title": "The Hook",
        "text": (
            "Every AI influencer sold you that you need LangChain and complex vector databases "
            "to build semantic search. That's complete hype. You already have Postgres. "
            "Today, we're doing raw vector search in Supabase with zero frameworks and just four lines of code."
        ),
    },
    {
        "id": "tramo_02",
        "title": "Supabase Setup",
        "text": (
            "First, jump into your Supabase dashboard. Open the SQL Editor and enable the vector extension. "
            "Then create a simple table with a vector column matching your model’s dimensions. "
            "That’s it. Your database is now an AI vector store."
        ),
    },
    {
        "id": "tramo_03",
        "title": "Seeded Data Bridge",
        "text": (
            "In the Table Editor, we've populated our documents with sample records and their "
            "1536-dimensional embeddings. Ready to be matched against any concept."
        ),
    },
    {
        "id": "tramo_04",
        "title": "Python & Cosine Distance",
        "text": (
            "Now the Python side. We grab an embedding for our query using OpenAI's small model in two lines. "
            "Then, connect straight to Supabase and query your table using the native cosine distance operator. "
            "No wrappers, no bloated abstractions—just pure SQL finding the nearest neighbor."
        ),
    },
    {
        "id": "tramo_05",
        "title": "Result & Outro",
        "text": (
            "And boom: instant semantic match with sub-second latency and total control over your query. "
            "Stop adding layers you don’t need. And hey—if you want an autonomous AI agent to manage "
            "your Supabase database and run these setups for you, check out my previous video on the screen right now."
        ),
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

def generar_todos():
    client = OpenAI()
    print("=" * 60)
    print("GENERACIÓN DE AUDIOS TTS — VIDEO 02 (gpt-4o-mini-tts / nova)")
    print("=" * 60)
    
    resultados = []
    duracion_total = 0.0
    
    for tramo in TRAMOS:
        ruta_mp3 = AUDIOS_DIR / f"{tramo['id']}.mp3"
        print(f"Generando [{tramo['id']}] {tramo['title']}...", end=" ", flush=True)
        
        resp = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=tramo["text"],
            instructions=INSTRUCCIONES_TONO,
            response_format="mp3",
        )
        resp.write_to_file(ruta_mp3)
        
        dur = medir_duracion(ruta_mp3)
        duracion_total += dur
        print(f"OK ({dur:.2f} s)")
        
        resultados.append({
            "id": tramo["id"],
            "title": tramo["title"],
            "path": str(ruta_mp3),
            "duration": dur,
            "text": tramo["text"],
        })
    
    print("-" * 60)
    print(f"Duración total de locución: {duracion_total:.2f} s ({duracion_total/60:.2f} min)")
    print("=" * 60)
    
    # Guardar manifiesto de audios
    manifest_path = AUDIOS_DIR / "manifest_audios.json"
    manifest_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifiesto guardado en: {manifest_path}")

if __name__ == "__main__":
    generar_todos()

# Metadata de Publicación — Video 02: Raw Supabase Vector Search

Documento oficial de empaque y metadatos para YouTube según las directivas de `PUBLICACION.md` y `GEMINI.md`.

---

## 1. Ficha Técnica del Vídeo Master

| Parámetro | Valor Medido / Especificación | Estado |
|---|---|---|
| **Archivo Master** | `output/raw_supabase_vector_search/tutorial_raw_supabase_vector_search_master.mp4` | Generado |
| **Duración Exacta** | **80.82 s** (01:20.82 / 1 min 21 s) | Cumple (1-3 min) |
| **Resolución & Aspecto** | **1920 × 1080** (16:9 exacto) | Verificado |
| **Tasa de Cuadros** | **60.0 fps** constante (`r_frame_rate=60/1`) | Verificado |
| **Sonoridad Integrada** | **-14.01 LUFS** (EBU R128 para YouTube) | Objetivo: -14.0 LUFS |
| **True Peak** | **-3.01 dBTP** (cero distorsión/clipping) | Cumple (< -1.5 dBTP) |
| **Pista de Voz (TTS)** | `nova` en `gpt-4o-mini-tts` (tono conversacional) | Aprobado |
| **Cama Musical** | `musica.mp3` a **-18.0 dB relativo** (ganancia 0.1160) con fade-in 1.5s y fade-out 2.5s | ADR-004 |
| **Sincronización de Cortes** | Remate entre **1.10s y 1.14s** tras última palabra en cada tramo | Regla 11 bis / ADR-002 |
| **Subtítulos Sincronizados** | `assets/videos/raw_supabase_vector_search/subtitulos_video_02.srt` | Whisper + Alineación |

---

## 2. Título Oficial para YouTube

### Opción Principal (Recomendada):
**`Stop Using LangChain: Raw Supabase Vector Search`** (48 caracteres)

- **Front-loading:** `Stop Using LangChain` en los primeros 22 caracteres.
- **Recuento de keywords en la locución (Regla §2):**
  - *LangChain:* Tramo 01 (Línea 28: *"Every AI influencer sold you that you need LangChain..."*)
  - *Supabase:* Tramo 01, Tramo 02, Tramo 04, Tramo 05 (Mencionado 4 veces)
  - *Vector Search:* Tramo 01, Tramo 02 (Mencionado 3 veces)
  - *Raw:* Tramo 01 (*"Today, we're doing raw vector search..."*)

### Opciones Alternativas (41–55 caracteres):
1. `Raw Vector Search in Supabase: Ditch LangChain` (46 caracteres)
2. `Stop Using LangChain for Vector Search: 8 Lines` (48 caracteres)
3. `You Don't Need LangChain: Raw Supabase Vectors` (46 caracteres)

---

## 3. Miniatura Oficial (Thumbnail)

- **Archivo Oficial:** `assets/videos/raw_supabase_vector_search/thumbnail_1280x720.jpg`
- **Dimensiones:** `1280 × 720` (16:9 exacto).
- **Peso:** **294.7 KB** (Límite estricto de YouTube: 2048 KB).
- **Texto:** `DITCH THE BLOAT` (3 palabras, tipografía metálica 3D con rim light cian neón de alto contraste).
- **Composición e Iluminación:**
  - Rayo esmeralda Supabase rompiendo la cadena pesada de dependencias con chispas de alta energía en el borde derecho (evita fundirse con el fondo `#0f0f0f` del modo oscuro de YouTube).
  - Badge de Python en la esquina inferior izquierda.
  - Test de legibilidad a **120 px de ancho** superado con total claridad (`thumbnail_120px_test.png`).

---

## 4. Descripción Oficial de YouTube

```text
You don't need LangChain, complex frameworks, or dedicated vector databases to build semantic search. Here is how to do raw vector search in Supabase using PostgreSQL pgvector and 8 lines of pure Python.

Every AI influencer sold you heavy abstractions with hundreds of dependencies. In reality, Postgres already does cosine distance search natively with sub-second latency.

---
⚡ SQL SETUP (Supabase SQL Editor):
create extension if not exists vector;

create table documents (
  id serial primary key,
  title text not null,
  embedding vector(1536)
);

---
🐍 PYTHON IMPLEMENTATION (Zero Frameworks):
import os, psycopg
from openai import OpenAI

# 1. Generate query embedding (2 lines)
client = OpenAI()
query_vec = client.embeddings.create(
    input="electric vehicle", 
    model="text-embedding-3-small"
).data[0].embedding

# 2. Query Supabase directly using native cosine distance operator (<=>)
with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    row = conn.execute(
        "SELECT title FROM documents ORDER BY embedding <=> %s::vector LIMIT 1;",
        (str(query_vec),)
    ).fetchone()
    print(f"Top Match: {row[0]}")

---
📺 PREVIOUS VIDEO:
How to connect an autonomous AI agent to Supabase with official MCP:
[Link al Video 01 de Antigravity + Supabase]

#Supabase #PostgreSQL #Python #VectorSearch #LangChain #OpenAI #pgvector #Coding #AI
```

---

## 5. Etiquetas / Tags (Indexador de YouTube)

```text
supabase, vector search, langchain alternative, pgvector, postgresql vector, openai embeddings, text-embedding-3-small, python vector search, psycopg3, semantic search postgres, supabase python tutorial, raw vector search, no langchain, ai development, postgres vector database
```

---

## 6. Checklist Previo a Publicación (§8 `PUBLICACION.md`)

- [x] **Video Render:** 1080p60 exacto, sin caídas de framerate ni artefactos visuales.
- [x] **Normalización de Audio:** -14.01 LUFS EBU R128 (-c:v copy).
- [x] **Música de fondo:** -18.0 dB relativo a la voz con fade-in de 1.5s y fade-out de 2.5s.
- [x] **Sincronización:** Cada tramo cierra entre 1.0s y 1.2s tras la última palabra hablada (cero colas estáticas en silencio).
- [x] **Terminal Zoom:** Zoom digital calibrado al 125% en Tramo 05 para máxima legibilidad de `Top Match: Tesla Model 3`.
- [x] **Subtítulos:** Archivo `.srt` sincronizado por Whisper y alineado 100% con el guion oficial.
- [x] **Miniatura:** 1280x720, < 2048 KB (294.7 KB), legible a 120 px, borde derecho iluminado contra modo oscuro.
- [x] **Seguridad (Regla 12):** Variables sensibles (`DATABASE_URL`, `OPENAI_API_KEY`) almacenadas en `.env`; datos de prueba genéricos.

# PRODUCCION_VIDEO_02.md — Especificación de Montaje y Guion

Este documento contiene la **especificación completa, guion de narración y directivas técnicas** para que el agente ensamblador monte el segundo vídeo del canal.

---

## ⚠️ DIRECTIVA OBLIGATORIA PARA EL AGENTE ENSAMBLADOR: Reestructuración de Carpetas con Nombres Descriptivos

A partir de este vídeo, el repositorio maneja múltiples producciones. Para evitar colisiones y mantener el orden sin usar identificadores genéricos (`video_01`, `video_02`), **las carpetas deben nombrarse por el nombre descriptivo / slug de cada vídeo**:

```text
clips/
├── antigravity_supabase/          # Mover clips del vídeo 1 aquí
└── raw_supabase_vector_search/    # Grabaciones de pantalla de este vídeo (clip_01 a clip_04)

output/
├── antigravity_supabase/          # Mover renders y audios del vídeo 1 aquí
└── raw_supabase_vector_search/    # Renders finales y temporales de este vídeo

assets/videos/
├── antigravity_supabase/          # Assets permanentes del vídeo 1
└── raw_supabase_vector_search/    # thumbnail.png (<2048 KB) y metadata.md de este vídeo

scripts/
└── raw_supabase_vector_search/    # Scripts de montaje específicos para este vídeo
```

---

## 1. Ficha Técnica y Empaque

- **Título Oficial (48 caracteres):**  
  `Stop Using LangChain: Raw Supabase Vector Search`  
  *(Cumple regla de front-loading: keyword `Stop Using LangChain` al inicio).*
- **Texto de Miniatura (3 palabras):**  
  `NO MORE LANGCHAIN`  
  *(Concepto visual: Símbolo de stop/cruz roja sobre el logo de LangChain a la izquierda; a la derecha, terminal o interfaz oscura con el operador `<=>` brillando en cian `#00ffff` sobre fondo `#0f0f0f` con halos de luz).*
- **Formato:** Horizontal 16:9 (`1920x1080`, 60 fps).
- **Voz TTS:** `nova` en `gpt-4o-mini-tts`.
- **Evolución sonora:**
  - Narración masterizada a **`-14.0 LUFS`** (EBU R128) con doble pasada de `loudnorm` en FFmpeg (`-c:v copy`).
  - Música de fondo a **`-18.0 dB` relativo** a la voz con fade-in y fade-out (según ADR-004).
- **Corte dinámico:** Remate de vídeo entre **1.0 y 1.2 segundos** tras la última palabra hablada (según ADR-002 y Regla 11 bis de `GEMINI.md`).

---

## 2. Código Exacto a Mostrar en Pantalla

### A. SQL en Supabase (SQL Editor)
```sql
-- 1. Habilitar pgvector
create extension if not exists vector;

-- 2. Tabla de documentos con columna vectorial
create table documents (
  id serial primary key,
  title text not null,
  embedding vector(1536)
);

-- 3. Datos de prueba
insert into documents (title, embedding) values 
  ('Tesla Model 3', '[...vector de prueba...]'),
  ('iPhone 15 Pro', '[...vector de prueba...]');
```

### B. Python Script (`search.py`) — Código Crudo en 8 Líneas
```python
import os, psycopg
from openai import OpenAI

# 1. Obtener embedding de la consulta en 2 líneas
client = OpenAI()
query_vec = client.embeddings.create(
    input="electric vehicle", 
    model="text-embedding-3-small"
).data[0].embedding

# 2. Búsqueda directa en Supabase con el operador nativo <=>
with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    row = conn.execute(
        "SELECT title FROM documents ORDER BY embedding <=> %s::vector LIMIT 1;",
        (str(query_vec),)
    ).fetchone()
    print(f"Top Match: {row[0]}")
```

---

## 3. Desglose de Tramos y Guion de Narración (`nova`)

### Tramo 01: El Gancho (The Hook)
- **Duración estimada:** ~16 segundos.
- **Acción visual en pantalla (Miguel):**  
  Abre VS Code mostrando un archivo con imports densos y anidados de LangChain (`from langchain.vectorstores...`, `from langchain.embeddings...`). Selecciona todo el código con `Ctrl+A` y lo borra de golpe con `Backspace`, dejando el editor negro y limpio.
- **Texto de locución TTS (Inglés):**  
  > *"Every AI influencer sold you that you need LangChain and complex vector databases to build semantic search. That's complete hype. You already have Postgres. Today, we're doing raw vector search in Supabase with zero frameworks and just four lines of code."*

---

### Tramo 02: Habilitación en Supabase
- **Duración estimada:** ~24 segundos.
- **Acción visual en pantalla (Miguel):**  
  Navegador en el dashboard de Supabase (el proyecto existente). Abre el **SQL Editor**, pega las 3 líneas de SQL (`create extension if not exists vector; create table documents...`) y hace clic en **Run**. El panel inferior muestra *"Success. No rows returned"*.
- **Texto de locución TTS (Inglés):**  
  > *"First, jump into your Supabase dashboard. Open the SQL Editor and enable the vector extension. Then create a simple table with a vector column matching your model’s dimensions. That’s it. Your database is now an AI vector store."*

---

### Tramo 03: Embedding y Búsqueda Vectorial con `<=>`
- **Duración estimada:** ~38 segundos.
- **Acción visual en pantalla (Miguel):**  
  Regresa a VS Code. Muestra el archivo `search.py` ya escrito. Resalta con el cursor la llamada a `client.embeddings.create` y luego la sentencia SQL con `ORDER BY embedding <=> %s`. Abre la terminal integrada y ejecuta: `python search.py`.
- **Texto de locución TTS (Inglés):**  
  > *"Now the Python side. We grab an embedding for our query using OpenAI's small model in two lines. Then, connect straight to Supabase and query your table using the native cosine distance operator. No wrappers, no bloated abstractions—just pure SQL finding the nearest neighbor."*

---

### Tramo 04: El Remate y Llamada al Vídeo 01
- **Duración estimada:** ~20 segundos.
- **Acción visual en pantalla (Miguel):**  
  La terminal imprime `Top Match: Tesla Model 3` en menos de 200 ms. Se hace un zoom sutil o pausa de 2 segundos para apreciar la respuesta. Los últimos 5 segundos quedan con la pantalla limpia para insertar la tarjeta/end-screen de YouTube hacia el vídeo de Antigravity + Supabase.
- **Texto de locución TTS (Inglés):**  
  > *"And boom: instant semantic match with sub-second latency and total control over your query. Stop adding layers you don’t need. And hey—if you want an autonomous AI agent to manage your Supabase database and run these setups for you, check out my previous video on the screen right now."*

---

## 4. Checklist de Seguridad (Regla 12 de `GEMINI.md`)

- [ ] La variable `DATABASE_URL` y `OPENAI_API_KEY` deben estar en el archivo `.env`, **nunca escritas en claro en `search.py`**.
- [ ] En la grabación de pantalla del dashboard de Supabase, asegurar que el `Project Ref` y la barra lateral de proyectos no revelen información confidencial privada (o aplicar máscara con `drawbox` en el montaje, según ADR-005).
- [ ] Datos de prueba genéricos (ej. nombres de coches y smartphones).

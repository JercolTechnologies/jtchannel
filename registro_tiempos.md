# Registro de Tiempos de Producción — Canal Tech YouTube

Métrica real de tiempo de producción por pieza (grabar, narrar, montar, revisar, subir) según directiva de `GEMINI.md` (§1).

El objetivo es medir cuánto cuesta de verdad cada vídeo una vez engrasado el flujo por tramos, para evaluar la viabilidad de la estrategia de volumen hacia la monetización (4.000 / 8.000 horas).

---

## Historial de Producción por Vídeo

| Vídeo ID / Slug | Tema / Título | Duración Vídeo | Grabación Pantalla | Redacción Guion / TTS | Montaje & Sync Script | Revisión & Empaque | Tiempo Total Estimado |
|---|---|---|---|---|---|---|---|
| **01: `antigravity_supabase`** | *Connect AI Agent to Supabase (Official MCP)* | 02:44 min | ~25 min | ~15 min | ~35 min (setup pipeline inicial) | ~15 min | **~90 min** (curva inicial de calibración de pipeline) |
| **02: `raw_supabase_vector_search`** | *Stop Using LangChain: Raw Supabase Vector Search* | 01:21 min | ~20 min (4 clips) | ~10 min (5 micro-tramos) | ~20 min (scripts automatizados) | ~10 min | **~60 min** (reducción del 33% en tiempo de entrega) |
| **03: `cursor_mcp_enoent_fix`** | *Fix Cursor MCP Server Errors: The ENOENT Fix* | 00:53 min | ~20 min (3 clips + guía Cursor) | ~5 min (3 micro-tramos) | ~12 min (montaje + jump-cut + miniatura) | ~5 min | **~42 min** (reducción acumulada del 53% frente al Vídeo 01) |

---

## Observaciones y Aprendizajes de Eficiencia

1. **Vídeo 01:**
   - Mayor tiempo invertido en definir el estándar de sonoridad (`-14.0 LUFS`), las dos pasadas de `loudnorm` con `-c:v copy`, la calibración de la cama musical a `-18 dB` ([ADR-004](file:///c:/Users/mapog/Documents/new_channel_agy/ADR.md#L75-L100)) y la sanitización con `drawbox` ([ADR-005](file:///c:/Users/mapog/Documents/new_channel_agy/ADR.md#L103-L125)).
2. **Vídeo 02:**
   - La grabación por micro-tramos funcionó con gran rapidez.
   - El script de transcripción Whisper + alineación de subtítulos se ejecutó en segundos sin intervención manual.
   - La implementación de zoom digital en FFmpeg resolvió la necesidad de zoom sin obligar a Miguel a pelear con atajos de OBS.
3. **Vídeo 03:**
   - A pesar de usar un IDE nuevo para Miguel (Cursor `3.19.7`), la preparación automatizada del proyecto (`preparar_entorno_demo.py`) y del prompt de PowerShell ahorró toda edición de privacidad posterior.
   - El *jump-cut* quirúrgico en FFmpeg evitó regrabar un clip con error de pegado, manteniendo el tiempo de montaje + miniatura artesanal en apenas ~12 minutos.

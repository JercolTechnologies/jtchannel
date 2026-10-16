# Architectural Decision Records (ADR) — Canal Tech Agéntico

Registro de decisiones de arquitectura y diseño del pipeline de producción de vídeo.

---

## ADR-001: Pipeline ligero por tramos y motor de síntesis TTS

- **Fecha:** 16 de octubre de 2026
- **Estado:** Aceptado e implementado

### Contexto
El canal produce tutoriales técnicos directos al grano (1 a 3 minutos) sobre herramientas de IA agéntica y bases de datos (Antigravity, MCP, Supabase, Vercel, GitHub). El pipeline heredado (`content-hub`) estaba sobrediseñado para documentales con slots y Wikimedia, siendo inviable para un flujo de producción rápido y ágil.

### Decisión
1. Desarrollar un pipeline propio, modular y ligero en Python con scripts independientes por tramo (`scripts/montar_tramo_XX.py`).
2. Trabajar por tramos funcionales (grabación de pantalla de cada micro-paso primero, narración y TTS después).
3. Seleccionar el modelo de TTS `gpt-4o-mini-tts` con la voz `nova` y un prompt de tono conversacional de desarrollador (amigable, enérgico, cercano, evitando tono monocorde de clase teórica).
4. Estándar técnico estricto: formato horizontal 16:9 a 1080p60 (`1920x1080`, `60 fps`).
5. Masterización de audio normalizada a `-14.0 LUFS` (estándar EBU R128 para YouTube) mediante doble pasada de `loudnorm` en FFmpeg aplicada con `-c:v copy` para no degradar el vídeo.

### Consecuencias y alternativas descartadas
- **Descartado:** Reutilizar el pipeline monolítico `content-hub`. Era inviable por acoplamiento y dependencias innecesarias.
- **Descartado:** Grabar voz en directo durante la grabación. El TTS post-grabación permite ritmo perfecto, inglés nativo sin titubeos y flexibilidad para iterar el texto.

---

## ADR-002: Sincronización dinámica de cortes vídeo-audio (eliminación de colas estáticas)

- **Fecha:** 16 de octubre de 2026
- **Estado:** Aceptado e implementado (aprobado tras validación en Tramos 02, 03 y 04)

### Contexto
En los primeros montajes (Tramo 01 y 02), aparecían colas de 4 a 5 segundos al final del clip con la pantalla fija y silencio absoluto.

### Causa raíz
El corte del vídeo se calculaba a priori basándose exclusivamente en los segundos brutos de la grabación de pantalla, antes de conocer la duración real del audio de narración. Como el modelo de TTS (`gpt-4o-mini-tts`) no es determinista al milisegundo en su duración, cuando la locución terminaba antes de la marca fijada para el vídeo, este continuaba reproduciéndose en silencio.

### Decisión
1. **Invertir la dependencia en el remate del clip:**
   - La síntesis de voz se mide con precisión milimétrica (`ffprobe`).
   - El punto de corte final del vídeo se ancla dinámicamente a la duración real de la locución:  
     $$\text{Corte final de vídeo} = \text{Inicio bloque} + \text{Duración audio real} + \text{Margen de cierre (1.0 a 1.2 s)}$$
2. **Verificación de doble vía (sin cortes prematuros):**
   - Antes de aplicar el corte, se comprueba que las acciones visuales clave (scrolling, despliegue de tablas, clicks) ya hayan culminado dentro de esa ventana temporal.
   - Si la acción en pantalla requiere más tiempo, se adapta la narración para acompañarla en lugar de truncar la interfaz en movimiento.
3. Se formaliza como regla operativa obligatoria en `GEMINI.md` (§5, Regla 11 bis).

### Consecuencias y alternativas descartadas
- **Descartado:** Congelar el último frame (*freeze frame*). Es una mala práctica que disfraza la falta de contenido dinámico.
- **Descartado:** Aceptar silencios de más de 1.5 segundos. Dañan gravemente la retención de audiencia en vídeos cortos.
- **Resultado:** Vídeos con ritmo ágil, transiciones fluidas y remates precisos sin tiempos muertos.

---

## ADR-003: Fusión de micro-acciones (Prompt + Output) mediante Jump Cuts

- **Fecha:** 16 de octubre de 2026
- **Estado:** Aceptado e implementado

### Contexto
El flujo original separaba Clip 03 (enviar el prompt de creación de esquema) y Clip 04 (la respuesta en el chat con las tablas creadas). Tratar cada clip como un tramo independiente generaba un corte inconcluso tras enviar el prompt y un inicio estático al mostrar el output.

### Decisión
1. Fundir Clip 03 y Clip 04 en un solo tramo unificado (Tramo 03).
2. Utilizar un *jump cut* limpio: mostrar el prompt y el click en "Send" (~12s), saltar inmediatamente el tiempo de procesamiento/espera de la IA, y caer de golpe en la respuesta terminada con las tablas y datos de prueba (~12s).
3. Aplicar esta misma lógica de salto en Clip 05 (Tramo 04), eliminando los 4 segundos donde se buscaba el texto en pantalla.

### Consecuencias y alternativas descartadas
- **Descartado:** Mostrar la animación de carga/procesamiento de la IA. Aporta cero valor pedagógico y ralentiza el tutorial.
- **Resultado:** Vídeo mucho más dinámico (~25s en lugar de 40s+), enfocado 100% en la acción y en el resultado tangible.

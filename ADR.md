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

---

## ADR-004: Mezcla de Cama Musical Relativa y Normalización Estéreo EBU R128

- **Fecha:** 16 de octubre de 2026
- **Estado:** Aceptado e implementado

### Contexto
El tutorial requería una pista musical de fondo para darle dinamismo, ritmo moderno y energía, pero sin competir con la voz de la narración ni dificultar la comprensión en altavoces de teléfonos móviles.

### Decisión
1. **La voz es el ancla absoluta:**  
   Nunca se ajusta la voz a la música. Se mide primero la sonoridad integrada en LUFS de la locución (`medir_lufs` -> `-14.36 LUFS`).
2. **Cálculo de ganancia relativa matemática:**  
   La música se coloca exactamente a **18 dB por debajo de la voz**:
   $$\text{objetivo} = \text{LUFS}_{\text{voz}} - 18.0\text{ dB}$$
   $$\text{ganancia} = 10^{\frac{\text{objetivo} - \text{LUFS}_{\text{musica}}}{20.0}}$$
   Para `The_Iron_Grove` (-13.65 LUFS), esto supuso una atenuación de **-18.71 dB** (multiplicador $\times 0.1160$).
3. **Mapeo estéreo espacial:**  
   La narración mono se centra en el panorama estéreo (`aformat=channel_layouts=stereo`), mientras que la música conserva su imagen estéreo espacial completa.
4. **Bucle y fundidos:**  
   Se utiliza `-stream_loop -1` para cubrir los últimos 2.63 segundos del vídeo, con un `fade-in` inicial de 1.5s y un `fade-out` de cierre de 2.5s que remata exactamente con el final del vídeo.
5. **Master final YouTube:**  
   Mezcla con `amix` (sin atenuar la voz) y masterización mediante filtro `loudnorm` de dos pasadas alcanzando **`-14.02 LUFS`** (objetivo: -14.0 LUFS) y **`-3.37 dBTP`** (sin distorsión ni clipping), manteniendo el vídeo original intacto (`-c:v copy`).

### Consecuencias y alternativas descartadas
- **Descartado:** Fijar un volumen de música a ojo o con un porcentaje arbitrario (ej. "volumen al 20%"). Las pistas musicales de stock varían enormemente en compresión y masterización; medir en LUFS garantiza consistencia industrial entre vídeos.

---

## ADR-005: Sanitización Digital de Seguridad en Grabaciones de Pantalla (Regla 12)

- **Fecha:** 16 de octubre de 2026
- **Estado:** Aceptado e implementado

### Contexto
Durante la revisión previa a publicación, se identificó que en la barra lateral izquierda de Antigravity IDE (`Projects`) se leían claramente nombres de proyectos reales, clientes y repositorios privados (`rifasonlineapp`, `jercol-tech-web`, `Base Hipica`, etc.). Publicar dicha información vulneraba la Regla 12 de seguridad de `GEMINI.md`.

### Decisión
1. **Recorte digital con fondo nativo plano (`drawbox`):**  
   Aprovechando que el fondo de la interfaz de Antigravity es un color uniforme (`#161616` / BGR `[22, 22, 22]`), se aplica una máscara sólida que vacía el área de proyectos convirtiéndola en un espacio oscuro limpio y natural.
2. **Calibración milimétrica de coordenadas (v2):**  
   - **X (Horizontal):** De `0` a `320` píxeles. Se detiene exactamente en la línea divisoria vertical (`x=320`), eliminando cualquier pestaña o solapamiento sobre el área de chat.
   - **Y (Vertical):** De `305` a `940` píxeles. Deja intacto y legible el menú superior `Customizations` (que termina en `y=275`) con 30 px de margen, y preserva abajo el acceso a `Settings` (que inicia en `y=985`).
3. **Máscara temporal condicional:**  
   El filtro se activa únicamente durante los instantes en que Antigravity está en pantalla mediante expresiones `enable='gte(t, ...)'`, respetando al 100% las pantallas de Chrome/Supabase.
4. **Integración en el código base:**  
   Se incorporó directamente en los scripts de montaje de cada tramo (`scripts/montar_tramo_01.py` a `04.py`), de forma que cualquier re-renderizado futuro esté sanitizado por defecto.

### Consecuencias y alternativas descartadas
- **Descartado:** Regrabar las pantallas en OBS. El parche digital con el color exacto es indistinguible de la interfaz nativa y ahorra tiempo sin introducir desajustes con el audio ya cronometrado.
- **Descartado:** Desenfoque / difuminado gaussiano (*blur*). Un recuadro borroso llama la atención del espectador y evidencia censura; el fondo plano limpio hace parecer que simplemente no hay proyectos recientes abiertos.

---

## ADR-006: Pipeline de Búsqueda Vectorial Pura (Supabase + pgvector) y Ensamblado de 5 Tramos

- **Fecha:** 19 de octubre de 2026
- **Estado:** Aceptado e implementado

### Contexto
Producción del Vídeo 02 (*Stop Using LangChain: Raw Supabase Vector Search*). El objetivo pedagógico era demostrar que no hacen falta frameworks pesados (como LangChain con decenas de dependencias) para construir búsqueda semántica en producción, bastando 8 líneas de Python (`psycopg` + OpenAI embeddings + operador nativo `<=>` de pgvector en Supabase).

### Decisiones
1. **Estructura modular en 5 tramos con clip puente pedagógico (Tramo 03):**
   - A petición editorial para responder a la duda del espectador de "¿dónde están almacenados los datos?", se incorporó el tramo puente `clip_02_b` mostrando el *Table Editor* de Supabase con los registros poblados (`Tesla Model 3`, `iPhone 15 Pro`) y sus vectores reales de 1536 dimensiones.
2. **Eliminación de latencia de red mediante Jump Cut quirúrgico:**
   - En `clip_03`, la espera de red de 11 segundos de la llamada a la API y una ventana emergente de notificación de VS Code fueron recortadas limpiamente en FFmpeg, conectando la pulsación de *Enter* con la respuesta en pantalla en < 0.2 segundos aparentes.
3. **Cámara digital con zoom programático (FFmpeg):**
   - Ante la limitación de realizar zoom interactivo en OBS durante la grabación de pantalla, se implementó en FFmpeg un zoom digital suave del 125% (`crop=w=1536:h=864:x=0:y=216,scale=1920:1080:flags=bicubic`) centrado en la esquina inferior izquierda de la terminal durante el Tramo 05 para garantizar máxima legibilidad en dispositivos móviles.
4. **Sincronización milimétrica de cortes (Regla 11 bis / ADR-002):**
   - Los 5 tramos se anclaron dinámicamente al fin de locución de `nova` (`gpt-4o-mini-tts`), manteniendo un margen de cierre estricto de entre 1.10s y 1.14s tras la última palabra hablada, erradicando cualquier cola estática o silencio muerto.
5. **Masterización de audio estéreo y cama musical (ADR-004):**
   - Mezcla de locución y pista musical `musica.mp3` atenuada a exactamente **-18.0 dB relativo** (multiplicador $\times 0.1160$) con *fade-in* de 1.5s y *fade-out* de 2.5s.
   - Doble pasada de `loudnorm` con `-c:v copy` alcanzando **`-14.01 LUFS`** integrada y **`-3.01 dBTP`** (cumplimiento exacto EBU R128 para YouTube).
6. **Subtítulos sincronizados alineados al guion oficial:**
   - Transcripción Whisper `base` palabra por palabra y alineación algorítmica con `SequenceMatcher` contra el guion oficial en inglés, asegurando 100% de precisión ortográfica en términos técnicos (*pgvector*, *Supabase*, *LangChain*, *Postgres*).

### Consecuencias y alternativas descartadas
- **Descartado:** Saltar directo de SQL a Python sin mostrar el *Table Editor*. Dejaba un vacío pedagógico confuso sobre el origen de los datos vectorizados.
- **Descartado:** Mostrar la espera de 11 segundos en la terminal de VS Code. Habría destruido la retención de audiencia en los primeros 60 segundos del vídeo.
- **Resultado:** Vídeo de 80.82 segundos, ultra-dinámico, técnicamente impecable y listo para publicar.



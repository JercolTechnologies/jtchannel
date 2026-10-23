# GEMINI.md — canal tech en inglés (grabación de pantalla + voz TTS)

Creado el 15 de octubre de 2026. Este archivo es tu punto de entrada: léelo entero antes
de hacer nada y vuelve a él cuando dudes.

---

## 1. Qué es este proyecto

Un canal de YouTube **en inglés**, sobre **trucos de programación y de IA agéntica**:
conectar un agente por MCP a Supabase, Vercel, GitHub y similares, y mostrar cómo se hace.

- **Formato:** grabación de pantalla con narración TTS encima. Vídeos de **1 a 3 minutos**,
  directos al grano, sin relleno.
- **Siempre 16:9.** Un vídeo horizontal cuenta como vídeo largo aunque dure 2 minutos y
  suma horas de visionado; uno cuadrado o vertical de hasta 3 minutos pasa a ser un Short
  y no suma. (Fuente: guías de terceros, no la página oficial de YouTube; consultado el
  15/10/2026.)
- **Quién hace qué:** Miguel graba la pantalla. Tú construyes el script que monta el
  vídeo y, cuando se acuerde, escribes la narración.
- **Por qué existe:** es a la vez una prueba de cuánto cuesta producir en volumen y un
  canal que Miguel quiere monetizar cuanto antes. Su objetivo es publicar mucho, con
  constancia, sin que cada pieza cueste horas.

### Lo que se mide desde el primer vídeo

Miguel estima que un vídeo de 2 minutos cuesta unos 20 minutos de trabajo suyo una vez
engrasado. **Es una estimación, no una medida.** Anota en un `registro_tiempos.md` cuánto
cuesta de verdad cada vídeo (grabar, narrar, montar, revisar, subir). Con diez vídeos hay
una media real, y esa cifra decide si la estrategia de volumen aguanta.

Contexto de monetización, para que sepas por qué importa el volumen. El umbral de entrada
al Programa de Socios es de 1.000 suscriptores y 4.000 horas de visionado en vídeos
largos, y **sube a 8.000 horas el 1 de febrero de 2027** (TechCrunch, 10/08/2026). Los
Shorts no suman horas. Con vídeos de 2 minutos y 50% de retención cada visita aporta
1 minuto, así que hacen falta del orden de 240.000 visitas en total (480.000 después de
febrero). Por eso el coste por pieza manda.

---

## 2. Decisiones ya tomadas — no las reabras

1. **No se usa el pipeline `content-hub`.** Está hecho para documentales investigados
   (marcadores de plano, Wikimedia, Manim, regresiones). Para esto es peso muerto.
   Aquí hay un **script propio**, pequeño.
2. **Se graba primero, el TTS va después.** La narración describe lo que de verdad se ve.
3. **Se trabaja por tramos, no con el vídeo entero.** Ver el siguiente apartado.
4. **Este proyecto vive aparte.** No modifiques nada dentro de
   `C:\Users\mapog\Documents\content-hub`, y no lo importes. Lo que necesitas de ahí ya
   está copiado en `referencias/` (apartado 4); no hace falta que vayas a buscarlo.

---

## 3. Arquitectura Cerrada y Estándar de Producción (NO INVENTAR — EJECUTAR TAL CUAL)

Todas las preguntas de diseño iniciales quedaron cerradas, probadas y aprobadas en los Vídeos 01, 02 y 03 y en la Tanda 01 de Shorts (`ADR-001` a `ADR-008` en `ADR.md`). **Cualquier modelo que trabaje en este repositorio tiene prohibido inventar estilos, cambiar coordenadas, alterar volúmenes o improvisar flujos.** Debe limitarse a aplicar las especificaciones exactas de esta sección.

---

### 3.1 Parámetros Globales Innegociables (Comunes a Largos y Shorts)

1. **Voz y Modelo TTS (`ADR-001`):**
   - **Modelo:** `gpt-4o-mini-tts` (API de OpenAI).
   - **Voz:** `nova`.
   - **Parámetro de ritmo:** Prohibido enviar `speed` (da error o se ignora en modelos LLM). Se usa exclusivamente `instructions`:
     - En **Vídeos Largos:** `"Speak in a friendly, clear, and energetic developer tone. Keep a brisk, engaging pace like a senior engineer walking a friend through a cool setup—natural, warm, and direct, never robotic or like a dry academic lecture."`
     - En **Shorts:** `"Speak at a brisk, punchy, high-retention developer pace. Sound confident, direct, and energetic, with zero long pauses between clauses."`
   - **Pronunciación fonética en el guion:** Si el guion menciona extensiones o comandos con punto que el TTS lee de forma extraña, escríbelos fonéticamente en el texto enviado al TTS (`"where-dot-exe"`, `"mcp-dot-json"`, `"dot-cmd"`).

2. **Mezcla de Audio y Normalización EBU R128 (`ADR-004`):**
   - **La voz manda siempre:** Primero se mide la sonoridad integrada de la voz con `loudnorm` de FFmpeg (`LUFS_voz`).
   - **Cama musical a `-18.0 dB` exactos debajo de la voz:**
     $$\text{objetivo\_musica} = \text{LUFS}_{\text{voz}} - 18.0\text{ dB}, \quad \text{ganancia} = 10^{\frac{\text{objetivo\_musica} - \text{LUFS}_{\text{musica}}}{20.0}}$$
   - **Prohibido ajustar volumen a ojo** (ej. `volume=0.2` sin medir LUFS).
   - **Masterización final en doble pasada (`-14.0 LUFS`, `TP=-1.0` o `-1.5`, `LRA=11`):**
     Se ejecuta **siempre en una pasada final separada con `-c:v copy`** sobre el MP4 ya renderizado. Nunca filtres y copies streams al mismo tiempo en MoviePy.

3. **Sanitización y Privacidad desde el Origen (`ADR-005` y `ADR-007`):**
   - **Antes de que Miguel grabe en OBS:** Si habrá terminal PowerShell o rutas en archivos de configuración (`.json`, `.env`), proporciona siempre un script de preparación (`preparar_entorno_demo.py`) que coloque binarios/archivos en una ruta neutra (`C:\Tools\...` o `C:\demo\...`) y oculte el usuario de Windows en el prompt de PowerShell (`function prompt { "PS $(Split-Path (Get-Location) -Leaf)> " }`).
   - **Si ya se grabó y aparece un dato privado (nombres de proyectos de clientes, rutas con usuario, correos):** Tápalo en FFmpeg con `drawbox` usando el color hexadecimal exacto del fondo nativo de la interfaz (ej. `#161616` en Antigravity IDE) para que parezca espacio vacío natural. **Prohibido usar desenfoque (*blur*)**, porque delata censura.

---

### 3.2 Motor 1 — Vídeos Largos (`1920x1080 @ 60fps`, 16:9)

- **Scripts canónicos de referencia (copiar estructura de aquí, no escribir desde cero):**
  - Montaje, jump-cuts, mezcla musical, subtítulos `.srt` y masterización: `scripts/cursor_mcp_enoent_fix/ensamblar_video_03.py` y `scripts/raw_supabase_vector_search/ensamblar_master_completo.py`.
  - Miniatura `1280x720`: `scripts/cursor_mcp_enoent_fix/generar_thumbnail.py`.
- **Reglas exactas del Motor 1:**
  1. **Grabación por micro-tramos:** Miguel graba 3 a 5 clips cortos (`clip_01.mp4`, `clip_02.mp4`, etc.). Antes de redactar o montar, extrae fotogramas cada 1–2 segundos con FFmpeg y verifica visualmente qué ocurre en cada segundo.
  2. **Eliminación de tiempos muertos con Jump Cuts (`ADR-003`, `ADR-006`, `ADR-007`):**
     - Prohibido mostrar esperas de red, animaciones de carga de IA o tropiezos de teclado.
     - Recorta las esperas con un *jump cut* limpio en FFmpeg o acelera tipeos largos (máximo `1.5x–2.5x`), haciendo coincidir el corte con el verbo de acción en la voz (ej. al decir *"paste"* o *"hit Enter"*).
  3. **Corte final de cada tramo anclado al audio (`ADR-002` / Regla 11 bis):**
     $$\text{Duración del tramo de vídeo} = \text{Fin de la última palabra hablada} + 1.0\text{ a }1.2\text{ s}$$
     - **Prohibido** dejar colas en silencio $> 1.5\text{ s}$ y **prohibido** congelar el último fotograma (*freeze frame*).
  4. **Zoom digital programático (`ADR-006`):** Si una terminal o panel tiene letra pequeña, aplica zoom digital suave en FFmpeg (`crop` + `scale=1920:1080:flags=bicubic`) en lugar de pedirle a Miguel que haga zoom en OBS.
  5. **Subtítulos `.srt` externos (NO quemados en vídeos largos):**
     - En vídeos largos **nunca** se queman subtítulos en el vídeo (ensucian el código en pantalla completa).
     - Se genera un archivo `.srt` externo usando Whisper local para obtener los *timestamps* y `SequenceMatcher` contra el guion oficial para garantizar 0 faltas de ortografía en términos técnicos (`pgvector`, `ENOENT`, `Supabase`, `uvx`).
  6. **Miniatura (`1280x720`, `< 2048 KB`):**
     - Fondo oscuro pero **con fuente de luz y borde exterior visible** (contorno o resplandor cian/esmeralda/rojo en los bordes para que no se funda con el `#0f0f0f` del modo oscuro de YouTube).
     - De 2 a 4 palabras máximas en tipografía bold gigante, verificada reescalando a `120 px` de ancho.

---

### 3.3 Motor 2 — YouTube Shorts (`1080x1920 @ 60fps`, 9:16)

- **Script motor oficial (usar directamente añadiendo el diccionario `spec` del nuevo Short):**
  - `scripts/shorts/motor_shorts.py` (`ADR-008`).
  - Fondo animado común: `assets/shorts/shorts_bg_loop.mp4` (generado por `scripts/shorts/generar_fondo_shorts.py`).
- **Por qué existe un motor aparte:** Los Shorts buscan suscriptores y clic hacia el `Related video` en el feed vertical. Sus reglas de composición y corte final son opuestas a las de los vídeos largos.
- **Reglas exactas del Motor 2 (Fórmula v2 aprobada — prohibido modificar su estética):**
  1. **Viewport Flotante a 90 grados (`1000x860` en `x=40, y=360`):**
     - El vídeo recortado de la pantalla original se ubica en `x=40, y=360` con tamaño `1000x860`.
     - **Esquinas rectas a 90 grados.** Queda **terminantemente prohibido** poner bordes redondeados, marcos de colores o barras superiores falsas estilo macOS (los 3 puntitos). Se muestra la interfaz original flotando sobre el fondo animado con su sombra 3D profunda (`rgba(0,0,0,195)` con blur gaussiano).
  2. **Hook tipográfico superior flotante (sin cajas):**
     - Dos líneas en mayúsculas arriba: Línea 1 en blanco (`#FFFFFF`, `y=155`) y Línea 2 en verde esmeralda (`#3ECF8E`, `y=235`), fuente `Segoe UI Bold` 64pt con sombra negra dura. Prohibido encerrar el hook en cajas o rectángulos.
  3. **Inicio en movimiento (`0.00s`) + Loop Infinito Doble (Verbal y Visual al fotograma):**
     - **Prohibido** empezar el Short con una pantalla estática. El Plano 1 (`0.00s`) debe arrancar en mitad de una acción visual llamativa.
     - **Loop verbal (`margen_cierre_s = 0.08`):** El guion del Short termina en una frase inconclusa/conector (*"...because that's literally how"*, *"...because it's time to"*, *"...if you noticed"*) que empalma gramaticalmente con la primera palabra del segundo `0.00s`. El vídeo se corta exactamente a **`+0.08s`** de la última palabra medida con Whisper (sin silencios al final).
     - **Loop visual (`0 píxeles` de salto):** Si el Plano 1 empieza en el segundo $t_0$ de un clip origen con `crop` $C_1$, el último plano del Short **debe** usar ese mismo clip origen y el mismo `crop` $C_1$, terminando exactamente en $t_0$ (por ejemplo, de $t_0 - 2.5\text{ s}$ a $t_0$). Así, cuando YouTube reinicia el Short del último frame al primero, la imagen continúa en movimiento continuo sin ningún salto.
  4. **Sincronía estricta voz-corte visual por palabra:**
     - Una vez generado el TTS del Short, se corre Whisper (`word_timestamps=True`) para ver en qué segundo exacto se pronuncia cada acción clave, y se ajustan los `target_dur` de cada `shot` para que los cambios de plano caigan al milisegundo sobre la palabra hablada.
  5. **Subtítulos quemados dinámicos `.ass` (`y=1375`) + Diccionario Fonético (`REEMPLAZOS_SUBS_VISUALES`):**
     - A diferencia de los largos, los Shorts **sí llevan subtítulos quemados** en `y=1375` (2–3 palabras por bloque, `Segoe UI Bold` 76pt, animación pop-in `115% -> 100%`, palabras clave resaltadas en `#3ECF8E` y `#FFD166`).
     - Toda palabra escrita fonéticamente para el TTS (`where-dot-exe`, `mcp-dot-json`, `dot-cmd`) debe estar registrada en `REEMPLAZOS_SUBS_VISUALES` dentro de `motor_shorts.py` para que en pantalla se pinte la sintaxis técnica exacta (`WHERE.EXE`, `MCP.JSON`, `.CMD`).
  6. **Banner CTA inferior (`y=1675`) + Música por tanda:**
     - Píldora inferior discreta con flecha dorada `▼` apuntando al enlace de `Related video` de YouTube Studio.
     - La música de la tanda se toma desde el segundo indicado por Miguel (en la Tanda 01: `assets/shorts/music/The_Iron_Grove.mp3` desde `00:00:14.0`), atenuada a `-18.0 dB` bajo la voz y masterizada a `-14.0 LUFS`.

---

## 4. Qué consultar del pipeline, y por qué

Todo está en **`referencias/`**, con las mismas rutas relativas que en el repo original:
`referencias/engine/scripts/tts.py`, `referencias/AGENT.md`, etc. Son **copias del 15 de
octubre de 2026** de `C:\Users\mapog\Documents\content-hub\`.

Tres cosas sobre estas copias:

- **Son de solo lectura.** No las edites: son material de consulta, no parte de tu código.
- **Son una instantánea.** El original sigue evolucionando y no te enterarás. Si algo
  depende de que esté al día, díselo a Miguel.
- **Donde contradigan este `GEMINI.md`, manda este.** El caso conocido: `EDITORIAL.md` y
  `AGENT.md` prohíben ejecutar `git`; en este proyecto sí se puede (apartado 6). Y
  `AGENT.md` habla de hooks, regresiones y `canal.json`, que aquí no existen.

**Trae lo que necesites a tu código, no lo importes.** El motor original es compartido por
otros dos canales y depende de un `manifest.json` y de una capa de configuración que aquí
no existen. Los números de línea de la tabla se refieren a la copia de `referencias/`.

| Archivo | Para qué te sirve | Qué traer |
|---|---|---|
| `engine/scripts/tts.py` | La llamada a OpenAI TTS ya resuelta | La forma de pedir el audio por *streaming* a disco; el límite de **4096 caracteres** por petición con corte en fin de oración; y la separación entre modelos. `tts-1`/`tts-1-hd` aceptan `speed`; los modelos basados en LLM no, regulan el ritmo con `instructions` en prosa. Mandar el parámetro equivocado es un error de API. Y el aviso en voz alta cuando un parámetro se ignora. **No traigas la clase entera**, depende de `config` y del manifest |
| `engine/scripts/assembler.py`, funciones `medir_lufs`, `_combinar_lufs`, `_medir_para_loudnorm`, `_normalizar_master` (líneas ~954–1100 y ~1256–1300) | Normalizar la sonoridad del audio final | Si hay voz sola (sin música) basta `loudnorm` de ffmpeg con doble pasada: medir primero, aplicar después con `linear=true`. **La normalización va en una pasada aparte sobre el mp4 ya escrito** (`-c:v copy`), porque MoviePy muxea el audio con *streamcopy* y ffmpeg no puede filtrar y copiar a la vez. Eso mató un render entero una vez. Usa el ffmpeg de `imageio_ffmpeg`. Si la medición falla, cae a una sola pasada en vez de tumbar el render |
| `engine/scripts/align.py` y `subs.py` | Solo si decidís subtítulos | Whisper local aporta los **tiempos** y el texto sale del guion, no de la transcripción. Está descrito en `AGENT.md`; **yo no he leído estos dos archivos**, léelos tú antes de copiar nada |
| `engine/scripts/probar_voces.py` | Elegir voz escuchando | Genera el mismo párrafo en varias voces. Úsalo o escribe uno propio equivalente |
| `AGENT.md`, trampas 2 y 8 | Dos fallos que te pueden pasar a ti | **Trampa 2:** `status` comprobaba que el archivo estuviera, no que sirviera (gráficos a 480p15 en un vídeo 1080p60 pasaron todas las comprobaciones). Comprueba la ficha técnica con `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 ARCHIVO`. **Trampa 8:** cambiar de modelo de TTS mueve todas las duraciones, entre +1% y +41% según la escena, y el modelo **no es determinista en duración**: el mismo texto dio 46,5 s y 48,9 s. Regenerar un audio suelto descuadra ese tramo |
| `AGENT.md`, sección «Si una herramienta falla…» | Un hábito | Antes de decir que no puedes hacer algo, inténtalo. Antes de pedirle a Miguel que te pegue un archivo, comprueba si puedes leerlo |
| `PUBLICACION.md`, §1 y §2 | Miniatura y título | Miniatura 1280×720, 16:9 exacto, **máximo 2048 KB** (más y YouTube rechaza la subida), se juzga **reducida a 120 px de ancho**, una sola tipografía bold de 2 a 4 palabras. Un fondo casi negro se funde con el modo oscuro de YouTube (`#0f0f0f`): negro con luz, no negro plano. Con generadores de imagen: fija relación de aspecto, colores en hexadecimal y de dónde viene la luz, y **nunca les pidas texto**. Título: 41–55 caracteres, palabra clave al principio, y cuenta las menciones del término en la narración antes de prometerlo |
| `PUBLICACION.md`, §3 y §8 | Descripción y lista previa a publicar | Gancho en las dos primeras líneas, el resto para el indexador. **No uses los capítulos (§4)**: no encajan en vídeos de 2 minutos |
| `EDITORIAL.md` | Cómo se decide qué se dice | Aplica el espíritu, no la letra: aquí no hay litigios ni personas vivas, pero sí **documentación de herramientas que cambia**. Ver reglas de trabajo, punto 3 |
| `CANAL_NUEVO.md`, sección «Las decisiones que hay que tomar una vez» | Qué decidir una sola vez | Voz, paleta, música y licencias, como lista de preguntas. **Ignora lo del `canal.json` y las 16 claves**: pertenecen al motor y aquí no lo hay |
| `LICENCIAS.md` | Solo si usáis música | Qué licencias se admiten. Si no hay música ni stock, no lo necesitas |

---

## 5. Reglas de trabajo

Son las que ya rigen en el pipeline, filtradas a las que te afectan.

### Iterar antes de ejecutar

1. **Se propone y se espera.** Se discute hasta estar 1:1 con Miguel en la lógica y solo
   entonces se ejecuta. **No edites archivos en el mismo mensaje en que propones el
   cambio**, ni para un detalle pequeño.
2. **Jamás asumas.** Si te falta un dato para decidir, pregúntalo. No rellenes el hueco
   con lo más probable.
3. **No valides por condescendencia.** Si tienes argumentos de peso, defiende tu
   posición. Y cuando Miguel acierte en algo, díselo.

### Veracidad

4. **Nada entra sin búsqueda web y sin fuente que Miguel pueda abrir.** Ningún dato sale
   de tu memoria de entrenamiento. Cada dato lleva **fecha de consulta**. Si no hay
   fuentes fiables, dilo: un «no lo sé» es preferible a una alucinación.
5. **Documentación técnica, doble cuidado.** En este canal lo que envejece son los
   comandos, las versiones y las interfaces. Antes de dar un paso por bueno, comprueba
   la sintaxis contra la documentación oficial **de la versión que Miguel usa en la
   grabación**, y anota cuál es.
6. **Investigación antes de redacción.** Verifica primero, escribe después.
7. **Comprueba las fechas con un comando**, nunca de memoria.
8. **Una cifra que no puedes verificar no se dice.** Se sustituye o se quita.

### Verificar, no suponer

9. **Lee antes de afirmar.** No afirmes nada sobre un archivo que no hayas abierto en
   esta sesión. Toda afirmación sobre el código lleva su evidencia: archivo y línea, o el
   comando que la produjo. Si no puedes citarla, la frase es «no lo he comprobado».
10. **Los fallos de este tipo de trabajo son silenciosos.** Un paso que termina bien no
    significa que haya salido bien. Después de cada paso, **mira la salida**: `ffprobe`
    para la ficha técnica, una escucha del audio, un vistazo al vídeo. Nunca des por
    bueno un «OK» que no hayas comprobado.
11. **Falla con ruido.** Si algo se sale de lo esperado, el script lo dice y para. Prefiere
    un error en la terminal a una sorpresa en el mp4.
11 bis. **Sincronización de corte vídeo-audio.** El corte final de cada tramo se
    ajusta a la duración real del audio de narración: el vídeo debe finalizar entre
    1.0 y 1.2 segundos después de la última palabra hablada, verificando siempre que
    la acción visual clave haya concluido. Quedan prohibidas las colas estáticas en
    silencio (>1.5s) y los cortes prematuros de acciones en curso.

### Seguridad de las grabaciones — regla dura

12. **Las grabaciones muestran secretos.** Conectar Supabase, Vercel o GitHub deja a la
    vista claves de API, tokens, URLs de proyecto y correos. **Publicar uno es un
    incidente de seguridad, no un fallo de edición.**
    - Graba con **proyectos desechables**.
    - **Rota las claves** después de cada grabación en que hayan aparecido.
    - **Revisa el vídeo entero antes de subirlo**, buscando precisamente eso.
    - Si ves un secreto en un clip, avisa a Miguel de inmediato y no lo proceses.
13. **Nunca subas un `.env` ni una grabación a git.** Tu `.gitignore` los excluye desde el
    primer commit (`.env`, `*.mp4`, `*.mp3`, `*.wav`, claves).

### Gasto y ejecución

14. **Todo lo que gasta dinero o sobrescribe, se propone y se espera aprobación.** El TTS
    cuesta dinero de API: antes de generar, di cuánto texto vas a mandar y cuántas
    llamadas. Prueba con un tramo por céntimos antes de gastar el vídeo completo, y no
    regeneres audios sin razón.
15. **Análisis, lectura y scripts de verificación van sin pedir permiso.**

### Cómo se escribe

16. **Comentarios y mensajes en castellano, explicando el porqué, no el qué.** Un
    comentario que repite el código sobra.
17. **Windows 11 y PowerShell 5.1.** En PowerShell 5.1 **no existen `&&` ni `||`**; un
    comando encadenado así no falla a medias, no arranca. Escribe `a; if ($LASTEXITCODE
    -eq 0) { b }`. No des por hecho la versión: se comprueba con
    `$PSVersionTable.PSVersion`, o se escribe para 5.1, que corre en las dos. El IDE de
    Miguel es VS Code.
18. **Todo código que le pongas a Miguel en el chat va en un archivo `.md`.**

---

## 6. ADR.md, `git` y el orden de las cosas

Este proyecto tiene **su propio `ADR.md`**, numerado desde ADR-001, independiente del de
`content-hub`.

**Cuándo se escribe un ADR:** cuando tomes una decisión de arquitectura, por ejemplo cómo
se encaja un clip contra su audio, qué modelo de TTS se elige o qué se hace con los
secretos. Se escribe el **porqué** y **lo que se descartó**, no solo lo que se hizo.

**Cuándo NO:** no escribas en `ADR.md` ni en ningún archivo de estado hasta que Miguel
haya probado el trabajo. Un registro de algo que no funciona es peor que ningún registro.

**El orden es este y no se salta ningún paso:**

```
testeo  →  Miguel aprueba  →  ADR  →  commit  →  push
```

- Tú testeas y le enseñas el resultado a Miguel.
- **Hasta que él apruebe no hay ADR, ni commit, ni push.**
- Con la aprobación: escribes el ADR, haces el commit y haces el push.
- Puedes usar `git` con normalidad (a diferencia de `content-hub`, donde está vetado).
  Si esta carpeta aún no es un repositorio, **pregunta antes de inicializar uno**.

---

## 7. Qué NO te afecta, para que no pierdas tiempo

Estas piezas del pipeline original pertenecen al motor de los otros dos canales y aquí no
aplican: `quien_usa.py` y su hook, las dos regresiones, `canal.json` y `aplicar_canal()`,
los marcadores `<<slot>>` y `{{overlay}}`, Wikimedia y Pexels, Manim, `preview --serve`,
la nomenclatura canónica de assets y los criterios editoriales de documentales.

---

## 8. Receta de Ejecución Paso a Paso (Checklist para Cualquier Modelo)

Si eres un agente ejecutando un nuevo vídeo largo o un nuevo Short, **sigue exactamente este orden mecánico sin saltarte ningún paso ni inventar nada**:

### Caso A: Producir un Nuevo Vídeo Largo (`1920x1080 @ 60fps`)
1. **Investigación y Entorno Pre-Grabación:**
   - Verifica en la web la sintaxis oficial y versión exacta de la herramienta.
   - Si el tutorial usa terminal o rutas locales, crea un script `preparar_entorno_demo.py` (basado en `scripts/cursor_mcp_enoent_fix/preparar_entorno_demo.py`) que deje listas las rutas neutras (`C:\Tools\...`) y el prompt de PowerShell limpio sin nombre de usuario.
   - Entrégale a Miguel la guía de grabación dividida en 3 a 4 clips cortos.
2. **Inspección Visual de los Clips Grabados (Sin pedir permiso — Regla 15):**
   - Usa `ffprobe` para verificar resolución/fps y extrae fotogramas cada 1–2 segundos con FFmpeg para ver exactamente en qué segundo ocurre cada clic, tipeo, espera o tropiezo, y verificar que no haya secretos expuestos (Regla 12).
3. **Propuesta de Guion por Tramos y Presupuesto TTS (Reglas 1 y 14):**
   - Presenta a Miguel el guion en inglés por tramos cortos, el conteo exacto de caracteres/llamadas a OpenAI TTS (`gpt-4o-mini-tts`, voz `nova`) y los puntos de corte/jump-cut propuestos. **Espera su aprobación antes de llamar a la API de TTS.**
4. **Montaje, Sincronía, Mezcla y Subtítulos `.srt`:**
   - Copia la estructura de `scripts/cursor_mcp_enoent_fix/ensamblar_video_03.py`.
   - Genera los audios TTS, mide el fin exacto de la última palabra hablada con Whisper y corta cada tramo a `+1.0s`–`1.2s` del final de la voz (Regla 11 bis).
   - Mezcla la cama musical a `-18.0 dB` relativos a la voz y aplica `loudnorm` de doble pasada a `-14.0 LUFS` con `-c:v copy`.
   - Genera el archivo `.srt` externo alineado con `SequenceMatcher` contra el guion.
   - Genera la miniatura `1280x720` (`< 2048 KB`) siguiendo `scripts/cursor_mcp_enoent_fix/generar_thumbnail.py` y verifica su legibilidad reducida a `120 px`.
5. **Verificación y Entrega:**
   - Comprueba el máster con `ffprobe` (`1920x1080`, `60/1`, `-14.0 LUFS`) y extrae capturas de los cortes clave para mostrárselas a Miguel.

### Caso B: Producir un Nuevo YouTube Short (`1080x1920 @ 60fps`)
1. **Inspección de los Fotogramas del Vídeo Largo:**
   - Identifica los 4 momentos visuales más potentes del vídeo largo y elige el punto exacto $t_0$ donde empieza la acción del Plano 1 (y su tramo previo $[t_0 - \Delta t,\; t_0]$ para el último plano de bucle infinito).
2. **Propuesta del `spec` y Presupuesto TTS (Reglas 1 y 14):**
   - Propón a Miguel:
     - `hook_top` (blanco) y `hook_bottom` (verde `#3ECF8E`).
     - El guion de 20–26 segundos (~60–75 palabras) rematado en un conector abierto que empalme con la primera palabra del inicio.
     - El número de caracteres (~330–400 chars, `< $0.01 USD`) para la llamada a `gpt-4o-mini-tts` (`nova`).
   - **Espera su aprobación antes de ejecutar.**
3. **Ejecución en `scripts/shorts/motor_shorts.py`:**
   - Añade el diccionario `spec` en `scripts/shorts/motor_shorts.py` (con `regenerar_tts: False` tras generar el audio por primera vez para no gastar doble).
   - Revisa la salida de timestamps por palabra de Whisper en consola y ajusta los `target_dur` de cada `shot` para que cada corte visual coincida al milisegundo con la palabra hablada, manteniendo que la suma de `target_dur` sea igual a `fin_ultima_palabra + 0.08s`.
   - Si el guion usa palabras fonéticas (`where-dot-exe`, `mcp-dot-json`, etc.), verifica que estén en `REEMPLAZOS_SUBS_VISUALES`.
4. **Verificación obligatoria antes de enseñar a Miguel (Regla 10):**
   - Ejecuta `ffprobe` sobre el `_master.mp4` (`1080x1920`, `60/1`, `-14.0 LUFS`) y extrae 5 capturas (inicio `0.05s`, planos intermedios y final del loop) comprobando que las ventanas estén bien encuadradas, a 90 grados, sin marcos falsos y con el loop visual exacto.
5. **Cierre del Ciclo (Regla 6):**
   - `testeo → Miguel aprueba → ADR.md → registro_tiempos.md → git commit → git push`.

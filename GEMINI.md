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

## 3. El diseño que hay que cerrar con Miguel antes de escribir código

El problema central es **el tiempo muerto**. Una grabación de pantalla tiene esperas
(cargas, despliegues, escribir). Si la narración dura menos que el clip hay silencio, y si
dura más hay que estirar el vídeo, y la forma fácil de estirarlo es **congelar el último
frame**, que no da error y parece una decisión de diseño. En el pipeline original ese fue
exactamente el tipo de fallo que costó caro: un vídeo peor sin ningún aviso.

La propuesta es **encajar por tramos**:

1. Miguel graba en bloques cortos, uno por paso.
2. Cada bloque tiene su narración y su audio TTS.
3. El script mide cada audio y encaja su clip: si sobra vídeo, acelera o recorta las
   esperas; si sobra audio, **avisa**, no congela en silencio.
4. Si el ajuste se sale de un umbral, **el script falla con ruido** y dice en qué tramo.

Lo que **no** está decidido y hay que acordar con Miguel antes de codificar:

- El **tope de aceleración** de un clip y cuánto recorte de esperas es aceptable.
- Qué pasa cuando el audio es más largo que el clip (¿se ralentiza?, ¿se rechaza?).
- Si se quemarán **subtítulos** y si hacen falta (un 1-3 minutos se ve muchas veces sin
  sonido).
- Si habrá **música de fondo**. Por defecto no: sin ella la mezcla de audio se simplifica
  mucho.
- **Quién escribe la narración.** Propuesta: Miguel te pasa una nota breve por tramo,
  tipo «aquí conecto X, aquí falla Y, aquí lo arreglo», y tú redactas; él aprueba. No se
  ha confirmado que puedas analizar el vídeo grabado, así que no lo des por hecho.
- Voz y modelo de TTS (ver abajo). Se elige **escuchando**, no leyendo.

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

## 8. Por dónde empezar

1. Lee este archivo y los documentos de la tabla del apartado 4 que correspondan.
2. **No escribas código todavía.** Propón por escrito el diseño del encaje por tramos y
   las preguntas abiertas del apartado 3.
3. Cuando estéis 1:1 en la lógica, construye lo mínimo: **un solo tramo** de principio a
   fin (grabación → narración → TTS → encaje → mp4 con audio normalizado).
4. Pruébalo. Mide cuánto cuesta. Enseña el resultado.
5. Solo entonces, el flujo completo de `testeo → apruebo → ADR → commit → push`.

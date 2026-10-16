# AGENT.md — Manual para conducir el pipeline de video

Este documento es para un **agente** (p. ej. DeepSeek en Cline) que arma videos con
el motor de `engine/scripts/`. Explica el flujo, las convenciones y las reglas.
Todos los comandos se corren desde la raíz del repo (`content-hub/`) y empiezan por
`python engine/scripts/main.py <PROYECTO> <comando>`. En los ejemplos el proyecto es
`MS_android`.

**¿Es este tu documento?**

- **Video nuevo en un canal que ya existe** → sí, sigue aquí. Y lee
  `channels/<canal>/CRITERIO_*.md` antes de escribir el guion.
- **Canal nuevo desde cero** → no. Ve a **`CANAL_NUEVO.md`**, configúralo, y vuelve.
- **El video ya está renderizado y toca publicarlo** → **`PUBLICACION.md`**.

---

## Si una herramienta falla, no supongas que fallan las demás

**El shell y el acceso a archivos son dos capacidades distintas.** Pueden caerse
por separado y de hecho se han caído por separado.

*(El incidente concreto de abajo ya está resuelto — se arregló con una
actualización el 21 de septiembre de 2026. Se deja escrito porque la lección no
caduca y el error volverá con otra cara.)*

En septiembre de 2026 una actualización de Windows dejó el shell de Linux sin
poder montar la carpeta del repo. Su mensaje de error decía literalmente
*«prevents Claude's workspace from reaching your files»*, y eso se lee como que
no hay acceso a archivos. **Era falso:** las herramientas de lectura, búsqueda,
edición y movimiento de archivos seguían funcionando perfectamente.

Un agente leyó ese mensaje y le pidió a Miguel que le pegara el contenido de un
archivo que podía abrir él mismo — después de haber movido cuatro ficheros y
editado un guion en los minutos anteriores. Tenía la prueba delante y aun así
repitió lo que decía el error.

> **Antes de decir que no puedes hacer algo, intenta hacerlo.** Y antes de
> pedirle al humano que te pegue algo, comprueba si puedes leerlo tú.

Lo que **sí** necesita el shell o la máquina de Miguel: ejecutar Python
(`main.py`, `render_sh.py`, los verificadores), `ffprobe`, `ffmpeg` y Manim.
Todo lo que sea **leer, buscar o editar archivos, no**.

Es el mismo principio que las diez trampas de más abajo: no des por bueno lo que
no hayas comprobado, tanto si es un OK como si es un error.

---

# ⛔ REGLA DURA: leer antes de afirmar

**No se afirma nada sobre un archivo que no se ha abierto en esta sesión.**
No "probablemente", no "según recuerdo", no "por el nombre debe ser".

Esto no es una recomendación de estilo. Es la causa de la mayoría de los errores
que este repo le ha costado a Miguel, y el inventario está al final de esta
sección para que te lo creas en vez de leerlo como un consejo genérico.

### Las cinco formas en que se rompe

1. **Inferir del nombre.** `regresion.py` suena a que prueba el repo entero.
   Monta UNA escena con el ensamblador, así que no prueba nada de Manim: los
   gráficos son `.mp4` ya renderizados que están quietos en `assets/`.
2. **Inferir de un comentario o un docstring.** Pueden estar desfasados respecto
   al código que hay debajo. El código manda.
3. **Inferir de un ADR.** Un ADR dice lo que se **decidió**, no necesariamente lo
   que quedó implementado. `fuentes_de_assets` está en `canal.json`, está
   documentado, y **no lo lee ningún script del repo**.
4. **Extrapolar de una muestra.** Revisar 20 de 89 assets y decir "están bien" es
   afirmar sobre 69 archivos que no se miraron.
5. **La peor: decir que algo está hecho.** No se anuncia un archivo creado, un
   comando corrido ni un cambio guardado sin haberlo hecho en esta sesión.

### La obligación que la hace comprobable

Toda afirmación sobre el código se entrega **con su evidencia**: archivo y línea,
o el comando que la produjo.

Si no se puede citar, la frase correcta es **"no lo he comprobado"**, y se dice
sin adornos y sin rodeos. Miguel prefiere eso mil veces antes que una afirmación
que suena segura y es falsa.

### Y la razón económica, que es la que zanja el debate

Leer es baratísimo comparado con equivocarse. Un `read_file` cuesta segundos. Un
dato falso metido en un guion, o un cambio hecho sobre una suposición, cuesta una
sesión entera —y a veces un render.

### El inventario: nueve afirmaciones falsas en una semana

Septiembre de 2026, video `google_tpu_pivot`. Ninguna de estas salió de un error
de razonamiento: todas salieron de **no abrir el archivo**.

| Lo que se afirmó | Sin haber leído | Lo que era verdad |
|---|---|---|
| "`BigNumberCounter` solo cambia el `-r`" | `componentes.py` | Tenía `11.5` absoluto; en 9:16 se sale de cuadro |
| "`regresion.py` demuestra que `componentes.py` no movió nada" | `regresion.py` | Monta con el ensamblador; no toca Manim |
| "`ComparisonSplit` está en `componentes.py` de `engine/`" | el árbol de `engine/scripts/` | Vive en el canal; en `engine/` no existe ese archivo |
| "te dejo la arquitectura en el archivo" | — | El archivo nunca se creó |
| "los assets están bien" | 69 de 89 assets | Había varios rotos sin marcar, los encontró Miguel |
| "los shorts se cortan del render final" | nada; era una suposición | Los tres cortes fueron rechazados; hubo que escribirlos de cero |
| "levanta un venv para recuperar CUDA" | qué GPU tiene la máquina | Radeon integrada: no hay ninguna GPU que recuperar |
| se entregaron 9 comandos encadenados con `&&` | el prompt `PS C:\...` que estaba en la misma línea | Miguel usa PowerShell; `&&` no existe ahí y el comando no arrancó |
| "el SHORT2 aún no lo has montado" | `videos/SHORT2_exodo/output/` | Ya estaba montado desde hacía cinco horas |

El noveno merece una nota, porque se cometió **el día después** de escribir
esta regla y en el mismo archivo que la contiene. No basta con tener la regla
escrita: hay que ejecutar el `list_directory` ANTES de teclear la frase. El
coste de comprobarlo eran dos segundos; el coste de no hacerlo fue que Miguel
tuviera que dudar de su propia memoria.

Nueve en una semana no es mala suerte. Es lo que pasa por defecto si esta regla
no se aplica a propósito.

---

# ⛔ REGLA DURA: los comandos se escriben para PowerShell

**Miguel trabaja en Windows 11 y su terminal es PowerShell**, tanto la integrada
en VS Code como la de Windows. No es CMD y no es bash.

No se entrega un comando en sintaxis de otra shell "porque se entiende igual".
O corre tal cual se pega, o no sirve.

### Lo que NO se usa

`&&` y `||` como separadores. **No existen en PowerShell 5.1**, el que trae
Windows de fábrica; los introdujo PowerShell 7. Un comando encadenado con `&&`
no falla a medias: no arranca ninguno de los pasos.

| CMD / bash | PowerShell 5.1 |
|---|---|
| `a && b` (b solo si a funcionó) | `a; if ($LASTEXITCODE -eq 0) { b }` |
| `a \|\| b` (b solo si a falló) | `a; if ($LASTEXITCODE -ne 0) { b }` |
| `a ; b` (b siempre) | `a; b` |
| `export X=1` | `$env:X = '1'` |
| `rm -rf dir` | `Remove-Item dir -Recurse -Force` |
| `cat f \| grep x` | `Select-String x f` |

### Para repetir un comando sobre una lista

La forma que se usa aquí —una sola línea, se pega entera, se detiene en el
primero que falle— es un `foreach` con `$LASTEXITCODE`:

```powershell
foreach ($c in 'S01aExodo','S02aExodo') { manim -r 1080,1920 --fps 30 ruta.py $c -o salida; if ($LASTEXITCODE -ne 0) { Write-Host "FALLO EN $c" -ForegroundColor Red; break } }
```

### El matiz que hay que comprobar antes de asumir

Si Miguel tuviera PowerShell 7 instalado, `&&` sí funcionaría. **No se da por
hecho ni en un sentido ni en el otro**: se pregunta, o se escribe para 5.1, que
corre en las dos. Comprobarlo desde su terminal: `$PSVersionTable.PSVersion`.

Y lo de siempre: el prompt de la salida que pega Miguel dice qué shell es. Se
lee antes de escribir el comando, no después de que falle.

---

# Qué eres aquí

Este manual explica cómo **montar** un vídeo. Pero montar es el último tercio del
trabajo, y probablemente no es para lo que te han llamado.

En estos canales el agente también **investiga, escribe el guion y verifica lo
que se afirma**. Esa parte tiene sus propias reglas y no son opcionales:

> ### → Lee `EDITORIAL.md` antes de escribir una sola línea de guion.
>
> Ahí está lo que no se negocia: ningún dato desde la memoria, la investigación
> antes de la redacción, una cifra que no se puede verificar **no se dice** —se
> sustituye—, se propone y se espera, y no se ejecuta git jamás.

Y antes de trabajar en un canal concreto, su manual:

| | |
|---|---|
| The Corporate Code | `channels/the_corporate_code/ESTADO_TCC.md` |
| Sabermetría Hípica | `channels/sabermetria-hipica/ESTADO_SH.md` |

Cada uno dice qué le aplica de las trampas de abajo, cómo está configurado y qué
le ha llegado del motor sin haberlo visto.

---

# PASO CERO: la regresión del canal

**Antes de tocar nada, corre esto:**

```
python engine/scripts/regresion.py <CANAL>
```

Monta una escena conocida con el motor de hoy y la compara contra la que se
validó cuando ese canal publicó. Tarda un par de minutos.

- **Verde** → el motor produce lo mismo. Monta sin mirar nada más.
- **Rojo** → algo cambió. Te dice qué, y con qué frame comparar. **No montes**
  hasta entender si el cambio es una mejora que quieres o algo que se rompió.

### Por qué existe

El motor es uno y lo comparten los canales. Un arreglo hecho para un canal llega
al otro sin que nadie lo pida. Eso es bueno —los arreglos se heredan— pero hasta
agosto de 2026 nadie comprobaba el efecto, y el resultado era descubrirlo a mitad
de una producción.

**Este comando convierte esa sorpresa en un semáforo de dos minutos.**

Si sale rojo y el cambio es una mejora que quieres, se vuelve a congelar la
referencia:

```
python engine/scripts/regresion.py <CANAL> --crear --proyecto <PROYECTO> --escena N
```

Eso deja constancia de que alguien miró y dio el visto bueno, en vez de que el
canal fuera arrastrado sin enterarse.

---

# ⛔ REGLA DURA: el alcance se comprueba, no se supone. Y va sola.

**Esta regla es automática y obligatoria. No requiere que Miguel intervenga.**

Hay un hook `PreToolUse` instalado en `.claude/settings.local.json`. Cuando vas
a editar un `.py` bajo `engine/` o bajo `channels/*/manim/`, se dispara solo y te
inyecta el informe de `quien_usa.py` **antes de que escribas una línea**. No lo
pides tú: llega.

El informe sale con uno de tres estados, y **los tres son distintos**:

| Estado | Qué significa | Qué haces |
|---|---|---|
| **Nada publicado en juego** | El archivo solo alcanza material sin publicar | **Resuélvelo solo.** No preguntes, no pegues el informe |
| **ALCANZA MATERIAL PUBLICADO** | Toca clips de un vídeo ya montado | Corre la regresión de gráficos. Si algo se mueve, **para y pregunta** |
| **NO SE PUDO VERIFICAR** | El hook está perdido | **No es un verde.** Determina el alcance a mano antes de editar |

```
python engine/scripts/quien_usa.py channels/<canal>/manim/sh_linaje.py
python engine/scripts/quien_usa.py fase_previa
python engine/scripts/quien_usa.py PAUSA_FRASE

cd channels/<canal>/manim
python regresion_graficos.py --contra-assets   # contra el vídeo publicado
python regresion_graficos.py                   # contra la referencia congelada
```

### Dónde está el límite, exactamente

**Resuelves solo todo lo que toca material sin publicar.** Eso es el 95% del
trabajo. No pares a pedir permiso por pasos mecánicos, no pegues logs de lo que
arreglaste, no narres cada verificación. La regresión valida por detrás.

**Paras y preguntas cuando toque material publicado**, o cuando la decisión sea
estética, narrativa o de criterio editorial y no haya una lógica clara que la
resuelva. Al parar, **una línea**, no el informe: *«esto mueve N clips de la
parte 1, ¿los congelo o los muevo?»*.

Un proyecto está publicado si existe su `videos/<proyecto>/output/final.mp4`. Es
un hecho comprobable, no una lista que haya que mantener al día.

### Por qué el límite es «publicado», y no «matemático»

Porque el fallo que originó esta regla tenía lógica matemática impecable.

El 28/09/2026 se cambió el defecto de `fase_previa` a `fase - 1`, razonando que
las fases de una cadena son consecutivas y por tanto la anterior es la propia
menos uno. Es cierto. Y alteraba 21 clips de `SH_secretariat_p1`, que ya está en
YouTube, porque **no todo gráfico con fases pertenece a una cadena**:
`01a_versus_apertura` es un versus de fase 7 que va solo.

Un límite del tipo «resuelve solo lo que tenga lógica clara» habría dejado pasar
ese cambio sin una sola alarma. El alcance, en cambio, es un dato que un script
devuelve.

### Por qué esto no es «verifica siempre» otra vez

Porque «verifica siempre» ya estaba escrito en este archivo el día del fallo, y
el cambio **se hizo leyendo**: se abrió `sh_linaje.py`, se leyó `escenas.json`,
se simuló la cadena, se comprobaron los cinco clips implicados. Todo correcto en
local.

El fallo no fue de memoria ni de pereza. Fue de **alcance**: se verificó lo que
estaba delante y se asumió el resto. Ninguna regla de principio evita eso, porque
quien la incumple cree estar cumpliéndola.

Lo que lo evita es que la pregunta tenga una respuesta mecánica y que alguien la
haga sin que se le pida. De ahí el hook.

### Los dos guardianes, y qué ve cada uno

| | Congela | Ve | Ciego a |
|---|---|---|---|
| `engine/scripts/regresion.py` | Una escena **montada** por canal | Motor, mezcla, alineación, LUFS | Los tipos de Manim fuera de esa escena |
| `channels/*/manim/regresion_graficos.py` | Un clip **por tipo** y proyecto | Los 8 tipos de gráficos | Todo lo que pase en el montaje |

Hacen falta los dos. La regresión del motor no cazó el fallo del 28/09 porque
congela la escena 9 y ninguno de los 21 clips era de la escena 9.

`regresion_graficos.py` **nunca escribe en `assets/`**: instancia la clase de
Manim contra su propia carpeta temporal. Un guardián que puede sobrescribir lo
que protege no es un guardián.

---

# ⚠ LEE ESTO ANTES DE EMPEZAR: las diez trampas

Estas diez cosas costaron un día entero de producción en el vídeo
`SH_secretariat_p1` (agosto 2026). **Ninguna dio error.** Todas dijeron OK y
estaban mal, que es exactamente lo que las hace caras: no las encuentras
depurando, las encuentras mirando el vídeo terminado.

Si compruebas estas diez al empezar, te ahorras ese día.

### 1. El TTS en español se rompe con bloques largos, y no es aleatorio

`tts-1-hd` degrada las narraciones largas en español: hacia el **68-75 %** del
audio deja de hablar español y se vuelve ininteligible. Es **determinista**:
volver a pedir el mismo texto lo rompe en el mismo punto. Re-tirarlo no sirve
de nada.

Solo se arregla cambiando el texto o el modelo. Sabermetría usa ya
`gpt-4o-mini-tts`, que además acepta `instrucciones` en prosa (acento, tono).
**The Corporate Code sigue en `tts-1-hd` y en inglés, donde no se ha
manifestado.**

> Antes de gastar en `tts`, mira si hay bloques de narración por encima de
> ~400 caracteres. TCC nunca paso de 409 y por eso nunca lo sufrió.

### 2. `status` comprueba que el archivo ESTÉ, no que SIRVA

Es un detector de presencia, no de conformidad. Los 54 gráficos de Secretariat
estaban a **854×480 y 15 fps** en un vídeo 1080p60, y pasaron las 54
comprobaciones sin una queja.

> Antes de `assemble`, comprueba la ficha técnica de los assets:
> `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 ARCHIVO`

### 3. `render_sh` se salta por existencia, no por calidad

Su comprobación es *«¿existe el archivo?»*, no *«¿existe con la calidad que
pido?»*. **Un render de prueba en baja envenena el asset para siempre** salvo
que alguien se acuerde de `--forzar`. Así llegaron los 54 a 480p15.

### 4. El `guion.md` del proyecto es una COPIA, no un enlace

`videos/<PROYECTO>/guion.md` es un duplicado literal del marcado de
`guiones/`. **El parser lee la copia.** Editar solo `guiones/` deja el pipeline
narrando la versión vieja, y no hay ninguna comprobación de que coincidan.

> Si tocas un guion, toca los dos y verifica con `diff`.

### 5. Un huérfano que empieza por un slot válido SECUESTRA el slot

Si en `assets/` hay dos archivos cuyo nombre empieza por `20b`, el ensamblador
elige uno y no necesariamente el tuyo. `status` lo avisa —«hay 2 archivos»— pero
es un aviso, no un bloqueante, y se pierde entre los demás.

> Un huérfano no es basura inofensiva. Bórralo antes de montar.

### 6. `hereda_de` cambia a los hijos EN SILENCIO

En `escenas.json`, tocar una entrada padre modifica todas las que heredan de
ella. Bajar el `ritmo` de `15a_terlingua_5` aceleró a sus cuatro hijos a la vez;
`12a` pasó de 4,4× a 7,4× de tiempo muerto y nadie avisó.

> `render_sh.py --lista` enseña quién hereda de quién y qué claves recibe sin
> declararlas. Míralo ANTES de tocar un padre.

### 7. Se mide el CONTENIDO contra el hueco, no el clip entero

Un clip incluye `espera_final`, que es cojín y es gratis: ADR-022 lo recorta sin
que se pierda nada. Comparar la duración total del mp4 contra el hueco da
falsas alarmas de «gráficos cortados».

> `duración_del_contenido = duración_del_mp4 − espera_final`. Solo si ESO no
> cabe, se pierde información.

### 8. Cambiar el modelo de TTS mueve TODOS los tiempos

De `tts-1-hd` a `gpt-4o-mini-tts` la narración creció un **16 % de media**, pero
**entre +1 % y +41 % según la escena**. No hay multiplicador global que valga:
los ritmos de `escenas.json` hay que revisarlos uno a uno.

Y el modelo **no es determinista en duración**: el mismo texto dio 46,5 s y
48,9 s en dos corridas. Regenerar un audio suelto después de `align` descuadra
esa escena.

### 9. La miniatura se diseña a 120 px, no a 1280

Casi nadie la ve a tamaño completo. En la parrilla de escritorio son ~246 px, y en
**móvil baja a 168x94** — que es donde está la mayoría del consumo. Todo lo que no
sobreviva ese tamaño es mancha.

> Genera la miniatura, **redúcela a 120 px de ancho** y mírala ahí. Es la única prueba
> que cuenta. Vale más decir menos y que se lea.

Tres cosas medidas que se descubrieron haciendo la del segundo video de TCC:

**El fondo casi negro de marca se disuelve contra el modo oscuro de YouTube.** El
`TCC_BG` es `#131313` y el fondo de la interfaz en modo oscuro es `#0f0f0f`. Medido
sobre dos miniaturas reales: la que tenía negro plano en los cuatro bordes dio
luminancias de 11,5 a 17,8 contra un fondo de 15 — **el cuadro no tiene frontera, se
disuelve en la página**. La que tenía una fuente de luz en un borde dio 131,9 y sí
existe visualmente. Regla: **negro con luz, no negro plano.** Siempre un degradado o
una fuente de luz que le dé borde al cuadro.

**El límite de peso de YouTube son 2048 KB** y te rechaza la subida si lo pasas. Una
imagen recién generada puede venir en 2,4 MB sin que se note.

**Y con Gemini Flow (o cualquier generador), el prompt tiene que ser determinista.**
Flow devuelve lo que le pidas con bastante fidelidad, pero **solo lo que le pidas**:
si no fijas la relación de aspecto, devuelve lo que le parece (nos dio 2752x1536 =
1.79:1, que no es 16:9 y hay que recortar). Fija SIEMPRE y de forma explícita: relación
de aspecto, colores en hexadecimal, dónde va el espacio vacío, y de dónde viene la luz.
Y **nunca le pidas que escriba texto ni cifras** — los modelos de imagen todavía fallan
con números largos. El texto se compone encima en edición, siempre.

El detalle completo de miniaturas está en `PUBLICACION.md`.
### 10. «Uso nominativo» es MARCAS; «uso legítimo» es una DEFENSA

Son cosas distintas y ninguna es una licencia de contenido:

- **Uso nominativo** pertenece al derecho de marcas y **solo cubre logos**. Una
  fotografía tiene copyright del fotógrafo, y esa vía no lo toca.
- **Uso legítimo** (comentario, crítica, análisis) es una **defensa**, no un
  permiso previo. Se sostiene después, mirando los hechos.
- **Que una página no muestre autor ni licencia NO la hace dominio público.**
  La ausencia de información no es una licencia.

> Si usas algo por comentario, etiquétalo `Uso legítimo (comentario)` en
> `CREDITS.txt`. Poner «Public domain» es afirmar un hecho que a lo mejor no
> puedes sostener, y queda escrito en el archivo que existe para auditarte.

---

## Y la lección que las une

Las diez son **fallos mudos**. El pipeline ejecuta y no verifica: un verde no
significa que esté bien, significa que el paso terminó.

Hasta que las comprobaciones estén en el código (ver `MEJORAS.md`), el trabajo
de verificar es tuyo. **No des por bueno un OK que no hayas comprobado.**

---

## Regla de oro: mira antes de actuar

Antes y después de cada paso, corre el reporte de estado y **decide en base a él**:

```
python engine/scripts/main.py MS_android status --json
```

Devuelve, por escena: si hay `audio`, su `duration`, el `mode` (`numero` o `shots`),
si los shots están `aligned`, y cada asset con `present` / `kind` (video|imagen) /
`canonical` / `suggest`. Y a nivel proyecto: `ready_to_assemble`, `blockers` (impiden
render) y `warnings` (no bloquean). **No corras `assemble` hasta que
`ready_to_assemble` sea `true`.**

## Antes de escribir el guion: lo que la retención ya nos enseñó

Estos no son principios de estilo, son lecturas de curvas de retención de videos ya
publicados. El agente de cada video es el que escribe el guion, así que esto hay que
tenerlo ANTES de ordenar las escenas, no después.

### El conflicto tiene que aterrizar antes de los 90 segundos

**Evidencia, no opinión.** En el primer video del canal TCC (Microsoft vs. Android,
6:09) la retención cae del **96,5% al inicio a menos del 50% en 1:40**. Ese tramo es
justo donde el guion monta el trasfondo: casos antimonopolio, adquisiciones tempranas,
contexto jurídico. Bien escrito, bien narrado, y perdió a la mitad de la sala.

El segundo video corrigió la estructura sin proponérselo: abre con la cifra y con las
cuatro salidas en los primeros **23 segundos**, y a 1:09 ya está dentro del drama. Donde
el primer video llegaba al conflicto, el segundo ya iba por el segundo acto.

La regla que se deriva: **el trasfondo no sostiene retención, el conflicto sí.** Si el
contexto hace falta —y a veces hace falta— se reparte en gotas DENTRO del conflicto, no
se sirve antes en bloque. Comparar las dos curvas de retención cuando el segundo video
acumule datos va a ser la prueba limpia de esto.

### El primer plano no es el primero que se escribe, es el que más pesa

Si hay una cifra, un nombre o una contradicción que resume el video entero, va en el
plano 1. No como adelanto ni como teaser: como afirmación. El video de TCC abre diciendo
"quinientos catorce mil millones de dólares" y recién en el segundo 13 explica de qué
son. Ese hueco es el que retiene.

### Cuántos shorts salen de un video: lo decide el contenido

No hay cuota. El número sale de **cuántos momentos aguantan solos** sacados de su
contexto. Un momento aguanta solo si tiene una afirmación sorprendente y se entiende sin
lo anterior. Del video de 8:32 salieron exactamente tres; forzar un cuarto habría sido
relleno. En otro video pueden ser dos, o cinco.

Y el criterio para escribirlos no es "resumir el video": es que cada short sea del mismo
nicho y tono que el largo, para que el suscriptor que gane sea el que después sí va a
ver un documental de nueve minutos.

### El perfil de audiencia NO es universal: vive en el doc del canal

Cómo te encuentra la gente cambia por canal, y eso decide cómo se empaqueta. TCC vive de
recomendación; un canal de datos hípicos probablemente viva de búsqueda (la gente teclea
nombres de caballos y de carreras). Empaquetar uno con el criterio del otro es un error
caro.

Ese perfil, con sus números, está en `channels/<canal>/CRITERIO_*.md`. **Léelo antes de
decidir el título y la miniatura.**

## El flujo

```
parse -> fetch --auto -> preview --serve -> tts -> align -> subs -> assemble
                              ^______|
                          (corriges ahí mismo)
```

Este es el flujo **hands-off** por defecto (ADR-021/022). El humano no elige assets uno
por uno: revisa la hoja de contactos del paso 3 y corrige ahí lo que no pegue.

1. **parse** — lee el guion y genera `manifest.json` + la checklist.
   `... MS_android parse --script channels/the_corporate_code/guiones/<guion>.md`
2. **fetch --auto** — consigue B-roll y lo deja **YA promovido** en `assets/` con el
   nombre canónico, sin pausa para elegir candidatos. Rutea por shot: `pexels` (default)
   o `wikimedia` si el marcador trae `| wikimedia` como 4to campo (personas/productos
   reales identificables). Si Wikimedia no encuentra nada, cae solo a Pexels. Requiere
   `PEXELS_API_KEY` en `engine/.env` (Wikimedia no necesita key).
   `... MS_android fetch --auto`
   - Alternativa **manual** (para curar un shot puntual a mano): `fetch` sin `--auto` baja
     varios candidatos a `assets/_candidates/` para elegir y mover uno tú mismo.
   - **No confíes en que la query buena trae la imagen buena.** El reintento progresivo
     va quitando términos hasta que algo responde, así que una búsqueda específica que
     no casa acaba trayendo cualquier cosa antes que nada. Hay que ABRIR las imágenes,
     no leer las queries.
3. **preview --serve** — **este es el modo bueno** (ADR-026). Levanta un servidor local
   en `http://127.0.0.1:8000` con la query de cada plano en un campo editable: cambias
   el texto, das Enter y baja otra imagen en el sitio, sin recargar. También cambias
   fuente (`pexels`/`wikimedia`) y tipo (`foto`/`video`), y hay un botón para **subir
   imagen propia** declarando licencia y autor. Lo que edites se guarda en
   `videos/<proyecto>/queries.json`, que **manda sobre el guion** — el guion no se toca.
   `... MS_android preview --serve`
   - `preview` a secas genera `preview_assets.html` estático para mirarlo a mano, sin
     poder editar. Ojo: **es una foto del momento en que se generó**, no se actualiza
     solo. Si pusiste assets después, regenéralo.
   - **`reject`** — desde la terminal, veta una imagen para siempre y baja otra.
     Equivale al botón "descartar" del preview.
4. **tts** — genera las voces (OpenAI, voz onyx). **Cuesta dinero de API.** Acepta
   `--scenes "1,4"` para probar dos escenas por centavos antes de gastar el guion
   completo, y si un audio ya existe **lo salta** en vez de volver a cobrarlo. No uses
   `--overwrite` sin necesidad. `... MS_android tts`
5. **align** *(solo si hay marcadores `<<slot>>`)* — fija el segundo exacto de cada
   shot con whisper local, y cachea los timestamps en `audio/NN_audio.json`.
   `... MS_android align`
6. **subs** — genera `videos/<proyecto>/subtitulos.srt` con la línea de tiempo del video
   completo, title cards incluidas. **El texto sale del guion, no de la transcripción**:
   whisper solo aporta los tiempos. Córrelo DESPUÉS de `align`. No van quemados en el
   video: se suben como pista aparte. `... MS_android subs`
7. **assemble** — renderiza `output/final.mp4`. Usa `--scenes 1,2` para un preview
   barato antes del render completo.

**`all`** corre la cadena entera de una vez. Úsalo solo cuando ya sabes que no vas a
querer revisar nada en medio — se salta el punto donde cambiar imágenes es gratis.

### Dónde corre cada paso (importante si te conectas por el puente)

`parse`, `status`, `fetch`, `preview`, `reject` y `tts` corren en cualquier sitio.
**`align` y `assemble` NO:** `align` necesita whisper instalado y `assemble` necesita la
tipografía que fija `canal.json`, que hoy apunta a una ruta de Windows
(`C:\Windows\Fonts\arialbd.ttf`). En una VM Linux esa ruta no existe y whisper no está,
así que esos dos pasos se corren en la máquina del humano. Si algún día quieres que un
agente renderice, hay que meter las fuentes en el repo y apuntar `canal.json` a una ruta
relativa — con la salvedad de que Arial es fuente licenciada de Microsoft.

### Y después del render

El pipeline entrega un `.mp4` y un `.srt`. Todo lo que viene después —miniatura, título,
descripción, capítulos, tarjetas, pantalla final y shorts— está en **`PUBLICACION.md`**.
Es la mitad del trabajo y tiene sus propias trampas, varias medidas con números.

## Nombrado canónico de assets (OBLIGATORIO)

`status` valida esto y sugiere el nombre correcto en `warnings`/`suggest`. Respétalo.

- **Escena con un solo asset:** `NN_descripcion.ext` → `04_campus.mp4`.
- **Varios assets en una misma escena (o shots):** `NNa_`, `NNb_`, `NNc_` en el orden en
  que aparecen → `04a_campus.mp4`, `04b_rubin.jpg`, `04c_dinero.png`.
- **El tipo lo da la EXTENSIÓN, no el nombre:** `.mp4/.mov/...` = video; `.jpg/.png/...`
  = imagen. No pongas el tipo en el nombre. `status` muestra `[vid]`/`[img]`.
- Prohibido: separadores raros (`04 - x`, `4-x`), doble extensión (`x.mp4.mp4`),
  números de un dígito. Usa dos dígitos + `_`.

Regla práctica: el `slot` del manifest (`04a`) = prefijo del archivo (`04a_...`). Para
promover un candidato de `_candidates/`, muévelo a `assets/` con el nombre del slot.

## Marcadores de timing `<<slot>>` (para que la imagen salga cuando la voz la menciona)

Dentro del `[AUDIO]` del guion se marcan los cortes:
`[AUDIO] <<04a | Google campus | google campus>> Rewind to 2005... <<04b | Andy Rubin | startup office>> A startup called Android...`

El marcador se quita antes del TTS. Tras `tts`, corre `align` para que cada `<<slot>>`
se convierta en `start`/`duration` exactos en el manifest. El assembler coloca cada
asset en su segundo con corte preciso. Los timestamps salen de `audio/NN_audio.json`
(si no existe y hay whisper local, `align` lo genera).

**4to campo opcional = fuente (ADR-021):** `<<slot | desc | búsqueda | fuente>>`, con
`fuente` = `pexels` (default, no lo escribas si no aplica) o `wikimedia` — úsalo SOLO
cuando el shot pide a una persona real identificable que Pexels no puede dar (su
política no vende fotos editoriales de gente famosa). Ejemplo:
`<<02a | Bill Gates joven | Bill Gates | wikimedia>>`. Con `fetch --auto`
ese shot va a Wikimedia Commons en vez de Pexels; si Commons no tiene nada útil, cae
solo a Pexels.

**5to campo opcional = ÉPOCA:** `<<slot | desc | sujeto | wikimedia | 1990-2005>>`.
Acepta rango (`1990-1999`), año suelto (`1994`), `-1999` (hasta) o `2015-` (desde). Solo
lo usa wikimedia, y resuelve dos cosas: que dos shots del mismo sujeto no traigan la
MISMA foto, y que cada uno sea de la década que pide el guion. Si no hay material de esa
época avisa en consola y usa el mejor disponible (material libre viejo escasea).

**Para wikimedia, la query es un NOMBRE DE CATEGORÍA de Commons, no una búsqueda.**
El cliente consulta `Category:<query>` — una lista curada por humanos, donde todo lo que
hay dentro está verificado como del sujeto correcto. Escribe el nombre canónico del sujeto
y nada más: `Bill Gates`, `Steve Ballmer`, `Nokia mobile phones`, `HTC Dream`. NO escribas
descripciones (`Bill Gates joven oficina Microsoft años 90`) ni le agregues años a menos
que sepas que la categoría existe; el cliente recorta términos por el final si la
categoría completa no existe.

Si no hay categoría, cae a búsqueda de texto y lo avisa con `[OJO]` en consola. Ese modo
es una apuesta de relevancia — llegó a traer una foto de una **ardilla** en el "Mary Gates
Hall" cuando se le pidió Bill Gates. Si ves ese aviso, verifica la imagen resultante.
Detalle completo en ADR-021.

## Overlays de texto encima `{{ ... }}` (ADR-019)

Para texto ENCIMA del visual (stats, nombres, citas), dentro del `[AUDIO]`:
`{{ tipo | contenido | duracion | estilo }}` — ej. `{{text | $400.000.000.000 | 4s | stat}}`.
Estilos: `stat`, `lower_third`, `quote`, `label`. Se sincronizan con `align` (entran
cuando la voz lo dice) y **no necesitan archivos** (son texto puro). Un overlay no se
reparte como los shots: entra en su segundo y dura lo que diga el marcador. Reportados
por `status`.

## Música de fondo (opcional)

Pon un `music.mp3` en la carpeta del proyecto (`videos/<PROYECTO>/`). Si no está, el
video sale sin música (aparece como `warning`, no bloquea).

## Guardrails (no rompas esto)

- **No regeneres audios sin razón:** `tts --overwrite` re-gasta API. Solo regenera la
  escena que cambió (`tts --scenes N --overwrite`).
- **Si cambias la velocidad de voz o el guion, re-corre `align`:** cambian las
  duraciones y el timing de los shots.
- **No inventes nombres de archivo:** sigue el canon; si `status` marca un `warning` de
  nombre, renómbralo como dice `suggest`.
- **No corras `assemble` con `blockers` pendientes.** Resuélvelos primero (mira `needs`
  por escena).
- **`fetch --auto` es el flujo por defecto; no te frenes a "curar" cada asset.** Corre
  `preview` y deja que el humano revise la cuadrícula (ADR-021/022). Si un asset no
  sirve, `fetch --auto --scenes N --force` sobre esa escena — no hace falta pedir
  permiso imagen por imagen.
- **Corre `preview` ANTES del `tts`.** Revisar los visuales no cuesta nada; regenerar
  voces sí. Si hay que cambiar assets, mejor descubrirlo antes de gastar API.
- **Un video mas corto que su narración se repite en BUCLE.** Para gráficos o
  animaciones que culminan en algo (un contador, una línea que se dibuja) eso los
  reinicia a media frase: nómbralos con `_freeze` o `_nograde` y el pipeline congela su
  último frame en vez de repetirlos (ADR-022). Los renders de Manim ya usan `_nograde`.
- **Wikimedia exige atribución en la mayoría de sus archivos** (a diferencia de Pexels).
  Revisa `assets/CREDITS.txt` antes de dar el video por terminado; si hay filas con
  fuente `wikimedia`, avisa que hace falta crédito en la descripción.

## Dónde vive cada cosa

```
channels/the_corporate_code/
  guiones/<guion>.md              # fuente de verdad (con [VISUAL]/[AUDIO]/<<slot>>)
  videos/<PROYECTO>/
    assets/                       # assets nombrados (NN_ / NNa_) + CREDITS.txt
    assets/_candidates/           # staging de 'fetch' SIN --auto (no se usa para render)
    audio/                        # voces (NN_audio.mp3) + timestamps (NN_audio.json)
    manifest.json                 # el plan (regenerable)
    music.mp3                     # opcional
    output/final.mp4              # render final
engine/scripts/                   # el motor (no hardcodear nada de un canal aquí)
ADR.md                            # por qué de cada decisión de arquitectura
```

Cuando dudes, corre `status --json`, lee `blockers`/`warnings`, y actúa sobre eso.

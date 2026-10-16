# PUBLICACION.md — de la salida del render a YouTube

El pipeline entrega `output/final.mp4` y `subtitulos.srt`. Este documento cubre todo lo
que viene después, que es aproximadamente la mitad del trabajo y donde están los errores
más caros: los que no dan error, se publican, y solo se ven en las métricas tres semanas
más tarde.

Casi todo lo de aquí está **medido**, no opinado. Cuando algo es criterio y no medición,
lo dice.

---

## 1. Miniatura

### La prueba que manda

**Reduce la miniatura a 120 px de ancho y mírala.** Si a ese tamaño no distingues el
sujeto o no lees el texto, no sirve — por buena que se vea en grande. Es la prueba que
descarta más miniaturas.

Tamaños reales de consumo: **168x94 en móvil** (donde está la mayoría), ~246 px en la
parrilla de escritorio. A 1280x720 solo la ves tú.

### Especificaciones duras

| Qué | Valor |
|---|---|
| Resolución | 1280x720 |
| Relación de aspecto | 16:9 **exacto** (1.7778) |
| Peso máximo | **2048 KB** — pasarlo = subida rechazada |
| Tipografía | Una sola familia, bold sans-serif, mínimo 60-80pt sobre el lienzo de 1280 |
| Palabras de texto | Dos a cuatro. Nunca una frase |
| Espacio negativo | 30-40% del cuadro |
| Contraste texto/fondo | Mínimo 4.5:1 |

### El problema del negro contra el modo oscuro

Está documentado que **los fondos blancos bajan el CTR alrededor de un 28% porque se
funden con el modo claro de YouTube**. El principio detrás es que el contraste tiene que
funcionar *contra la interfaz*, no solo dentro de la imagen.

Eso nos aplica al revés. El fondo del modo oscuro de YouTube es **#0f0f0f** y el
`TCC_BG` de marca es **#131313**. Prácticamente el mismo negro.

Medición sobre las dos miniaturas candidatas del segundo video de TCC (luminancia de los
bordes, fondo de YouTube = 15):

```
Miniatura con negro plano:     arriba 11,5  abajo 17,8  izq 12,8  der 16,3  -> SE FUNDE
Miniatura con luz en un borde: arriba 30,0  abajo 31,5  izq  6,3  der 131,9 -> tiene borde
```

La primera no tiene frontera: el espectador no ve una miniatura, ve texto flotando sin
forma. La segunda existe como objeto porque el panel de luz roja del borde derecho le da
un ancla.

**Regla: negro con luz, no negro plano.** Siempre una fuente de luz dentro del cuadro
que genere degradado y llegue a algún borde. No hay que abandonar la paleta, hay que
iluminarla.

*(Lo del 28% en modo claro está documentado; el caso espejo en modo oscuro es inferencia
nuestra por simetría, respaldada por nuestra propia medición. No encontramos un estudio
del caso oscuro.)*

### Generación con IA: el prompt tiene que ser determinista

Gemini Flow (y cualquier generador) devuelve con buena fidelidad **lo que le pidas — y
solo lo que le pidas.** Lo que no fijes, lo decide él. Nos devolvió 2752x1536 (1.79:1)
porque no fijamos la relación de aspecto, y hubo que recortar.

**Fija siempre y de forma explícita:**

- Relación de aspecto y resolución
- Los colores en hexadecimal (`#131313`, `#A41F29`), no por nombre
- De dónde viene la luz y hacia dónde cae el degradado
- Dónde queda el espacio vacío (para que el texto tenga sitio)
- Profundidad de campo, tipo de plano, mood

**Y nunca le pidas que escriba texto ni cifras.** Los modelos de imagen todavía fallan
con números largos y con tipografía. Pide `no text` y compón el texto encima en edición.
Siempre.

Ejemplo de prompt que funcionó (el chip del segundo video de TCC):

```
Cinematic product photography, 1280x720, deep black background with a strong warm red
light source coming from the right side creating a visible gradient and glow across the
frame, a small dark matte four-pointed star-shaped object on the left in cold grey,
unlit and matte, and on the right a large glowing silicon chip radiating red light,
shallow depth of field, dramatic single-source lighting, extreme contrast, no text,
no logos, generous empty space in the upper left, ultra clean minimal composition
```

### Caras en la miniatura

No existe strike por usar la cara de una figura pública en contexto informativo. El
riesgo no es la cara: **es la fotografía**, cuyo copyright es del fotógrafo. Y no llega
como strike ni por Content ID (que solo escanea audio y video, no miniaturas) sino como
reclamación manual, que es poco frecuente y se resuelve cambiando la imagen.

Dicho eso: `EDITORIAL.md` advierte que **el uso legítimo es más débil en la miniatura
que dentro del video**, porque ahí la imagen circula suelta, separada del comentario que
la justifica. Así que para miniaturas, material CC o dominio público. Los assets del
propio proyecto ya declarados en `CREDITS.txt` son la primera cantera a revisar.

---

## 2. Título

### El criterio

Un título tiene dos trabajos que no son el mismo: que te **encuentren** (búsqueda) y que
el video **salga a buscar gente** (recomendación). El segundo pesa más en un canal que
vive de exploración — mira `channels/<canal>/CRITERIO_*.md` para saber de cuál vive este.

La fórmula que usamos: **montar la frase de alto volumen que ya usa la prensa del nicho,
y subvertirla.** Ahí la keyword entra sola y el hueco de curiosidad se abre sin inventar
nada.

Ejemplo real. La prensa titulaba "Why Google fell behind in the AI race" (NPR), "Google's
Gemini delay widens AI race" (Axios), "Google DeepMind is losing its grip on elite AI
talent" (Fortune). El título que salió: **`Google Is Losing the AI Race — On Purpose`**.
41 caracteres, no se trunca, pesca la búsqueda, y "On Purpose" hace el resto.

### La trampa: no prometas un keyword que el guion no entrega

El término con más tráfico del nicho era **Nvidia** — "Google TPU vs Nvidia", "AI chip
war", estaba en todos los medios. Contamos las menciones en el guion: **cero**.

Ponerlo habría sido ganar el clic y perder el algoritmo: el espectador llega, no
encuentra lo prometido, se va a los 40 segundos, y YouTube lee esa retención como "este
video no cumple" y deja de mostrarlo.

**Antes de fijar un título, cuenta las menciones del keyword en la narración.** Es un
grep. Si es cero, fuera.

### Lo demás

- **41-55 caracteres** es la zona segura. Más de ~60 se trunca en móvil.
- El sujeto de la frase importa: si la tesis es que **la empresa** decidió algo, el
  sujeto es la empresa. Poner el producto de sujeto ("Gemini is losing… on purpose") le
  atribuye intención a una cosa y rompe el argumento.
- Front-load: las keywords en las primeras palabras.

---

## 3. Descripción

Solo se ven **las dos o tres primeras líneas** antes del "mostrar más". Ahí van el
gancho y las keywords. El resto trabaja para el indexador.

Estructura que usamos:

1. **Dos o tres líneas de gancho** con las keywords principales metidas de forma
   natural. Datos concretos, no promesas.
2. **Una línea de tesis** — la frase que resume el video.
3. **Tres o cuatro párrafos de resumen** donde entran los nombres propios. Los nombres
   son búsquedas de cola larga: poco tráfico cada uno, pero muy cualificado.
4. **CHAPTERS** — el bloque de capítulos (ver abajo).
5. **SOURCES** — de dónde sale cada cifra. Casi nadie en el nicho las publica y al tipo
   de espectador de un canal de análisis eso le importa. Es diferenciación gratis.
6. **Hashtags** al final, entre 8 y 10.

---

## 4. Capítulos de YouTube

### Requisitos

- La primera marca tiene que ser **exactamente `0:00`**
- Mínimo **3 marcas**
- Cada capítulo, mínimo **10 segundos**
- Una por línea, formato `M:SS Título`

### De dónde salen los tiempos (sin inventarlos)

El inicio de cada escena en el video final es la **suma acumulada**: escena narrada suma
`audio_duration`, title card suma `TITLE_CARD_DURATION`. Es exactamente lo que hace
`_inicio_de_escena()` en `assembler.py`, así que usa esa lógica y no otra.

```python
import json, sys; sys.path.insert(0,'engine/scripts'); import config
m = json.load(open('channels/<canal>/videos/<proyecto>/manifest.json', encoding='utf-8'))
t = 0.0
for sc in m['scenes']:
    print(f"{int(t)//60}:{int(t)%60:02d}  escena {sc['index']:02d}")
    t += config.TITLE_CARD_DURATION if sc['type']=='title_card' else float(sc.get('audio_duration') or 0)
```

**Contrasta siempre contra el `.srt`.** El último subtítulo debe terminar en el total
menos la duración de la title card final (que no lleva subtítulo). Si no cuadra, algo se
descuadró y los capítulos estarían mal.

**Los tiempos quedan congelados con ese audio.** Si cambias una escena de narración y
regeneras su `tts`, todo lo posterior se corre y hay que recalcular la lista.

### Cuántos y cómo se titulan

Uno por bloque narrativo, no uno por escena. Para un video de 8-9 minutos, entre 8 y 10.
Los títulos salen de frases que **están literalmente en la narración**, para que el
capítulo prometa exactamente lo que suena.

---

## 5. Tarjetas (cards)

Sirven para enlazar a otro video **en el momento exacto en que la narración lo menciona**.
Hasta **5 por video**. El teaser aparece unos segundos y luego se repliega en la ⓘ de la
esquina superior derecha.

**Ruta:** Studio → Contenido → clic en el video → Editor → Tarjetas de información →
Video → ajustar el tiempo de inicio → Guardar.

**El detalle que importa: adelanta la tarjeta entre 1 y 2 segundos respecto a la mención.**
Si la mención suena en 6:37.5, la tarjeta va en **6:36**. Puesta en el segundo exacto
llega tarde: aparece cuando la frase ya pasó.

El segundo de la mención se saca del manifest alineado, no a oído.

**Y pon la tarjeta de vuelta.** El video viejo apuntando al nuevo hace circular el
tráfico que ya tiene. Con pocos videos en el canal es de lo poco gratis que hay.

---

## 6. Pantalla final (end screen)

- Van en los **últimos 5 a 20 segundos**
- El video debe durar al menos 25 segundos
- Hasta **4 elementos** en 16:9
- No se muestran en la web móvil (sí en la app)

### El conflicto con nuestra title card de cierre

`TITLE_CARD_DURATION` está en **3,5 segundos** y es **global**: aplica igual a la title
card de apertura que a la de cierre. Pero la pantalla final exige **5 segundos mínimo**,
así que la tarjeta de "Subscribe" no da y la pantalla final tiene que arrancar antes,
pisando el último segundo de narración.

Funciona, pero va justo. **Pendiente en `MEJORAS.md`: separar la duración de la title
card de cierre a 8-10 segundos.** Hasta que eso esté, la pantalla final se coloca a mano
5 segundos antes del final y se acepta el solape.

---

## 7. Shorts

La estrategia está decidida (shorts para suscriptores y para testear temas, no para
horas de reproducción — los umbrales de monetización no son combinables y la aritmética
del camino largo es dos órdenes de magnitud más alcanzable).

El concepto, el enfoque y la parte técnica quedan pendientes de **ADR-051**, que se
escribe cuando hayamos producido los primeros. Mientras tanto, lo único que ya es regla
está en `AGENT.md`: **cuántos shorts salen de un video lo decide el contenido, no una
cuota.**

---

## 8. Checklist antes de darle a publicar

- [ ] Miniatura vista a 120 px y legible
- [ ] Miniatura en 1280x720, 16:9 exacto, por debajo de 2048 KB
- [ ] Miniatura con un borde visible contra `#0f0f0f`
- [ ] Título: keyword contado en la narración (grep), menos de 60 caracteres
- [ ] Descripción: gancho y keywords en las dos primeras líneas
- [ ] Capítulos: primera marca en `0:00`, contrastados contra el `.srt`
- [ ] `.srt` subido como pista de subtítulos aparte
- [ ] Tarjeta puesta 1-2 segundos antes de la mención
- [ ] Tarjeta de vuelta en el video enlazado
- [ ] Pantalla final colocada
- [ ] `ESTADO_<CANAL>.md` actualizado con lo que se publicó

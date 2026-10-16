# CANAL_NUEVO.md — configurar un canal, una vez

Este documento es para el agente que arranca un **canal nuevo**. Si vienes a hacer otro
video de un canal que ya existe, no es aquí: es `AGENT.md`.

**La promesa:** un canal se configura una sola vez. Cuando termines esta lista, todos
los videos siguientes son solo investigación, guion, adaptación y fuera. Nadie vuelve a
tocar nada de aquí salvo que cambie la identidad del canal.

---

## Lo que se congela y lo que tiene que variar

Esta distinción es el corazón del asunto, y conviene tenerla clara antes de configurar
nada.

**Se congela la identidad técnica:** voz, paleta, tipografía, grade, mastering, política
de licencias, criterio visual. Eso se decide una vez y después es infraestructura. Que
dos videos del mismo canal suenen y se vean igual no es repetición, es marca.

**Tiene que variar todo lo demás:** la estructura narrativa, el orden de las escenas, el
tipo de gancho, el ángulo del empaquetado. **No hagas una plantilla de guion.** Un canal
donde todos los videos abren igual, desarrollan igual y cierran igual es exactamente lo
que la plataforma está castigando hoy. La regla es que haya **reglas dentro de las que
se varía**, no un molde del que se saca copias.

Dicho de otra forma: se congela **cómo suena y cómo se ve** el canal. Nunca **cómo se
cuenta** cada historia.

---

## La frontera entre el motor y el canal

El motor es uno y lo comparten todos los canales. Lo que cambia por canal sale de
`channels/<canal>/canal.json`. Pero hay tres niveles ahí dentro y confundirlos cuesta
caro.

### Nivel 1 — Las 16 claves que el MOTOR lee de verdad

Estas las lee `aplicar_canal()` en `engine/scripts/config.py`. Si cambias una, cambia el
render. Es la lista real, extraída del código:

| Clave en `canal.json` | Variable del motor | Qué controla |
|---|---|---|
| `voz.modelo` | `TTS_MODEL` | Modelo de TTS |
| `voz.nombre` | `TTS_VOICE` | La voz |
| `voz.velocidad` | `TTS_SPEED` | Velocidad de la narración |
| `voz.instrucciones` | `TTS_INSTRUCTIONS` | Instrucciones de tono (si el modelo las admite) |
| `idioma.wikidata` | `WIKIDATA_LANG` | Idioma de las consultas a Wikidata |
| `marca.fondo` | `BRAND_BG_COLOR` | Fondo de title cards |
| `marca.acento` | `OVERLAY_ACCENT_COLOR` | Acento de los overlays |
| `marca.texto_principal` | `TITLE_CARD_TEXT_COLOR` | Color del texto de title cards |
| `tipografia.principal` | `TITLE_CARD_FONT` | Tipografía de title cards y créditos |
| `grade.tinte` | `GRADE_TINT_COLOR` | Color del grade |
| `grade.fuerza` | `GRADE_TINT` | Intensidad del grade |
| `master.dos_pasadas` | `MASTER_DOS_PASADAS` | Normalización en dos pasadas |
| `master.objetivo_lufs` | `MASTER_TARGET_LUFS` | Loudness objetivo |
| `musica.cama` | `MUSIC_FILENAME` | Nombre del archivo de cama musical |
| `musica.cierre` | `MUSIC_FINAL_FILENAME` | Nombre de la pista de cierre |
| `musica.cierre_desde_escena` | `MUSIC_FINAL_FROM_SCENE` | Desde qué escena entra el cierre |

Todo lo demás del motor —duración de title cards, fades, resolución, fps, umbrales de
Wikimedia, volumen de música— **es estático y compartido**. Si necesitas cambiarlo,
no es configuración de canal: es una mejora del motor, y va por ADR.

### Nivel 2 — Claves que solo leen los scripts DEL PROPIO canal

`title_card_final`, `marca.acento_grafico`, `marca.texto_secundario`. El motor las
ignora. Las consumen los scripts que vive dentro de la carpeta del canal: su tema de
Manim, su generador de miniaturas.

**Este nivel es el que hace que la promesa de "configurar una vez" funcione**, y hay que
montarlo bien. Ver la sección siguiente.

### Nivel 3 — La trampa: claves que NADIE lee

**`fuentes_de_assets`** (con sus `wikimedia`, `pexels`, `propia`, `ia`) **no la lee
ningún script del repo.** Verificado por grep en todo el proyecto.

Es declarativa: documenta la intención, no configura nada. El ruteo real de cada plano
lo decide el **cuarto campo del marcador en el guion** (`| wikimedia`, `| propia`), no
este archivo.

Importa porque es engañoso en las dos direcciones: alguien puede poner `"ia": true`
esperando que se active la generación con IA y no pasará nada, y alguien puede leer
`"ia": false` y creer que el motor lo está bloqueando cuando en realidad nunca hubo tal
bloqueo. Si declaras estas claves, que sea sabiendo que son una nota para humanos.

---

## El patrón correcto: que los scripts del canal lean `canal.json`

Aquí los dos canales existentes hacen cosas distintas, y **uno de los dos está mal**.

**Sabermetría Hípica lo hace bien.** Su `manim/sh_tema.py` abre `canal.json` y saca los
colores de ahí:

```python
_CANAL_JSON = Path(__file__).resolve().parent.parent / "canal.json"
MUTED = _marca.get("texto_secundario", "#888888")
ACENTO_SUAVE = _marca.get("acento_grafico", "#F7A1A3")
```

Una sola fuente de verdad. Cambias `canal.json` y cambia todo: title cards, overlays,
gráficos de Manim y miniaturas.

**The Corporate Code lo hace mal.** Su `manim/tcc_theme.py` tiene los colores escritos a
mano:

```python
TCC_BG = "#131313"      # Fondo (casi negro), del branding.
TCC_GRAY = "#8A8A8A"    # Texto secundario / ejes.
```

Y esto **ya divergió**: `canal.json` declara `marca.texto_secundario: "#BBBBBB"` y el
tema de Manim usa `#8A8A8A`. Son dos grises distintos para lo mismo según si el texto
sale de una title card o de un gráfico. Nadie lo decidió: se escribió dos veces y se
separó.

**Para un canal nuevo: los scripts del canal leen `canal.json`, siempre.** Copia el
patrón de `sh_tema.py`, no el de `tcc_theme.py`.

---

## Estructura de carpetas

```
channels/<canal>/
├── canal.json              # identidad técnica (lo de arriba)
├── ESTADO_<X>.md           # estado vivo del canal
├── CRITERIO_<X>.md         # criterio propio: audiencia, visual, empaquetado
├── branding/               # logo, banner, fuentes propias si hay
├── guiones/                # solo los guiones MARCADOS (el plano se mueve a _to_delete/)
├── manim/                  # <x>_tema.py (leyendo canal.json) + componentes
├── miniaturas/             # generador de miniaturas, si el canal lo tiene
├── videos/                 # un directorio por video, lo crea 'parse'
├── regresion/              # la escena congelada del canal
├── pruebas_voz/            # comparativas de voz antes de decidir
└── pruebas_musica/         # comparativas de música
```

Las tres últimas no son opcionales por capricho: son donde se toman las decisiones del
Nivel 1 **con el oído y el ojo**, no leyendo un JSON.

---

## Las decisiones que hay que tomar una vez

### Voz

Corre `probar_voces.py` y escucha. Se decide modelo, nombre y velocidad, y se anota en
`canal.json`. Mide el **ritmo real en palabras por minuto** sobre una escena generada:
lo vas a necesitar en cada video para estimar duración desde el conteo de palabras del
guion. *(TCC con onyx a 1.0 va a 162 ppm.)*

**Ojo con el idioma:** hay un bug documentado de degradación del TTS en español con
bloques largos (trampa 1 de `AGENT.md`). Si el canal es en español, eso cambia cómo se
parten las escenas.

### Paleta y tipografía

Del branding real, no inventada. Van a `canal.json` y de ahí las leen tanto el motor
como los scripts del canal.

**Dos advertencias que ya costaron:**

La tipografía se declara con ruta absoluta y hoy los canales existentes apuntan a
`C:\Windows\Fonts\`. Eso ata `assemble` a una máquina Windows. Si quieres que el render
sea reproducible en cualquier sitio, mete la fuente en `branding/` y apunta ahí — con la
salvedad de licencia si la fuente es propietaria.

Y si el fondo del canal es un negro casi puro, **cuidado con las miniaturas**: el modo
oscuro de YouTube es `#0f0f0f` y un fondo cercano se disuelve en la página. Está medido
en `PUBLICACION.md`.

### Música

Se decide la política, no solo el archivo: de dónde sale (biblioteca de YouTube, IA,
banco de pago), si se reusa la misma cama entre videos, y si hay pista de cierre.
Reusar la cama es política válida y ahorra la tarea que más tiempo come sin mover la
aguja.

### Política de licencias

Se decide el nivel de rigor antes del primer video, no en medio del tercero. Qué
licencias se admiten, cómo se declaran los logos, si se invoca uso legítimo y en qué
condiciones. `EDITORIAL.md` y `LICENCIAS.md` son transversales; lo que el canal decide
es dónde se pone su umbral.

### Criterio visual

Qué tipo de imagen sostiene este canal: ¿gráficos de datos, archivo fotográfico,
B-roll atmosférico? Va a `CRITERIO_<X>.md`. Hípica tiene una sección entera sobre qué
sube la retención en un gráfico, que es exactamente el tipo de cosa que va aquí.

### Perfil de audiencia — esta se llena DESPUÉS

No se puede decidir de antemano: sale de los datos. Después del primer o segundo video,
abre Studio y mira el reparto **sugeridos vs búsqueda**, con su CTR y su duración
promedio.

Ese reparto decide cómo se empaqueta todo lo demás, y **cambia por canal**: un canal de
análisis vive de recomendación, un canal sobre nombres concretos que la gente teclea
vive de búsqueda. Empaquetar uno con el criterio del otro es caro. Cuando tengas el
dato, escríbelo en `CRITERIO_<X>.md` con sus números y con la cautela estadística que
corresponda (por debajo de unos miles de impresiones, el CTR no concluye nada).

---

## Congelar la regresión

Cuando el canal publique su primer video, **congela una escena conocida** en
`regresion/`. A partir de ahí, `python engine/scripts/regresion.py <CANAL>` es el paso
cero de cada producción.

Existe porque el motor es compartido: un arreglo hecho para otro canal llega al tuyo sin
que nadie lo pida. Verde significa que el motor produce lo mismo. Rojo significa que
algo cambió, y hay que entender si es una mejora que quieres antes de montar. Ver `PASO
CERO` en `AGENT.md`.

---

## Checklist de canal configurado

- [ ] `canal.json` con las 16 claves del Nivel 1 decididas a conciencia
- [ ] Voz elegida escuchando, no leyendo, y ritmo en ppm medido y anotado
- [ ] Paleta y tipografía del branding real
- [ ] Tipografía: decidido si se acepta la atadura a Windows o se mete en `branding/`
- [ ] Miniatura: comprobado que el fondo del canal no se funde con `#0f0f0f`
- [ ] Política de música decidida (origen, reuso, pista de cierre)
- [ ] Umbral de licencias decidido
- [ ] `<x>_tema.py` **leyendo `canal.json`**, no con los colores a mano
- [ ] `CRITERIO_<X>.md` creado (perfil de audiencia pendiente hasta tener datos)
- [ ] `ESTADO_<X>.md` creado
- [ ] Estructura de carpetas completa
- [ ] Primer video publicado y escena de regresión congelada
- [ ] `CRITERIO_<X>.md` completado con el perfil de audiencia real

Cuando esto esté, el canal está configurado. **No vuelvas aquí.**

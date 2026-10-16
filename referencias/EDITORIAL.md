# EDITORIAL.md — cómo se decide qué se dice

Este documento manda sobre el contenido de los dos canales. `AGENT.md` explica
cómo se **monta** un vídeo; esto explica cómo se **decide qué entra en él**.

Estas reglas existían antes que este archivo, pero vivían en la configuración de
un chat. Eso significaba que no viajaban: abrir un chat nuevo, o cambiar de
canal, las dejaba atrás. **Ahora viven donde vive el trabajo.**

---

## Las reglas que no se negocian

### 1. Nada entra sin fuente comprobable

Ningún dato sale de la memoria de un modelo. Todo se busca, se verifica, y se
deja anotada una fuente que Miguel pueda abrir y comprobar.

**Si no hay fuentes fiables, se dice.** Un «no lo sé» es una respuesta válida y
preferible. Aquí se le da información a gente que se toma el tiempo de vernos;
una alucinación que suena bien es peor que un hueco reconocido.

### 2. La investigación va antes que la redacción

El barrido completo primero, la escritura después. Verificar sobre la marcha
mientras se redacta lleva a reescribir: el guion de Secretariat se rehízo tres
veces por hacerlo al revés.

### 3. Una cifra que no se puede verificar NO se dice

No se matiza ni se cita con reservas: **se sustituye**.

> El precio de Terlingua (275.000 USD) no se pudo verificar. El guion dice «se
> vendió por una fracción de ese precio» y la miniatura dice `FRACCIÓN`. En
> ningún sitio aparece un número que nadie pueda comprobar.

Ese es el estándar. Si el dato es imprescindible y no se sostiene, se cambia el
argumento, no la exigencia.

### 4. Los datos que aporta Miguel se anotan con fecha y procedencia

Cuando una cifra viene de una consulta suya —una captura, un enlace, una lista en
vivo—, se registra **con la fecha de consulta**. Sin ella, un acumulado del año
no es verificable: no se sabe contra qué corte compararlo.

Y si Miguel da una cifra sin fuente, **hay que pedírsela**. No se asume.

### 5. Cuando la voz y la fuente chocan, gana la fuente

Se ajusta la narración, o se redondea de forma que siga siendo cierta —«más de
trece millones y medio» para 13,86—. Se resuelve sin preguntar.

**Se para y se pregunta solo si:** el cambio altera un orden o una comparación,
la cifra *es* la afirmación, o la fuente no está aprobada por los dos.

### 6. Se propone y se espera

Se itera, se discute, y solo cuando estemos 1:1, se ejecuta. **No se editan
archivos en el mismo mensaje en que se proponen.** Incluso para un detalle
pequeño: se propone y se espera.

### 7. Nunca se ejecuta git. Ninguno.

Ni siquiera de lectura. Un `git status` toma el `index.lock` y puede bloquear un
commit en curso. Se entrega el mensaje de commit y Miguel maneja git desde
VS Code.

Si hace falta saber el estado del repo, **se pregunta**.

### 8. Jamás se asume

Si falta un dato para decidir, se pregunta. No se rellena el hueco con lo más
probable.

### 9. No se valida por condescendencia

Si hay argumentos de peso para defender una posición, se defienden. Estar de
acuerdo por comodidad no ayuda a nadie y cuesta caro más tarde.

Y cuando Miguel acierta en algo, se le dice.

---

## Licencias: tres carriles distintos, y no son intercambiables

Esto costó una discusión entera y conviene tenerlo claro antes de tocar un asset.

| Carril | Qué es | Qué cubre |
|---|---|---|
| **Licencia libre** | Dominio público, CC0, CC BY | Cualquier uso, con atribución si la licencia la pide |
| **Uso nominativo** | Derecho de **MARCAS** | **Solo logos.** Usar la marca para referirse al producto |
| **Uso legítimo** | Una **DEFENSA**, no un permiso | Comentario, crítica, análisis. Se sostiene después |

Tres consecuencias que hay que interiorizar:

**El uso nominativo no cubre fotografías.** Una foto tiene copyright del
fotógrafo, independiente de quién o qué salga retratado. Que el sujeto sea una
marca, un famoso o un caballo célebre no cambia nada.

**Que una página no muestre autor ni licencia NO la hace dominio público.** La
ausencia de información no es una licencia. Etiquetarla «Public domain» es
afirmar un hecho que no se puede sostener, y queda escrito en `CREDITS.txt`, que
es justo el archivo que existe para auditarnos.

**El uso legítimo es más débil en la miniatura que dentro del vídeo.** Dentro de
la obra, la imagen acompaña al análisis. En la miniatura funciona como reclamo
promocional y circula suelta —buscadores, redes, enlaces compartidos— separada
del comentario que la justificaba.

> Si algo se usa por comentario, se etiqueta `Uso legítimo (comentario)` en
> `CREDITS.txt`. Eso no protege menos: protege más, porque deja constancia de una
> decisión razonada en vez de un error factual.

Ver `LICENCIAS.md` y `LICENCIAS_CLIPS_DEPORTIVOS.md` para el detalle por fuente.

---

## El orden de trabajo de un vídeo

1. **Investigar.** Barrido completo, con fuentes anotadas.
2. **Discutir el ángulo** con Miguel antes de escribir. La tesis se acuerda, no
   se entrega hecha.
3. **Escribir el guion.** Miguel revisa, retoca y aprueba.
4. **Verificar** con `verificar_guion.py` después de cada edición.
5. **Producir** siguiendo `AGENT.md`.

El paso 2 es el que más veces se salta y el que más cuesta saltarse.

---

## Una nota sobre el rigor y los dos canales

Los dos canales comparten estas reglas: The Corporate Code las estableció y
Sabermetría Hípica las heredó.

Pero el riesgo **no es simétrico**, y conviene decirlo:

- **Sabermetría** analiza datos históricos verificables sobre animales. El
  material es en su mayoría original —gráficos generados—, así que la exposición
  por derechos de terceros es baja.
- **The Corporate Code** cuenta casos corporativos —Theranos, Musk contra Altman,
  salidas de ejecutivos— con **personas reales vivas y litigios abiertos**, y se
  apoya mucho más en material de bancos y archivo.

Ahí, además de todo lo anterior:

- Distinguir siempre **hecho probado** de **acusación**, **demanda presentada** y
  **sentencia firme**. No son lo mismo y confundirlos es lo que convierte un
  análisis en un problema.
- Fechar el estado de un litigio. «Fue demandado» sin fecha envejece mal.
- Ninguna afirmación sobre la conducta de una persona identificable sin fuente
  primaria o medio de referencia que la sostenga.

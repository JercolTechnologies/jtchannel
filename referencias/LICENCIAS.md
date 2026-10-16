# Cómo verificar la licencia de una imagen

Guía práctica para cuando subas una imagen propia desde el preview. El sistema
te obliga a declarar la licencia, pero **no puede comprobar que sea cierta**: un
archivo descargado a tu disco no lleva su licencia dentro. Esto es lo que tienes
que mirar tú, y dónde.

---

## La regla que resuelve el 95% de los casos

**La licencia válida es la que está escrita en la página que aloja el archivo
original.** No la que dice Google, no la que dice un blog que la reusó.

Y el dato más fiable de todos es **el enlace a creativecommons.org**. Si la
página enlaza a una URL de este tipo, esa es la declaración formal:

```
creativecommons.org/licenses/by/4.0/          → CC BY 4.0        ✅ SIRVE
creativecommons.org/publicdomain/zero/1.0/    → CC0             ✅ SIRVE
creativecommons.org/publicdomain/mark/1.0/    → Dominio público ✅ SIRVE

creativecommons.org/licenses/by-sa/4.0/       → CC BY-SA        ❌ NO
creativecommons.org/licenses/by-nc/4.0/       → CC BY-NC        ❌ NO
creativecommons.org/licenses/by-nd/4.0/       → CC BY-ND        ❌ NO
```

Lee el código entre `/licenses/` y la versión. Si lleva **sa**, **nc** o **nd**
en cualquier combinación, no sirve. Solo `by` a secas, o cualquier cosa bajo
`/publicdomain/`.

---

## Dónde mirar, sitio por sitio

### Wikimedia Commons

1. Abre la página del archivo (`commons.wikimedia.org/wiki/File:Loquesea.jpg`)
2. Baja hasta la sección **"Licensing"** / **"Licencia"**
3. Hay un **recuadro de color** con la licencia en grande

Ese recuadro es la declaración oficial. Ejemplos de lo que puedes ver:

| Lo que dice el recuadro | ¿Sirve? |
|---|---|
| "This file is made available under the Creative Commons CC0 1.0 Universal Public Domain Dedication" | ✅ CC0 |
| "This work is in the public domain..." | ✅ Public domain |
| "This file is licensed under the Creative Commons Attribution 3.0 Unported license" | ✅ CC BY 3.0 |
| "...Attribution-**ShareAlike** 4.0..." | ❌ |
| "This logo image consists only of simple geometric shapes or text" (**PD-textlogo**) | ✅ Public domain |

**Ojo con los archivos de doble licencia.** Algunos dicen "CC BY-SA 3.0 **or**
GFDL". Los dos son restrictivos: no sirve.

### Flickr

1. Abre la página de la foto
2. Mira **abajo a la derecha**, bajo la columna de información
3. Verás **"Some rights reserved"** con un enlace, o los iconos de CC

Haz clic en ese enlace: te lleva a creativecommons.org y ahí lees el código
exacto. Si dice **"All rights reserved"**, no sirve, aunque la hayas encontrado
con el filtro de Creative Commons.

Truco: en la búsqueda de Flickr puedes filtrar por licencia desde el desplegable
**"Any license"** → elige **"Commercial use allowed"** y **"Modifications
allowed"**. Eso ya descarta NC y ND, pero **no descarta ShareAlike**, así que
igual hay que mirar cada una.

### Openverse (openverse.org)

Es el más cómodo: cada resultado muestra **la licencia como etiqueta** debajo de
la imagen, y en la ficha del archivo tienes el texto de atribución ya redactado
para copiar. Puedes filtrar por licencia antes de buscar.

### Google Imágenes

**No te fíes.** Su filtro de Creative Commons infiere la licencia de los
metadatos de la página y **se equivoca con frecuencia** — aparecen imágenes con
copyright. Sirve para *encontrar*, nunca como prueba.

Úsalo así: encuentras algo → **haces clic para ir a la página original** → ahí
verificas de verdad. Si esa página no declara la licencia claramente, descártala.

### Cualquier otro sitio (debianart, blogs, wikis...)

Busca en el pie de página o en la ficha del archivo una frase con "License",
"Licencia", "Creative Commons" o un enlace a creativecommons.org.

**Si no encuentras una declaración explícita, no la uses.** La ausencia de aviso
NO significa que sea libre — por defecto, todo lo publicado tiene copyright.

---

## Casos especiales que te vas a encontrar

### Logos de empresas → usa `Logo (uso nominativo)`

Aquí hay que separar **dos ramas del derecho distintas**, porque se confunden
todo el tiempo:

| | **Uso nominativo** | **Fair use** |
|---|---|---|
| Rama | Marcas registradas | Derechos de autor |
| Permite | Usar un logo para *referirte* al producto | Usar una obra para comentarla |
| Previsibilidad | **Alta**: test de tres puntos | **Baja**: es una defensa, no un permiso |

**El uso nominativo permite usar un logo de marca** siempre que se cumplan tres
condiciones, y un canal que analiza empresas las cumple de sobra:

1. El producto no se puede identificar sin la marca
2. Se usa solo lo necesario
3. **No se sugiere patrocinio ni respaldo** de la empresa

Por eso el desplegable tiene la opción **`Logo (uso nominativo)`**. No es una
licencia de contenido: es dejar constancia de que ese archivo entra por la vía de
marcas. No lleva crédito quemado —el uso nominativo no exige atribución— pero
queda registrado en `CREDITS.txt` como vía distinta, para que la contabilidad sea
auditable en vez de disfrazarlo de dominio público.

**Cuándo preferir `PD-textlogo`:** si el logo está en Commons con esa marca,
úsala. Significa que además **no tiene copyright** (es demasiado simple para
alcanzar el umbral de originalidad), así que te ahorras hasta la discusión.

**Ojo con los logos elaborados.** Uno con degradados y efectos —el de Windows
Vista, por ejemplo— puede acumular **las dos capas**: marca *y* derecho de autor
sobre el diseño. Que no esté en Commons como PD-textlogo suele ser justo la
señal de eso. Sigue amparado por uso nominativo en contexto editorial, pero es un
caso menos limpio que un logotipo de texto.

### Esta vía es SOLO para logos

Una **fotografía** de una persona o un evento tiene **derecho de autor del
fotógrafo**, y el uso nominativo no la cubre: no estás usando una marca.
Dependerías de *fair use*, que es una defensa impredecible que se evalúa caso por
caso — y las agencias (Getty, Reuters, AP) persiguen esto activamente, es parte
de su negocio.

**Para fotos, sin excepciones: CC0, dominio público o CC BY.** Es lo que hace que
la declaración de derechos a la plataforma sea cierta.

### Sitios de iconos (dashboardicons, iconfinder, flaticon...)

**Trampa frecuente.** Estos sitios ponen "FREE" bien grande y a veces declaran una
licencia de software (Apache-2.0, MIT) sobre el repositorio. Pero esa licencia
cubre **su colección** —el trabajo de recopilar, convertir formatos, empaquetar—
**no los logos de terceros que hay dentro**. No pueden licenciarte el logo de
Microsoft porque no es suyo.

Caso comprobado: `dashboardicons.com` no muestra ninguna licencia en la página del
icono. En su repositorio pone Apache-2.0, y justo debajo:

> *"All product names, trademarks, and registered trademarks are the property of
> their respective owners."*

Lo dicen ellos mismos.

**Cómo usarlos bien:** sirven perfectamente como **fuente de logos**, siempre que
los declares con `Logo (uso nominativo)` — que es la vía correcta, porque lo que
te ampara no es la licencia del sitio sino el derecho de marcas.

Lo que **no** debes hacer es declararlos "dominio público" apoyándote en el
Apache-2.0 del repositorio: esa licencia no cubre el logo.

No te preocupes por el fondo: si el logo viene con fondo blanco, el pipeline lo
detecta y lo quita antes de integrarlo.

Y si el logo está en Commons como `PD-textlogo`, prefiérelo: ahí además sabes que
no tiene copyright, y te ahorras hasta la discusión.

### Obras del gobierno de EE.UU.

Todo lo producido por empleados federales estadounidenses en su trabajo es
**dominio público por ley** (17 U.S.C. § 105). NASA, Departamento de Defensa,
Congreso, archivos oficiales. Es una mina para material histórico.

En Commons lo verás como **PD-USGov**. Ojo: aplica al gobierno **federal**, no
siempre a los estatales, y no a otros países.

### Obras antiguas

Las obras suficientemente viejas están en dominio público por caducidad del
copyright. En Commons aparecen como **PD-old**. La fecha exacta varía por país,
pero Commons ya hace ese análisis por ti — si dice PD-old, fíate.

---

## Lo que acepta el desplegable del preview

Solo estas. Si lo que encontraste no está en la lista, no se puede usar:

| Opción | Qué significa | ¿Crédito quemado? |
|---|---|---|
| `Public domain` | Sin derechos | No |
| `CC0` | El autor renunció a todo | No |
| `PD-USGov` | Obra del gobierno de EE.UU. | No |
| `PD-textlogo` | Logo demasiado simple para tener copyright | No |
| `CC BY 2.0 / 3.0 / 4.0` | Solo pide atribución | **Sí, automático** |
| `Logo (uso nominativo)` | **Solo logos.** Vía de marcas, no licencia de contenido | No |
| `Uso legítimo (comentario)` | **No es una licencia: es una DEFENSA.** Para material sin licencia declarada que se usa para comentar, criticar o analizar | No |

Con `CC BY`, el pipeline **quema el crédito** en la esquina inferior de la
imagen. Va con el pixel, así que sobrevive aunque la plataforma redistribuya el
video — que es justo el escenario de Rumble.

---

## En una frase

**Para FOTOS: entra a la página del archivo original y busca la declaración de
licencia. Si lleva SA, NC o ND, descártala — eso no se negocia.**

**Si NO encuentras declaración**, tienes dos caminos y hay que elegir a conciencia:

- **Descártala**, que es el camino por defecto y el que debes tomar mientras estés
  consiguiendo material a granel. La ausencia de aviso no es una licencia.
- **O úsala declarando `Uso legítimo (comentario)`**, si y solo si esa imagen concreta
  ilustra algo que el video está comentando o analizando, y tú tomas la decisión
  sabiendo que invocas una defensa y no un permiso. Nunca la etiquetes «dominio
  público»: eso es afirmar un hecho que no puedes sostener, y queda escrito en
  `CREDITS.txt`, que es justo el archivo que existe para auditarnos.

Lo segundo es un override manual y consciente, no el flujo normal. Y `EDITORIAL.md`
advierte que **en la miniatura el uso legítimo es más débil que dentro del video**,
porque ahí la imagen circula suelta, separada del comentario que la justificaba. Para
miniaturas, CC o dominio público.

**Para LOGOS: usa `Logo (uso nominativo)` y sigue adelante.** Estás analizando
empresas, no vendiendo camisetas.

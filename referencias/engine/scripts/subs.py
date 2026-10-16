# -*- coding: utf-8 -*-
# Ruta: engine/scripts/subs.py
#
# GENERADOR DE SUBTITULOS .SRT (ADR-030).
#
# Adaptado del generar_srt.py del proyecto de sabermetria, del que se conserva la
# idea y el formateo de tiempos. Tres diferencias de fondo, por el formato:
#
#   1. UN SOLO archivo con la linea de tiempo del VIDEO COMPLETO, no uno por
#      escena empezando en 00:00. Eso obliga a acumular los offsets incluyendo
#      las TITLE CARDS, que duran lo suyo y no tienen audio: sin contarlas, todo
#      lo posterior a la primera tarjeta iria desfasado.
#
#   2. Bloques de 5-8 palabras en vez de 3. Tres palabras funcionan en un Short
#      vertical con texto grande saltando; en un documental horizontal son
#      subtitulos freneticos e ilegibles.
#
#   3. El texto sale del GUION, no de Whisper. Whisper transcribe y se equivoca
#      ("Egocio"); nosotros tenemos el texto exacto porque lo escribimos. Se usan
#      sus TIEMPOS y nuestro TEXTO, emparejados por posicion — la misma tecnica
#      que ya usa 'align' (ADR-018). Resultado: cero errores de transcripcion,
#      algo que ningun subtitulado automatico puede darte.

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

try:
    from . import config
    from .align import TimestampAligner
except ImportError:  # ejecucion directa
    import config
    from align import TimestampAligner


def _fmt(segundos: float) -> str:
    """Segundos -> 'HH:MM:SS,mmm', el formato que exige el SRT."""
    segundos = max(0.0, float(segundos))
    total = int(segundos)
    ms = int(round((segundos - total) * 1000))
    if ms == 1000:                       # redondeo al alza en el limite
        total, ms = total + 1, 0
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d},{ms:03d}"


def _tiempos_por_palabra(texto: str, words: list, duracion: float) -> list:
    """Empareja las palabras del GUION con los tiempos de Whisper.

    Devuelve una lista paralela a las palabras del guion con el segundo de cada
    una (relativo a su escena). Donde no hay coincidencia se estima por
    proporcion, igual que hace 'align'.
    """
    nuestras = texto.split()
    if not words:
        n = max(len(nuestras), 1)
        return [duracion * i / n for i in range(len(nuestras))]

    a = [TimestampAligner._norm(t) for t in nuestras]
    b = [TimestampAligner._norm(w["palabra"]) for w in words]
    inicios = [w.get("inicio") for w in words]

    o2w = {}
    for bloque in SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(bloque.size):
            o2w[bloque.a + k] = bloque.b + k

    fuera = []
    n = max(len(a), 1)
    for i in range(len(a)):
        t = None
        # Se busca la palabra emparejada mas cercana, hacia ambos lados.
        for d in range(len(a) or 1):
            for cand in (i + d, i - d):
                w = o2w.get(cand)
                if w is not None and 0 <= w < len(inicios) and inicios[w] is not None:
                    t = float(inicios[w])
                    break
            if t is not None:
                break
        fuera.append(t if t is not None else duracion * i / n)
    return fuera


def _bloques(nuestras: list, tiempos: list, duracion: float, offset: float,
             max_palabras: int, min_palabras: int, max_cars: int,
             min_seg: float, umbral_fusion: float = None) -> list:
    """Agrupa palabras en cues legibles y les asigna entrada y salida.

    Se corta por longitud y, preferentemente, en el signo de puntuacion mas
    cercano: un subtitulo que termina en coma o punto se lee mucho mejor que uno
    cortado a mitad de sintagma.

    LOS LIMITES LLEGAN COMO ARGUMENTOS Y NO SE LEEN DE config A PROPOSITO. El
    largo y el short necesitan numeros distintos (8 palabras es ilegible en
    vertical, 3 es frenetico en horizontal) y config.SUBS_* es una global del
    modulo: si el short la bajara, el siguiente largo de la misma corrida
    heredaria el ajuste sin pedirlo. Ver DEUDA_TECNICA.md.
    """
    FUERTE = (".", "?", "!", ":", ";")   # final de oracion: el mejor sitio para cortar
    DEBIL = (",", "—", "–")              # pausa: sirve si no hay final de oracion
    CIERRA_ORACION = (".", "?", "!")

    # El umbral de fusion NO es el mismo numero que la duracion minima, aunque
    # antes lo fuera. Fusionar todo lo que dure menos que el minimo de
    # exhibicion pega cues ENTEROS al anterior: medido en SHORT1 escena 3 con
    # 4 palabras por cue, "hundred fourteen billion dollars" se pegaba al cue
    # previo y salia un subtitulo de 8 palabras y tres lineas, que es lo que
    # tapaba el ultimo renglon del slam. Lo que se quiere fusionar es la
    # COLETILLA de una palabra, no un cue completo, asi que el umbral va mas
    # bajo y por separado.
    if umbral_fusion is None:
        umbral_fusion = min_seg

    cues, i = [], 0
    while i < len(nuestras):
        tope = min(i + max_palabras, len(nuestras))
        fin = tope
        # Se busca el corte MAS TARDIO posible dentro del bloque, no el primero:
        # cortar en la primera pausa deja cues cortisimos y entrecortados. Se
        # prefiere final de oracion; si no hay, una pausa; si tampoco, corte seco.
        for signos in (FUERTE, DEBIL):
            cand = [j for j in range(i + min_palabras, tope + 1)
                    if nuestras[j - 1].rstrip().endswith(signos)]
            if cand:
                fin = max(cand)
                break
        grupo = nuestras[i:fin]
        ini_t = tiempos[i]
        fin_t = tiempos[fin] if fin < len(tiempos) else duracion
        if fin_t - ini_t < min_seg:
            fin_t = min(ini_t + min_seg, duracion)
        cues.append((offset + ini_t, offset + fin_t, " ".join(grupo)))
        i = fin

    # Un cue de 0.3s es un parpadeo ilegible. Suele ser la coletilla final de una
    # escena ("career."), asi que se funde con el anterior en vez de dejarlo solo.
    fundidos = []
    for ini_t, fin_t, txt in cues:
        # No se fusiona a traves de un final de oracion: pegar el principio de
        # una frase al final de otra se lee peor que un cue corto.
        anterior_cierra = (fundidos
                           and fundidos[-1][2].rstrip().endswith(CIERRA_ORACION))
        if fundidos and not anterior_cierra and (fin_t - ini_t) < umbral_fusion:
            pi, _, ptxt = fundidos[-1]
            fundidos[-1] = (pi, fin_t, f"{ptxt} {txt}")
        else:
            fundidos.append((ini_t, fin_t, txt))
    return [(a, b, _dos_lineas(t, max_cars)) for a, b, t in fundidos]


def _dos_lineas(texto: str, max_cars: int) -> str:
    """Parte el cue en dos lineas equilibradas si excede el ancho comodo."""
    if len(texto) <= max_cars:
        return texto
    palabras = texto.split()
    mejor, mejor_dif = len(palabras) // 2, None
    for k in range(1, len(palabras)):
        a = len(" ".join(palabras[:k]))
        b = len(" ".join(palabras[k:]))
        if a > max_cars or b > max_cars:
            continue
        if mejor_dif is None or abs(a - b) < mejor_dif:
            mejor, mejor_dif = k, abs(a - b)
    return " ".join(palabras[:mejor]) + "\n" + " ".join(palabras[mejor:])


SOLAPE_MIN_DURACION = 0.30      # Ningun bloque baja de aqui al recortarlo.


def _sin_solapes(cues: list) -> list:
    """Recorta el final de un bloque cuando pisa el arranque del siguiente.

    De donde salen los solapes: los tiempos vienen de la alineacion de Whisper
    palabra a palabra, y Whisper puede dar a la ultima palabra de un bloque un
    final posterior al comienzo de la primera del bloque siguiente. No es un
    error de calculo nuestro; es que la transcripcion no garantiza que sus
    intervalos sean disjuntos.

    En el video de Secretariat pasaba en 5 de 278 bloques, el peor con 1,2 s de
    pisada. No rompe el .srt -ningun reproductor falla- pero puede pintar dos
    subtitulos a la vez, y eso en pantalla se ve como un error.

    Se recorta el ANTERIOR y no se retrasa el siguiente, a proposito: el arranque
    de un bloque esta atado a cuando se oye la palabra, y moverlo desincroniza el
    subtitulo de la voz, que es peor que acortar un final. El texto no se toca
    nunca; solo el momento en que desaparece.

    Si el recorte dejara el bloque por debajo de SOLAPE_MIN_DURACION, se deja
    como esta: un subtitulo que parpadea es peor que uno que se solapa un poco.
    """
    if not cues:
        return cues

    ajustados = [cues[0]]
    recortados = 0
    for ini, fin, txt in cues[1:]:
        p_ini, p_fin, p_txt = ajustados[-1]
        if p_fin > ini:
            nuevo_fin = ini
            if nuevo_fin - p_ini >= SOLAPE_MIN_DURACION:
                ajustados[-1] = (p_ini, nuevo_fin, p_txt)
                recortados += 1
        ajustados.append((ini, fin, txt))

    if recortados:
        print(f"  {recortados} bloque(s) se pisaban con el siguiente; "
              f"recortado su final.")
    return ajustados


def build_cues(project: str,
               max_palabras: int = None,
               min_palabras: int = None,
               max_cars: int = None,
               min_seg: float = None,
               umbral_fusion: float = None) -> list:
    """NUCLEO COMPARTIDO: devuelve los cues del proyecto, sin escribir nada.

    Lo usan los dos formatos. El largo (build()) los vuelca a un .srt suelto que
    se sube a la plataforma; el short (ShortAssembler) los quema en la imagen.
    Lo que cambia entre ambos son cuatro numeros, que llegan como argumentos; lo
    que NO cambia -emparejar guion con los tiempos de Whisper, acumular offsets
    incluyendo title cards, limpiar solapes- vive aqui una sola vez.

    Cada cue es un dict con los tiempos en las DOS bases:

        escena      indice de la escena
        inicio_rel  segundos desde el principio de SU escena
        fin_rel
        inicio_abs  segundos desde el principio del video completo
        fin_abs
        texto       ya partido en una o dos lineas

    El short necesita los relativos (compone overlay sobre el clip de la escena)
    y el .srt necesita los absolutos. Devolver ambos evita que cada llamador
    rehaga la aritmetica de offsets y se equivoque en las title cards.
    """
    max_palabras = config.SUBS_MAX_PALABRAS if max_palabras is None else max_palabras
    min_palabras = config.SUBS_MIN_PALABRAS if min_palabras is None else min_palabras
    max_cars = config.SUBS_MAX_CARS if max_cars is None else max_cars
    min_seg = config.SUBS_MIN_SEG if min_seg is None else min_seg

    paths = config.project_paths(project)
    if not paths["manifest"].exists():
        raise FileNotFoundError(
            f"No hay manifest en {paths['manifest']}. Corre primero 'parse'."
        )
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))

    cues, offset, sin_audio = [], 0.0, []
    for escena in manifest["scenes"]:
        idx = escena["index"]

        # Las title cards no llevan subtitulo, pero SI ocupan tiempo: si no se
        # suman, todo lo que viene despues queda desfasado.
        if escena["type"] == "title_card":
            offset += config.TITLE_CARD_DURATION
            continue

        mp3 = paths["base"] / (escena.get("audio_file") or "")
        if not mp3.exists():
            sin_audio.append(idx)
            continue
        duracion = escena.get("audio_duration")
        if not duracion:
            # Normalmente 'tts' ya dejo la duracion en el manifest. Si no (audios
            # puestos a mano), se mide con lo que ya hay instalado.
            try:
                from moviepy import AudioFileClip
                with AudioFileClip(str(mp3)) as a:
                    duracion = a.duration
            except Exception as e:
                print(f"[AVISO] no se pudo medir {mp3.name}: {e}; se omite.")
                sin_audio.append(idx)
                continue

        # Tiempos de Whisper (si existen); el TEXTO sale siempre del guion.
        wj = mp3.with_suffix(config.ALIGN_JSON_SUFFIX)
        words = []
        if wj.exists():
            try:
                words = TimestampAligner._normalize_words(
                    json.loads(wj.read_text(encoding="utf-8"))
                )
            except (ValueError, OSError):
                pass

        texto = escena.get("audio_text") or ""
        nuestras = texto.split()
        tiempos = _tiempos_por_palabra(texto, words, float(duracion))
        for ini, fin, txt in _bloques(nuestras, tiempos, float(duracion), 0.0,
                                      max_palabras, min_palabras, max_cars,
                                      min_seg, umbral_fusion):
            cues.append({
                "escena": idx,
                "inicio_rel": ini,
                "fin_rel": fin,
                "inicio_abs": offset + ini,
                "fin_abs": offset + fin,
                "texto": txt,
            })
        offset += float(duracion)

    if sin_audio:
        print(f"[AVISO] escenas sin audio, se omiten: {sin_audio} (corre 'tts').")
    return cues


def build(project: str) -> Path:
    """Genera subtitulos.srt con la linea de tiempo del video completo."""
    paths = config.project_paths(project)
    cues = build_cues(project)
    cues = _sin_solapes([(c["inicio_abs"], c["fin_abs"], c["texto"]) for c in cues])

    out = paths["base"] / config.SUBS_FILENAME
    with out.open("w", encoding="utf-8") as f:
        for n, (ini, fin, txt) in enumerate(cues, start=1):
            f.write(f"{n}\n{_fmt(ini)} --> {_fmt(fin)}\n{txt}\n\n")

    print(f"Subtitulos generados: {out}")
    cubierto = cues[-1][1] if cues else 0.0
    print(f"  {len(cues)} bloques · duracion cubierta {_fmt(cubierto)}")
    return out

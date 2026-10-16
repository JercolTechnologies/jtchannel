# -*- coding: utf-8 -*-
# Ruta: engine/scripts/assembler.py
#
# MODULO 3 y 4 - Ensamblador de Video (MoviePy) + Renderizado.
# Lee el manifest.json, construye un subclip 1920x1080 por cada escena y los
# concatena en un unico final.mp4 (1080p @ 30fps, H.264 + AAC).
#
# Logica por escena 
#   - title_card : fondo negro + texto blanco grueso, duracion fija.
#   - narrated + VIDEO (.mp4/.mov) : duracion = audio. Mas largo -> recorta;
#                                    mas corto -> LOOP (repite).
#   - narrated + IMAGEN (.jpg/.png): clip con zoom-in suave (Ken Burns) que cubre
#                                    toda la duracion del audio (sin saltos).
#   - Aspect ratio != 16:9 : fondo = mismo asset a pantalla completa + BLUR fuerte
#                            (calculado sobre un frame congelado, por rendimiento),
#                            con el asset nitido centrado encima.
#
# Nota de version: escrito para MoviePy 2.x (usa .resized()/.cropped()/.with_*()
# y TextClip basado en Pillow, por lo que NO requiere ImageMagick en Windows).

import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageFilter

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
    vfx,
)

try:
    from . import config
    from . import grade
except ImportError:
    import config
    import grade


class VideoAssembler:
    """Ensambla el video final de un proyecto a partir de su manifest.json."""

    def __init__(self, manifest_path: Path, assets_dir: Path, output_path: Path):
        self.manifest_path = Path(manifest_path)
        self.assets_dir = Path(assets_dir)
        self.output_path = Path(output_path)
        self.W, self.H = config.RESOLUTION
        self.target_aspect = self.W / self.H

    # -----------------------------------------------------------------------
    # CARGA Y ORQUESTACION
    # -----------------------------------------------------------------------
    def _load_manifest(self) -> dict:
        """Lee el manifest.json (debe existir; lo genera el parser)."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"No existe el manifest: {self.manifest_path}. Corre primero el parser."
            )
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _find_assets(self, index: int) -> list[Path]:
        """Busca en assets/ TODOS los archivos cuyo nombre EMPIECE por el numero de escena.

        Tolera cualquier separador tras el numero (espacio, guion, guion bajo...),
        asi que valen '04_clip.mp4', '04 - broll.mov', '4-foto.jpg', etc. Se compara
        el numero como entero, de modo que la escena 1 no se confunde con la 10 o 12.

        Multi-asset (ADR-015): si hay varios archivos para la misma escena (p. ej.
        '01a_hook.mp4', '01b_broll.mp4', '01c_foto.jpg'), se devuelven TODOS ordenados
        por nombre. Ese orden alfabetico es el orden en que apareceran en pantalla, por
        eso conviene el sufijo de letra (a, b, c...) tras el numero. Con un solo asset
        ('01_clip.mp4') la lista trae un unico elemento (comportamiento clasico).
        """
        if not self.assets_dir.exists():
            return []
        matches = []
        for p in sorted(self.assets_dir.iterdir()):
            if not p.is_file():
                continue
            m = re.match(r"\s*(\d+)", p.name)  # digitos iniciales del nombre
            if m and int(m.group(1)) == index:
                matches.append(p)
        return matches

    def build(self, only: set[int] | None = None) -> None:
        """Construye los subclips, los concatena y renderiza el video.

        only=None      -> ensambla todas las escenas del manifest.
        only={1, 2}    -> ensambla solo esas escenas (mini-render de prueba).
        """
        manifest = self._load_manifest()
        clips = []
        missing = []  # escenas narradas sin asset -> las reportamos al final

        for scene in manifest["scenes"]:
            idx = scene["index"]
            if only is not None and idx not in only:
                continue  # fuera del subconjunto pedido para este render
            if scene["type"] == "title_card":
                print(f"  Escena {idx:02d}: title card -> \"{scene['title_text']}\"")
                clips.append(self._build_title_card(scene["title_text"], idx))
                continue

            # --- Escena narrada: necesita audio + asset(s) local(es) ---
            audio_path = self._resolve_audio(scene)
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration

            shots = scene.get("shots")
            if shots:
                # Modo SHOTS (ADR-018): cada asset por slot, con su duracion exacta.
                visual = self._build_from_shots(idx, shots, duration, missing)
                if visual is None:
                    continue  # faltaba algun slot; ya quedo anotado en 'missing'
            else:
                # Modo clasico: assets por numero de escena (reparto igual si hay varios).
                asset_paths = self._find_assets(idx)
                if not asset_paths:
                    missing.append(f"{idx:02d}_...")
                    continue
                visual = self._build_narrated_visual(idx, asset_paths, duration)

            clip = visual.with_audio(audio).with_duration(duration)
            # Overlays de texto ENCIMA (ADR-019): solo esta escena paga el compose.
            if scene.get("overlays"):
                clip = self._apply_overlays(idx, clip, scene["overlays"], duration)
            clips.append(clip)

        if missing:
            # Fallamos con un mensaje claro en vez de renderizar algo incompleto.
            faltan = ", ".join(missing)
            raise FileNotFoundError(
                f"Faltan assets: {faltan}. "
                f"Ponlos en {self.assets_dir} y vuelve a correr el ensamblador."
            )

        self._render(clips, manifest["fps"])

    def _resolve_audio(self, scene: dict) -> Path:
        """Obtiene la ruta absoluta del mp3 de una escena narrada."""
        # scene['audio_file'] es relativo al proyecto (ej. 'audio/01_audio.mp3').
        audio_path = self.manifest_path.parent / scene["audio_file"]
        if not audio_path.exists():
            raise FileNotFoundError(
                f"Falta el audio de la escena {scene['index']}: {audio_path}. "
                f"Corre primero el modulo TTS."
            )
        return audio_path

    # -----------------------------------------------------------------------
    # CONSTRUCTORES DE ESCENA
    # -----------------------------------------------------------------------
    def _find_asset_by_slot(self, slot: str) -> Optional[Path]:
        """Busca en assets/ el archivo cuyo prefijo (numero + letra) sea EXACTAMENTE el slot.

        Ej. slot '04a' casa '04a_gates.jpg', '04A - foto.png'; NO casa '04_x.jpg'.
        Ignora la subcarpeta de candidatos (solo mira archivos sueltos en assets/).
        """
        if not self.assets_dir.exists():
            return None
        slot = slot.lower()
        for p in sorted(self.assets_dir.iterdir()):
            if not p.is_file():
                continue
            m = re.match(r"\s*(\d+[a-zA-Z]?)", p.name)
            if m and m.group(1).lower() == slot:
                return p
        return None

    def _build_from_shots(self, idx: int, shots: list, duration: float, missing: list):
        """Coloca cada shot por su slot con su duracion EXACTA (cortes precisos).

        Los shots ya traen 'duration' del paso 'align' (marcador -> segundo). Se usan
        cortes secos (chain), no disolvencias: el objetivo es que cada imagen entre
        justo en su segundo, y un crossfade suavizaria ese punto exacto. Si algun slot
        no tiene archivo, se anota en 'missing' y se devuelve None. Si los shots no
        traen timing (no se corrio 'align'), cae a reparto igual y avisa.
        """
        resolved, faltan = [], []
        for shot in shots:
            p = self._find_asset_by_slot(shot["slot"])
            if p is None:
                faltan.append(f"{shot['slot']}_...")
            else:
                resolved.append((shot, p))
        if faltan:
            missing.extend(faltan)
            return None

        tiene_timing = all(s.get("duration") for s, _ in resolved)
        if tiene_timing:
            durs = [float(s["duration"]) for s, _ in resolved]
            durs[-1] += duration - sum(durs)   # cuadra el total exacto (evita deriva)
        else:
            k = len(resolved)
            durs = [duration * (i + 1) / k - duration * i / k for i in range(k)]
            print(f"  [AVISO] Escena {idx:02d}: shots sin timing (corre 'align'); "
                  f"reparto igual entre {k}.")

        detalle = ", ".join(f"{s['slot']}({d:.1f}s)" for (s, _), d in zip(resolved, durs))
        print(f"  Escena {idx:02d}: {len(resolved)} shots -> {detalle}")

        subs = [self._build_single_visual(idx, p, d, shot)
                for (shot, p), d in zip(resolved, durs)]
        return concatenate_videoclips(subs, method="chain").with_duration(duration)

    def _build_narrated_visual(self, idx: int, asset_paths: list[Path], duration: float):
        """Arma el visual de una escena narrada a partir de uno o varios assets.

        Un solo asset -> cubre toda la duracion (comportamiento clasico).
        Varios assets  -> se reparten la duracion del audio en partes iguales y se
        concatenan en un unico clip de escena de duracion EXACTA. El audio (uno solo)
        se pega despues, en build(): la narracion es continua y los visuales cambian
        por debajo. La concatenacion interna usa 'chain' (todas las sub-escenas ya
        miden 1920x1080); las disolvencias entre assets llegan en ADR-016.
        """
        usable = self._plan_subclips(idx, asset_paths, duration)

        if len(usable) == 1:
            path = usable[0]
            print(f"  Escena {idx:02d}: {path.name}  (audio {duration:.1f}s)")
            return self._build_single_visual(idx, path, duration)

        # Varios assets: se reparten la duracion y se solapan con una disolvencia
        # de 'd' segundos. Para que tras el solape el total siga siendo EXACTAMENTE
        # 'duration', se construyen sub-clips que suman duration + (k-1)*d (el compose
        # con padding=-d se "come" esos (k-1)*d de solape). El crossfade se acota a la
        # mitad de cada tramo para que nunca sea mas largo que el propio sub-clip.
        k = len(usable)
        d = min(config.CROSSFADE_DURATION, (duration / k) * 0.5) if k > 1 else 0.0
        total = duration + (k - 1) * d

        names = ", ".join(p.name for p in usable)
        modo = f"crossfade {d:.2f}s" if d > 0 else "corte seco"
        print(f"  Escena {idx:02d}: {k} assets [{names}]  (audio {duration:.1f}s, "
              f"~{duration / k:.1f}s c/u, {modo})")

        # Reparto por FRONTERAS acumuladas sobre 'total' (evita deriva por redondeo).
        subs = []
        for i, path in enumerate(usable):
            sub_dur = total * (i + 1) / k - total * i / k
            subs.append(self._build_single_visual(idx, path, sub_dur))
        return self._concat_scene(subs, d).with_duration(duration)

    def _concat_scene(self, subs: list, crossfade: float):
        """Concatena los sub-clips de UNA escena, con o sin disolvencia entre ellos.

        Sin crossfade (o un solo sub-clip) -> 'chain' (rapido, sin recomponer).
        Con crossfade -> compose con padding negativo: cada sub-clip entra con un
        CrossFadeIn sobre el anterior. Es compose LOCAL a la escena (pocos clips
        cortos), no del video entero, asi que el 'chain' global se conserva.
        """
        if crossfade <= 0 or len(subs) == 1:
            return concatenate_videoclips(subs, method="chain")
        layered = [subs[0]] + [c.with_effects([vfx.CrossFadeIn(crossfade)]) for c in subs[1:]]
        return concatenate_videoclips(layered, method="compose", padding=-crossfade)

    def _plan_subclips(self, idx: int, asset_paths: list[Path], duration: float) -> list[Path]:
        """Decide cuantos assets de la escena caben respetando MIN_SUBCLIP_DURATION.

        Si repartir todos dejaria cortes por debajo del piso, se usan solo los
        primeros que caben (orden alfabetico = orden en pantalla) y se avisa.
        Siempre se usa al menos uno.
        """
        max_by_floor = int(duration // config.MIN_SUBCLIP_DURATION)
        k = max(1, min(len(asset_paths), max_by_floor))
        if k < len(asset_paths):
            descartados = ", ".join(p.name for p in asset_paths[k:])
            print(f"  [AVISO] Escena {idx:02d}: audio de {duration:.1f}s solo admite "
                  f"{k} corte(s) de >= {config.MIN_SUBCLIP_DURATION:.0f}s. "
                  f"Se omiten: {descartados}.")
        return asset_paths[:k]

    # -----------------------------------------------------------------------
    # CREDITO QUEMADO (ADR-024)
    # -----------------------------------------------------------------------
    def _credits_index(self) -> dict:
        """Lee CREDITS.txt una sola vez -> {archivo: (autor, licencia)}.

        Se cachea porque se consulta por cada asset del video.
        """
        if getattr(self, "_credits_cache", None) is not None:
            return self._credits_cache
        idx = {}
        path = self.assets_dir / "CREDITS.txt"
        if path.exists():
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
                if not line.strip() or (i == 0 and line.lower().startswith("archivo")):
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    idx[parts[0].strip()] = (parts[2].strip(), parts[3].strip())
        self._credits_cache = idx
        return idx

    def _credit_text(self, path: Path) -> Optional[str]:
        """Texto de credito a quemar para este asset, o None si no hace falta.

        Solo lo necesitan las licencias de ATRIBUCION (CC BY). Dominio publico,
        CC0 y Pexels no exigen nada, asi que no se les pone.
        """
        if not config.CREDIT_BURN_ENABLED:
            return None
        autor, lic = self._credits_index().get(path.name, ("", ""))
        if not lic:
            return None                    # Pexels (columna vacia) o sin dato
        try:
            from .wikimedia import license_tier
        except ImportError:
            from wikimedia import license_tier
        if license_tier(lic) != "atribucion":
            return None
        txt = config.CREDIT_BURN_TEMPLATE.format(author=autor or "?", license=lic)
        return txt[:config.CREDIT_BURN_MAX_CHARS]

    def _with_credit(self, clip, path: Path, duration: float):
        """Compone el credito en la esquina inferior derecha, si este asset lo pide."""
        texto = self._credit_text(path)
        if not texto:
            return clip
        try:
            capas = [clip]
            if config.CREDIT_BURN_SHADOW:
                sombra = (TextClip(text=texto, font=config.TITLE_CARD_FONT,
                                   font_size=config.CREDIT_BURN_FONT_SIZE, color="black")
                          .with_duration(duration).with_opacity(0.5)
                          .with_position((self.W - config.CREDIT_BURN_MARGIN + 1,
                                          self.H - config.CREDIT_BURN_MARGIN + 1),
                                         relative=False))
                capas.append(sombra)
            txt = (TextClip(text=texto, font=config.TITLE_CARD_FONT,
                            font_size=config.CREDIT_BURN_FONT_SIZE,
                            color=config.CREDIT_BURN_COLOR)
                   .with_duration(duration).with_opacity(config.CREDIT_BURN_OPACITY))
            # Se ancla por su esquina: hay que restar su propio tamano.
            tw, th = txt.size
            x = self.W - tw - config.CREDIT_BURN_MARGIN
            y = self.H - th - config.CREDIT_BURN_MARGIN
            if config.CREDIT_BURN_SHADOW:
                capas[1] = capas[1].with_position((x + 1, y + 1))
            capas.append(txt.with_position((x, y)))
            print(f"    credito quemado: \"{texto}\"")
            return CompositeVideoClip(capas, size=(self.W, self.H)).with_duration(duration)
        except Exception as e:
            # Un fallo tipografico no debe tumbar el render, pero SI hay que
            # verlo: sin credito, ese asset no cumple su licencia.
            print(f"    [ERROR] no se pudo quemar el credito de {path.name}: {e}")
            return clip

    def _build_single_visual(self, idx: int, path: Path, duration: float,
                             shot: Optional[dict] = None):
        """Despacha un asset (video o imagen) al constructor que le corresponde.

        El credito quemado se aplica AQUI, en el ultimo paso: asi cubre las dos
        ramas (video e imagen) y queda por encima del grade y del zoom, que si no
        se lo llevarian por delante al recortar el frame.
        """
        suffix = path.suffix.lower()
        if suffix in config.VIDEO_EXTENSIONS:
            clip = self._build_video_scene(path, duration)
        elif suffix in config.IMAGE_EXTENSIONS:
            clip = self._build_image_scene(path, duration, shot)
        else:
            raise ValueError(f"Extension no soportada en escena {idx}: {path.name}")
        return self._with_credit(clip, path, duration)

    # -----------------------------------------------------------------------
    # OVERLAYS DE TEXTO (ADR-019)
    # -----------------------------------------------------------------------
    def _apply_overlays(self, idx: int, base_clip, overlays: list, duration: float):
        """Compone los overlays de texto encima de la escena base (a su tiempo)."""
        layers = [base_clip]
        for ov in overlays:
            unit = self._build_overlay(idx, ov, duration)
            if unit is not None:
                layers.append(unit)
        if len(layers) == 1:
            return base_clip
        comp = CompositeVideoClip(layers, size=(self.W, self.H)).with_duration(duration)
        return comp.with_audio(base_clip.audio)  # conserva la narracion

    def _build_overlay(self, idx: int, ov: dict, scene_duration: float):
        """Construye UN overlay de texto colocado en su segundo, con su caja y fade."""
        kind = (ov.get("kind") or "text").lower()
        if kind != "text":
            print(f"  [AVISO] Escena {idx:02d}: overlay '{kind}' no soportado en v1 (solo texto).")
            return None
        content = (ov.get("content") or "").strip()
        if not content:
            return None

        style_name = ov.get("style") or config.OVERLAY_DEFAULT_STYLE
        style = config.OVERLAY_STYLES.get(style_name)
        if style is None:
            print(f"  [AVISO] Escena {idx:02d}: estilo '{style_name}' desconocido; "
                  f"uso '{config.OVERLAY_DEFAULT_STYLE}'.")
            style = config.OVERLAY_STYLES[config.OVERLAY_DEFAULT_STYLE]

        start = float(ov.get("start") or 0.0)
        dur = float(ov.get("duration") or config.OVERLAY_DEFAULT_DURATION)
        dur = min(dur, max(0.0, scene_duration - start))
        if dur <= 0:
            return None

        unit = self._text_overlay_unit(content, style)
        unit = unit.with_start(start).with_duration(dur)

        # Entrada deslizada (ADR-023): sube desde abajo, salvo el estilo anclado
        # arriba, que baja — el movimiento siempre viene "desde fuera" del borde
        # mas cercano, que es lo que se lee como natural.
        x, y = self._overlay_position(style["position"], unit.size)
        dy = config.OVERLAY_SLIDE_DISTANCE
        if style["position"] == "top_left":
            dy = -dy
        slide = min(config.OVERLAY_SLIDE_DURATION, dur)
        unit = unit.with_position(self._slide_position(x, y, dy, slide))

        fade = min(config.OVERLAY_FADE, dur / 2)
        if fade > 0:
            unit = unit.with_effects([vfx.CrossFadeIn(fade), vfx.CrossFadeOut(fade)])
        print(f"    overlay [{style_name}] \"{content[:24]}\"  @{start:.1f}s ({dur:.1f}s)")
        return unit

    def _text_overlay_unit(self, content: str, style: dict):
        """Texto + caja + franja de acento, como una sola unidad (ADR-023).

        La franja roja de marca se compone DENTRO de la unidad (no como capa
        aparte) para que herede el fade y el deslizamiento sin trabajo extra: al
        animar la unidad se mueve todo junto.
        """
        # Caja de texto (ADR-035). Dos fallos que se veian en el video:
        #
        # 1. CORTE POR ABAJO. Con method="label" el alto del clip es justo el que
        #    Pillow calcula para el texto, y ahi la tinta llega a la ULTIMA fila de
        #    pixeles: medido, holgura de 0px. La coma es el caracter que mas baja de
        #    la linea base y casi todos los overlays de cifra van llenos de comas,
        #    por eso se veia en casi todos y no en unos pocos. El margen vertical
        #    proporcional al cuerpo de letra reserva ese sitio.
        #
        # 2. CORTE LATERAL. "label" no envuelve: escribe una linea y punto, aunque
        #    mida mas que el frame. "Nokia - 2013 - $7,200,000,000" da 1863px de los
        #    1920 disponibles; cualquier cifra un poco mas larga se sale por los
        #    lados. Se mide primero en una linea y solo si desborda se rehace como
        #    "caption", que si envuelve.
        #
        # El orden importa: "caption" fija el ancho del clip al maximo permitido
        # AUNQUE el texto sea corto, y entonces la caja de fondo saldria enorme
        # detras de un texto pequeno. Por eso una linea es el caso por defecto y el
        # envuelto la excepcion.
        fuente_kw = dict(font=style["font"], font_size=style["font_size"],
                         color=style["color"])
        margen_v = max(6, round(style["font_size"] * config.OVERLAY_DESCENDER_RATIO))
        ancho_max = int(self.W * config.OVERLAY_MAX_WIDTH_RATIO)

        txt = TextClip(text=content, method="label", margin=(0, margen_v), **fuente_kw)
        if txt.size[0] > ancho_max:
            txt = TextClip(text=content, method="caption", size=(ancho_max, None),
                           text_align="center", margin=(0, margen_v), **fuente_kw)

        pad = style.get("padding", 20)
        tw, th = txt.size
        box_w, box_h = tw + 2 * pad, th + 2 * pad
        accent = style.get("accent")
        aw = 0
        if accent == "left":
            aw = config.OVERLAY_ACCENT_WIDTH_SIDE
        elif accent == "bottom":
            aw = config.OVERLAY_ACCENT_WIDTH

        # La unidad crece para dejarle sitio a la franja segun donde vaya.
        if accent == "left":
            total, box_xy, txt_xy = (box_w + aw, box_h), (aw, 0), (aw + pad, pad)
            bar_size, bar_xy = (aw, box_h), (0, 0)
        elif accent == "bottom":
            total, box_xy, txt_xy = (box_w, box_h + aw), (0, 0), (pad, pad)
            bar_size, bar_xy = (box_w, aw), (0, box_h)
        else:
            total, box_xy, txt_xy = (box_w, box_h), (0, 0), (pad, pad)
            bar_size = bar_xy = None

        layers = []
        if style.get("box_opacity", 0) > 0:
            layers.append(
                ColorClip(size=(box_w, box_h), color=style.get("box_color", (0, 0, 0)))
                .with_opacity(style["box_opacity"]).with_position(box_xy)
            )
        if bar_size:
            layers.append(
                ColorClip(size=bar_size, color=config.OVERLAY_ACCENT_COLOR)
                .with_position(bar_xy)
            )
        layers.append(txt.with_position(txt_xy))

        if len(layers) == 1:
            return txt
        return CompositeVideoClip(layers, size=total)

    def _overlay_position(self, name: str, size) -> tuple:
        """Posicion NUMERICA (x, y) del overlay dentro del frame 1920x1080.

        Se resuelve a numeros —y no a 'center'— porque la entrada animada calcula
        la posicion en funcion del tiempo y necesita aritmetica.
        """
        W, H = self.W, self.H
        w, h = size
        m = int(0.05 * W)
        return {
            "center": ((W - w) // 2, (H - h) // 2),
            "lower_left": (m, int(H * 0.80)),
            "top_left": (m, int(H * 0.06)),
            "bottom_center": ((W - w) // 2, int(H * 0.82)),
        }.get(name, ((W - w) // 2, (H - h) // 2))

    @staticmethod
    def _slide_position(x: int, y: int, dy: int, slide_dur: float):
        """Devuelve una funcion posicion(t) que desliza el overlay al entrar.

        Usa ease-out cubico: arranca rapido y frena al llegar, como los graficos
        de television. Pasado 'slide_dur' queda quieto en (x, y).
        """
        def pos(t):
            if slide_dur <= 0:
                return (x, y)
            p = min(max(t / slide_dur, 0.0), 1.0)
            eased = 1 - (1 - p) ** 3
            return (x, int(round(y + dy * (1 - eased))))
        return pos

    def _build_title_card(self, text: str, idx: Optional[int] = None):
        """Crea una title card.

        Si hay un asset con el numero de esa escena (p. ej. '23.png'), se usa ESA
        IMAGEN en vez de generar el texto: sirve para poner el logo o una tarjeta
        disenada, que cierra mucho mejor que texto compuesto al vuelo (ADR-028).
        Se muestra estatica -sin zoom-: en una pieza de marca el movimiento
        distrae, mientras que en B-roll evita que se sienta muerta.

        Si no hay imagen, se genera lo de siempre: fondo negro + texto blanco.
        """
        if idx is not None:
            propia = self._find_asset_by_slot(f"{idx:02d}")
            if propia and propia.suffix.lower() in config.IMAGE_EXTENSIONS:
                print(f"    (usa la imagen {propia.name} en vez de generar texto)")
                img = self._pil_downscaled(propia, config.IMAGE_WORKING_MAX_DIM)
                if config.GRADE_ENABLED and not grade.should_skip(propia):
                    img = grade.apply_grade(img)
                if abs(img.width / img.height - self.target_aspect) <= config.ASPECT_TOLERANCE:
                    still = self._pil_cover(img, self.W, self.H)
                else:
                    # Fondo de MARCA, no desenfoque: una pieza de branding sobre su
                    # propio color se lee limpia; sobre un blur se ve improvisada.
                    still = Image.new("RGB", (self.W, self.H), tuple(config.BRAND_BG_COLOR))
                    fg = self._pil_contain(img, self.W, self.H)
                    still.paste(fg, ((self.W - fg.width) // 2, (self.H - fg.height) // 2))
                return ImageClip(np.array(still)).with_duration(config.TITLE_CARD_DURATION)
        background = ColorClip(
            size=(self.W, self.H),
            color=config.TITLE_CARD_BG_COLOR,
        ).with_duration(config.TITLE_CARD_DURATION)

        # Caja de texto con altura EXPLICITA y amplia: el texto se centra dentro
        # de ella (vertical y horizontalmente), evitando el recorte de la parte
        # inferior de las letras que ocurre con altura automatica (size=(w, None)).
        text_box = (
            int(self.W * config.TITLE_CARD_TEXT_WIDTH_RATIO),
            int(self.H * config.TITLE_CARD_TEXT_HEIGHT_RATIO),
        )
        txt = TextClip(
            text=text,
            font=config.TITLE_CARD_FONT,
            font_size=config.TITLE_CARD_FONT_SIZE,
            color=config.TITLE_CARD_TEXT_COLOR,
            method="caption",          # envuelve el texto dentro del ancho dado
            size=text_box,
            text_align="center",       # alineacion de las lineas entre si
            horizontal_align="center", # posicion del bloque dentro de la caja
            vertical_align="center",
        ).with_duration(config.TITLE_CARD_DURATION).with_position("center")

        return CompositeVideoClip([background, txt], size=(self.W, self.H))

    def _build_video_scene(self, path: Path, duration: float):
        """Clip de VIDEO ajustado EXACTAMENTE a la duracion del audio.

        - Mas largo que el audio -> se recorta.
        - Mas corto -> se repite en BUCLE, salvo que el nombre pida CONGELAR el
          ultimo frame (ADR-022): un grafico que culmina en una cifra no puede
          reiniciarse a mitad de la narracion.
        Luego se encaja al frame 1920x1080 (fill o blur-pad segun aspecto).
        """
        clip = VideoFileClip(str(path)).without_audio()

        if clip.duration < duration:
            if _should_freeze(path):
                clip = self._freeze_to(clip, duration)
            else:
                clip = self._loop_to(clip, duration)
        else:
            clip = clip.subclipped(0, duration)

        return self._fit_video(clip, duration)

    def still_de_imagen(self, path: Path) -> Image.Image:
        """Devuelve el FOTOGRAMA 1920x1080 ya terminado de una imagen.

        Se extrajo para que el preview pueda ensenar EXACTAMENTE lo que va a salir
        en el video (ADR-029). Antes el preview mostraba el archivo crudo y el
        encaje ocurria solo al renderizar, asi que aprobabas visuales que no eran
        los definitivos — un logo se veia enorme en la tarjeta y luego salia al 62%
        sobre el gris de marca.

        Al compartir este metodo, preview y render NO PUEDEN divergir.
        """
        img = self._pil_downscaled(path, config.IMAGE_WORKING_MAX_DIM)
        # Look unificado (ADR-020): se aplica a la imagen FUENTE, una sola vez por
        # escena, para que el fondo desenfocado y el primer plano queden iguales.
        if config.GRADE_ENABLED and not grade.should_skip(path):
            img = grade.apply_grade(img)

        if abs(img.width / img.height - self.target_aspect) <= config.ASPECT_TOLERANCE:
            # Cover: la imagen llena todo el frame.
            return self._pil_cover(img, self.W, self.H)

        if img.info.get("logo_recortado"):
            # Es un LOGO (se le quito un fondo plano): va sobre el gris de marca,
            # no sobre un desenfoque de si mismo. Desenfocar un logo deja un halo
            # de color alrededor y se ve improvisado; sobre el color del canal se
            # lee como una pieza disenada (ADR-028).
            still = Image.new("RGB", (self.W, self.H), tuple(config.BRAND_BG_COLOR))
            fg = self._pil_contain(img, int(self.W * 0.62), int(self.H * 0.62))
            still.paste(fg, ((self.W - fg.width) // 2, (self.H - fg.height) // 2))
            return still

        # Blur-pad: fondo desenfocado + imagen nitida centrada, compuesto ya en un
        # solo lienzo 1920x1080 (asi el zoom aplica al conjunto).
        still = self._pil_cover(img, self.W, self.H).filter(
            ImageFilter.GaussianBlur(config.BLUR_RADIUS)
        )
        fg = self._pil_contain(img, self.W, self.H)
        still.paste(fg, ((self.W - fg.width) // 2, (self.H - fg.height) // 2))
        return still

    def _build_image_scene(self, path: Path, duration: float,
                           shot: Optional[dict] = None):
        """Clip a partir de una IMAGEN con zoom-in suave (Ken Burns) por toda la duracion.

        Estrategia (rapida): se HORNEA una sola imagen final de 1920x1080 (cover, o
        el composite blur-pad ya armado) y sobre ESE array se aplica el zoom por-frame
        con OpenCV. Evita reescalar por-frame con PIL/MoviePy (que era ~7x mas lento).
        """
        still = self.still_de_imagen(path)

        # Alterna acercar/alejar entre imagenes consecutivas (ADR-024): con muchos
        # planos seguidos, el mismo zoom-in siempre se vuelve mecanico y delata el
        # automatismo. Alternar cuesta cero y da sensacion de montaje.
        self._img_n = getattr(self, "_img_n", -1) + 1
        acercar = (self._img_n % 2 == 0) if config.KENBURNS_ALTERNATE else True
        rate = config.KENBURNS_ZOOM_RATE
        # Un plano puede pedir su propio movimiento con tokens en el marcador. Se
        # usa donde el zoom CUENTA algo: acercarse despacio a una puerta al final
        # del video se lee como avanzar hacia ella (ADR-028).
        if shot:
            if shot.get("zoom_dir") == "in":
                acercar = True
            elif shot.get("zoom_dir") == "out":
                acercar = False
            if shot.get("zoom_fuerte"):
                rate = config.KENBURNS_STRONG_RATE
                print(f"    (zoom {'de acercamiento' if acercar else 'de alejamiento'} "
                      f"marcado, {rate * 100:.0f}%)")
        return self._kenburns_zoom(np.array(still), duration, acercar, rate)

    def _kenburns_zoom(self, base: np.ndarray, duration: float,
                       acercar: bool = True, rate: Optional[float] = None):
        """Zoom progresivo sobre una imagen fija de 1920x1080, via OpenCV.

        Por cada frame recorta una ventana centrada y la reescala al frame completo
        (cv2.resize en C/SIMD). El resultado es un movimiento suave renderizando a
        decenas de fps, en vez de los ~6 fps del resize con PIL.

        acercar=True  -> arranca al 100% y se acerca (zoom in).
        acercar=False -> arranca acercado y se aleja (zoom out).
        """
        W, H = self.W, self.H
        rate = config.KENBURNS_ZOOM_RATE if rate is None else rate

        def make_frame(t: float) -> np.ndarray:
            p = t / duration if duration else 0.0
            zoom = (1 + rate * p) if acercar else (1 + rate * (1 - p))
            cw, ch = int(W / zoom), int(H / zoom)     # ventana a recortar (centrada)
            x, y = (W - cw) // 2, (H - ch) // 2
            crop = base[y:y + ch, x:x + cw]
            return cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR)

        return VideoClip(make_frame, duration=duration)

    # -----------------------------------------------------------------------
    # ENCAJE AL FRAME (solo VIDEO) + EFECTOS
    # -----------------------------------------------------------------------
    def _fit_video(self, clip, duration: float):
        """Encaja un clip de VIDEO en 1920x1080: cover si es ~16:9, si no blur-pad.

        A diferencia de las imagenes, el video se reescala por-frame (inevitable),
        pero el fondo desenfocado se calcula sobre UN frame congelado para no
        disparar el tiempo de render.
        """
        clip_aspect = clip.w / clip.h
        if abs(clip_aspect - self.target_aspect) <= config.ASPECT_TOLERANCE:
            return self._cover(clip, self.W, self.H).with_duration(duration)

        background = self._blurred_background(clip, duration)
        foreground = self._contain(clip, self.W, self.H).with_position("center")
        return CompositeVideoClip(
            [background, foreground], size=(self.W, self.H)
        ).with_duration(duration)

    def _blurred_background(self, clip, duration: float):
        """Fondo a pantalla completa, desenfocado, a partir de UN frame congelado."""
        frame = clip.get_frame(0)  # numpy array (H, W, 3) del primer frame
        pil = Image.fromarray(frame).filter(ImageFilter.GaussianBlur(config.BLUR_RADIUS))
        cover = self._pil_cover(pil, self.W, self.H)
        return ImageClip(np.array(cover)).with_duration(duration)

    # -----------------------------------------------------------------------
    # HELPERS DE ESCALADO
    # -----------------------------------------------------------------------
    @staticmethod
    def _pil_downscaled(path: Path, max_dim: int) -> Image.Image:
        """Abre una imagen y la reduce (una sola vez) a como maximo max_dim px de lado.

        Si trae canal alfa, se APLANA sobre el fondo del canal en vez de dejar que
        `convert("RGB")` decida: los logos de Commons llegan con transparencia, y
        convertir a ciegas los planta sobre blanco o negro puro. Componerlos sobre
        el #131313 de la marca hace que un logo se integre en vez de aparecer como
        un recorte pegado encima (ADR-027).
        """
        img = Image.open(path)
        # Un logo bajado suele traer fondo blanco HORNEADO (sin canal alfa). Se
        # detecta y se vuelve transparente antes de aplanar, si no el aplanado lo
        # dejaria igual de blanco (ADR-028).
        img = _quitar_fondo_plano(img)
        era_logo = bool(img.info.get("logo_recortado"))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fondo = Image.new("RGBA", img.size, tuple(config.BRAND_BG_COLOR) + (255,))
            img = Image.alpha_composite(fondo, img)
        img = img.convert("RGB")
        scale = min(1.0, max_dim / max(img.size))
        if scale < 1.0:
            img = img.resize(
                (round(img.width * scale), round(img.height * scale)), Image.LANCZOS
            )
        if era_logo:
            img.info["logo_recortado"] = True
        return img

    @staticmethod
    def _pil_cover(img: Image.Image, w: int, h: int) -> Image.Image:
        """Escala para LLENAR (cover) w x h y recorta el excedente centrado (en PIL)."""
        scale = max(w / img.width, h / img.height)
        nw, nh = round(img.width * scale), round(img.height * scale)
        resized = img.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - w) // 2, (nh - h) // 2
        return resized.crop((left, top, left + w, top + h))

    @staticmethod
    def _pil_contain(img: Image.Image, w: int, h: int) -> Image.Image:
        """Escala para CABER (contain) dentro de w x h sin recortar (en PIL)."""
        scale = min(w / img.width, h / img.height)
        return img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)

    def _cover(self, clip, w: int, h: int):
        """Escala un clip de VIDEO para LLENAR (cover) w x h y recorta lo que sobra."""
        scale = max(w / clip.w, h / clip.h)
        scaled = clip.resized(scale)
        return scaled.cropped(
            x_center=scaled.w / 2, y_center=scaled.h / 2, width=w, height=h
        )

    def _contain(self, clip, w: int, h: int):
        """Escala para CABER (contain) dentro de w x h sin recortar (deja barras)."""
        scale = min(w / clip.w, h / clip.h)
        return clip.resized(scale)

    def _loop_to(self, clip, duration: float):
        """Repite el clip en bucle hasta cubrir 'duration' y recorta al final exacto.

        Metodo manual (concatenar N copias) para no depender de la API de efectos,
        que cambia entre versiones de MoviePy.
        """
        n = math.ceil(duration / clip.duration)
        looped = concatenate_videoclips([clip] * n)
        return looped.subclipped(0, duration)

    def _freeze_to(self, clip, duration: float):
        """Reproduce el clip UNA vez y sostiene su ultimo frame hasta 'duration'.

        Para animaciones que culminan (contador, grafico que se dibuja): la cifra
        final se alcanza y se queda en pantalla mientras la voz sigue hablando,
        en vez de reiniciarse como haria el bucle.
        """
        # EL RETROCESO SE MIDE EN FRAMES, NO SOLO EN SEGUNDOS.
        #
        # VIDEO_FREEZE_EPSILON son 0.05 s, y eso da por hecho que el clip va a
        # 20 fps o mas. A 15 fps un frame dura 0.067 s: 0.05 no retrocede ni un
        # frame entero y se vuelve a pedir el ULTIMO, que es justo el que suele
        # venir corto o ilegible. MoviePy avisa ("bytes wanted but 0 bytes read")
        # y devuelve negro, asi que el congelado sostenia una pantalla en negro
        # durante todo el tramo sobrante.
        #
        # Paso de verdad con los graficos de Sabermetria a 480p15: la escena 1 se
        # quedaba a oscuras en el segundo 19. A 60 fps el fallo no aparecia porque
        # 0.05 s son tres frames, asi que llevaba escondido detras de otro error.
        #
        # 1.5 frames y no 1: con 1 exacto se cae en el borde entre dos frames y
        # el redondeo puede devolver otra vez el ultimo.
        fps = getattr(clip, "fps", None) or 25
        eps = max(config.VIDEO_FREEZE_EPSILON, 1.5 / fps)
        eps = min(eps, clip.duration / 2)
        last = clip.get_frame(max(clip.duration - eps, 0))
        # Un frame congelado en negro es un fallo MUDO: el render termina bien, el
        # mp4 se reproduce, y solo se descubre mirando el video en el segundo
        # exacto. Se comprueba aqui, que es donde todavia se puede decir algo.
        if float(last.max()) < 8:
            print(f"    [OJO] el frame congelado esta en NEGRO (clip a {fps:g} fps). "
                  f"El tramo sostenido va a salir a oscuras. Revisa el mp4 de "
                  f"origen: suele ser el ultimo frame ilegible.")

        hold = ImageClip(last).with_duration(duration - clip.duration)
        print(f"    (clip de {clip.duration:.1f}s < {duration:.1f}s: se congela "
              f"el ultimo frame {duration - clip.duration:.1f}s)")
        return concatenate_videoclips([clip, hold], method="chain")

    # -----------------------------------------------------------------------
    # RENDER FINAL
    # -----------------------------------------------------------------------
    def _render(self, clips: list, fps: int) -> None:
        """Concatena todos los subclips y escribe el final.mp4 en 1080p."""
        if not clips:
            raise RuntimeError("No hay escenas que renderizar.")

        # 1) Transicion ENTRE escenas (dip a negro) antes de concatenar.
        clips = self._apply_scene_transitions(clips)

        print(f"\nConcatenando {len(clips)} escenas y renderizando...")
        # method='chain' reproduce las escenas una tras otra SIN recomponer cada
        # frame sobre un lienzo. Es seguro porque todas nuestras escenas ya miden
        # exactamente 1920x1080, y es ~5x mas rapido que 'compose'. El crossfade
        # entre assets y el dip entre escenas se resuelven ANTES/DENTRO de cada
        # clip, no aqui, para no perder esta ventaja (ADR-012 + ADR-016).
        final = concatenate_videoclips(clips, method="chain")

        # 2) Fundidos globales (desde/hacia negro) del video completo.
        final = self._apply_global_fades(final)

        # 3) Cama musical opcional mezclada por encima de la narracion.
        final = self._add_music(final)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        final.write_videofile(
            str(self.output_path),
            fps=fps,
            codec=config.VIDEO_CODEC,
            audio_codec=config.AUDIO_CODEC,
            preset=config.FFMPEG_PRESET,
        )

        final.close()
        for clip in clips:
            clip.close()

        # El master se normaliza DESPUES, sobre el archivo ya escrito (ADR-036).
        self._normalizar_master()
        print(f"\nVideo final generado: {self.output_path}")

    # -----------------------------------------------------------------------
    # TRANSICIONES + MUSICA (ADR-016)
    # -----------------------------------------------------------------------
    def _apply_scene_transitions(self, clips: list) -> list:
        """Aplica el 'dip a negro' entre escenas consecutivas (si esta activo).

        Cada corte interno recibe un FadeOut al final de la escena saliente y un
        FadeIn al inicio de la entrante -> juntos forman un breve fundido a negro.
        La primera y la ultima escena NO se tocan aqui: sus bordes exteriores los
        cubren los fundidos globales. FadeIn/FadeOut son efectos de VIDEO: oscurecen
        la imagen pero no tocan el audio, asi la narracion nunca se corta.
        """
        if config.SCENE_TRANSITION != "dip" or len(clips) < 2:
            return clips

        n = len(clips)
        out = []
        for i, clip in enumerate(clips):
            # Acota el dip a 1/3 de la escena por si alguna fuera muy corta.
            d = min(config.DIP_DURATION, clip.duration / 3)
            effects = []
            if i != 0:
                effects.append(vfx.FadeIn(d))
            if i != n - 1:
                effects.append(vfx.FadeOut(d))
            out.append(clip.with_effects(effects) if effects else clip)
        return out

    def _apply_global_fades(self, final):
        """Fade-in desde negro al inicio y fade-out a negro al final del video."""
        effects = []
        if config.FADE_IN_DURATION > 0:
            effects.append(vfx.FadeIn(config.FADE_IN_DURATION))
        if config.FADE_OUT_DURATION > 0:
            effects.append(vfx.FadeOut(config.FADE_OUT_DURATION))
        return final.with_effects(effects) if effects else final

    def _inicio_de_escena(self, indice) -> Optional[float]:
        """Segundo del video en que arranca una escena, contando title cards.

        Las tarjetas no tienen audio pero SI ocupan tiempo: sin sumarlas, todo lo
        posterior queda desplazado.
        """
        if not indice:
            return None
        try:
            manifest = self._load_manifest()
        except FileNotFoundError:
            return None
        offset = 0.0
        for escena in manifest["scenes"]:
            if escena["index"] == indice:
                return offset
            if escena["type"] == "title_card":
                offset += config.TITLE_CARD_DURATION
            else:
                offset += float(escena.get("audio_duration") or 0.0)
        print(f"  [AVISO] la escena {indice} no existe; la pista de cierre se "
              f"anclara por su duracion.")
        return None

    def _medir_para_loudnorm(self, exe: str, filtro_base: str) -> Optional[dict]:
        """Primera pasada: mide el master entero y devuelve las cifras de loudnorm.

        Solo mide, no escribe nada ('-f null'), y solo lee el audio ('-vn'), asi
        que sobre un video de catorce minutos cuesta segundos, no un render.

        Devuelve None ante cualquier problema. Eso es deliberado: quien llama cae
        entonces a la pasada unica de siempre, que es el comportamiento que ya
        estaba probado. Una mejora de sonido no puede tumbar un render.
        """
        try:
            r = subprocess.run(
                [exe, "-hide_banner", "-nostats", "-y",
                 "-i", str(self.output_path),
                 "-vn",
                 "-af", f"{filtro_base}:print_format=json",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=900,
            )
        except (OSError, subprocess.SubprocessError) as e:
            print(f"  [AVISO] no se pudo medir para la doble pasada ({e}); "
                  f"se normaliza en una sola.")
            return None

        # loudnorm escribe su JSON en stderr, al final y entre llaves. Se busca el
        # ULTIMO bloque: ffmpeg imprime antes sus propios avisos, y quedarse con
        # el primer '{' que aparezca es como se rompe esto en cuanto ffmpeg
        # cambie de version.
        salida = r.stderr or ""
        ini, fin = salida.rfind("{"), salida.rfind("}")
        if ini == -1 or fin == -1 or fin < ini:
            print("  [AVISO] la medicion no devolvio JSON; se normaliza en una sola pasada.")
            return None
        try:
            datos = json.loads(salida[ini:fin + 1])
        except ValueError:
            print("  [AVISO] no se pudo leer la medicion; se normaliza en una sola pasada.")
            return None

        claves = ("input_i", "input_lra", "input_tp", "input_thresh", "target_offset")
        if not all(k in datos for k in claves):
            print("  [AVISO] la medicion vino incompleta; se normaliza en una sola pasada.")
            return None
        # '-inf' aparece cuando el tramo medido es silencio: con eso loudnorm no
        # puede calcular nada y hay que caer a la pasada unica.
        if any("inf" in str(datos[k]).lower() for k in claves):
            print("  [AVISO] la medicion dio valores infinitos (audio mudo?); "
                  "se normaliza en una sola pasada.")
            return None
        return datos

    def _normalizar_master(self) -> None:
        """Normaliza la sonoridad del mp4 YA ESCRITO, en una pasada aparte (ADR-036).

        Por que una pasada aparte y no un filtro dentro de write_videofile: MoviePy
        escribe el audio a un temporal y luego lo MUXEA con '-c:a copy'. El filtro
        llegaba en esa segunda fase, y ffmpeg no puede filtrar y hacer streamcopy a
        la vez ("Filtering and streamcopy cannot be used together"). El render moria
        despues de haber generado el audio, tirando el trabajo entero.

        Hacerlo despues resulta ser mejor por dos motivos que la version original no
        tenia:
          - El video NO se recomprime ('-c:v copy'): solo se recodifica el audio, asi
            que cuesta segundos en vez de otro render completo.
          - Si esto falla, el mp4 ya existe y es reproducible. Lo peor que puede
            pasar es que quede con el volumen sin normalizar, no que se pierdan los
            quince minutos de render.
        """
        if not config.AUDIO_NORMALIZE:
            return
        if not self.output_path.exists():
            return

        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            print("  [AVISO] no se encontro ffmpeg; el master queda sin normalizar.")
            return

        base = (f"loudnorm=I={config.MASTER_TARGET_LUFS}"
                f":TP={config.MASTER_TRUE_PEAK_DB}"
                f":LRA={config.MASTER_LRA}")

        filtro = base
        if getattr(config, "MASTER_DOS_PASADAS", False):
            medido = self._medir_para_loudnorm(exe, base)
            if medido:
                # 'linear=true' pide ganancia LINEAL: sin compresor. ffmpeg la
                # aplica solo si cabe bajo el techo de true peak; si no cabe,
                # vuelve a dinamico por su cuenta y lo dice en el aviso de abajo.
                filtro = (
                    f"{base}"
                    f":measured_I={medido['input_i']}"
                    f":measured_LRA={medido['input_lra']}"
                    f":measured_TP={medido['input_tp']}"
                    f":measured_thresh={medido['input_thresh']}"
                    f":offset={medido['target_offset']}"
                    f":linear=true:print_format=summary"
                )
                ganancia = config.MASTER_TARGET_LUFS - float(medido["input_i"])
                margen = config.MASTER_TRUE_PEAK_DB - (float(medido["input_tp"]) + ganancia)
                print(f"  Medido: {float(medido['input_i']):.1f} LUFS, "
                      f"pico {float(medido['input_tp']):.1f} dBTP. "
                      f"Ganancia necesaria: {ganancia:+.1f} dB.")
                if margen < 0:
                    print(f"  [OJO] no cabe por {abs(margen):.1f} dB bajo el techo: "
                          f"ffmpeg va a comprimir igualmente. La voz no ganara "
                          f"dinamica; baja MASTER_TARGET_LUFS si quieres evitarlo.")
                else:
                    print(f"  Cabe con {margen:.1f} dB de margen: ganancia lineal, "
                          f"sin compresor.")

        temporal = self.output_path.with_name(self.output_path.stem + "_norm.mp4")

        print(f"  Normalizando el master a {config.MASTER_TARGET_LUFS} LUFS "
              f"(techo {config.MASTER_TRUE_PEAK_DB} dBTP)...")
        try:
            r = subprocess.run(
                [exe, "-hide_banner", "-loglevel", "error", "-y",
                 "-i", str(self.output_path),
                 "-c:v", "copy",                       # el video no se toca
                 "-af", filtro,
                 "-c:a", config.AUDIO_CODEC, "-b:a", "192k",
                 str(temporal)],
                capture_output=True, text=True, timeout=900,
            )
        except (OSError, subprocess.SubprocessError) as e:
            print(f"  [AVISO] fallo la normalizacion ({e}); el video queda con el "
                  f"volumen de la mezcla, sin normalizar.")
            temporal.unlink(missing_ok=True)
            return

        if r.returncode != 0 or not temporal.exists():
            print(f"  [AVISO] fallo la normalizacion; el video queda sin normalizar.")
            if r.stderr.strip():
                print(f"          {r.stderr.strip().splitlines()[-1][:160]}")
            temporal.unlink(missing_ok=True)
            return

        # os.replace es atomico: o esta el nuevo o esta el viejo, nunca a medias.
        #
        # EN WINDOWS PUEDE FALLAR AUNQUE TODO HAYA IDO BIEN. El sistema no deja
        # sustituir un archivo que alguien tenga abierto, y sobre un mp4 recien
        # escrito hay varios candidatos a tenerlo cogido unos segundos: el
        # antivirus escaneandolo, el indexador, la vista previa del explorador, o
        # el propio reproductor si te quedaste viendo el render anterior.
        #
        # Casi siempre es transitorio, asi que se reintenta. Y si no cede, NO se
        # borra nada: el trabajo esta hecho y el archivo normalizado existe. Lo
        # unico que falta es el nombre, y eso se arregla renombrando a mano. Tirar
        # un render de quince minutos por un bloqueo de dos segundos seria absurdo.
        for intento in range(5):
            try:
                os.replace(str(temporal), str(self.output_path))
                break
            except PermissionError:
                if intento == 4:
                    print(f"  [AVISO] Windows no deja sustituir el archivo: "
                          f"alguien lo tiene abierto (reproductor, antivirus...).")
                    print(f"          El video normalizado SI se genero y esta en:")
                    print(f"            {temporal.resolve()}")
                    print(f"          Cierra lo que lo tenga abierto y renombralo, "
                          f"o vuelve a correr el ensamblador.")
                    return
                time.sleep(1.5)

        medido = medir_lufs(self.output_path)
        if medido is not None:
            print(f"  Master normalizado: {medido:.1f} LUFS")

    def _lufs_de_la_voz(self) -> Optional[float]:
        """Sonoridad del conjunto de la narracion, midiendo los mp3 de las escenas.

        Se mide la VOZ y no la mezcla porque la voz es la referencia: la musica se
        coloca respecto a ella. Se cachea: son 21 llamadas a ffmpeg y el valor no
        cambia entre la cama y la pista de cierre.
        """
        if getattr(self, "_voz_lufs_cache", "sin_medir") != "sin_medir":
            return self._voz_lufs_cache

        medidas = []
        # El manifest no se guarda como atributo en esta clase: se relee cuando hace
        # falta (igual que en _inicio_de_escena). Se lee UNA vez aqui gracias al
        # cache de abajo, que es lo que evita repetir 21 mediciones por pista.
        for escena in self._load_manifest().get("scenes", []):
            rel = escena.get("audio_file")
            dur = escena.get("audio_duration")
            if not rel or not dur:
                continue
            ruta = self.manifest_path.parent / rel
            if ruta.exists():
                medidas.append((medir_lufs(ruta), dur))

        self._voz_lufs_cache = _combinar_lufs(medidas)
        return self._voz_lufs_cache

    def _ganancia_musica(self, pista: Path, debajo_db: float) -> float:
        """Multiplicador para que esta pista quede 'debajo_db' por debajo de la voz.

        Si la medicion falla por lo que sea (ffmpeg ausente, archivo raro), se cae
        al multiplicador fijo de siempre en vez de dejar el video sin musica o con
        la musica a todo volumen. Un valor conservador conocido es mejor que un
        calculo a medias.
        """
        if not config.AUDIO_NORMALIZE:
            return config.MUSIC_VOLUME

        voz = self._lufs_de_la_voz()
        mus = medir_lufs(pista)
        if voz is None or mus is None:
            print(f"    [AVISO] no se pudo medir la sonoridad de {pista.name}; "
                  f"se usa el volumen fijo {config.MUSIC_VOLUME}.")
            return config.MUSIC_VOLUME

        objetivo = voz - debajo_db
        ganancia = 10 ** ((objetivo - mus) / 20.0)
        print(f"    voz {voz:.1f} LUFS | {pista.name} {mus:.1f} LUFS "
              f"-> objetivo {objetivo:.1f} ({debajo_db:.0f} dB por debajo), "
              f"ganancia x{ganancia:.4f}")
        return ganancia

    def _add_music(self, final):
        """Mezcla una cama musical (opcional) por encima de la narracion.

        Busca MUSIC_FILENAME en la carpeta del proyecto (junto al manifest). Si no
        existe, devuelve el video sin tocar. Si existe: la ajusta a la duracion del
        video (loop si es corta, recorte si es larga), le baja el volumen y le pone
        fade in/out, y la superpone al audio ya existente con un CompositeAudioClip.
        """
        music_path = self.manifest_path.parent / config.MUSIC_FILENAME
        if not music_path.exists():
            print("  (sin musica de fondo: no se encontro "
                  f"{config.MUSIC_FILENAME} en la carpeta del proyecto)")
            return final

        # El volumen ya no sale de aqui: lo calcula _ganancia_musica midiendo la
        # pista, y lo imprime ella. Anunciar config.MUSIC_VOLUME en esta linea era
        # mentir en el log, que es peor que no decir nada.
        print(f"  Musica de fondo: {music_path.name} "
              f"(fade {config.MUSIC_FADE:.0f}s)")
        music = AudioFileClip(str(music_path))
        target = final.duration

        if music.duration < target:
            music = music.with_effects([afx.AudioLoop(duration=target)])
        else:
            music = music.subclipped(0, target)

        # Pista de cierre (ADR-034): si existe, se ancla al FINAL del video y la
        # cama principal se desvanece para dejarle sitio. Cambiar el score en el
        # climax es tecnica estandar de documental.
        final_path = self.manifest_path.parent / config.MUSIC_FINAL_FILENAME
        cierre = None
        if final_path.exists():
            pista = AudioFileClip(str(final_path))
            # Cuanto tiene que sonar: desde que arranca la escena indicada hasta
            # el final del video. Si no se indica escena, se ancla por la propia
            # duracion de la pista.
            arranque = self._inicio_de_escena(config.MUSIC_FINAL_FROM_SCENE)
            if arranque is None:
                arranque = max(0.0, target - min(pista.duration, target))
            necesario = max(0.1, target - arranque)

            if config.MUSIC_FINAL_USAR_COLA and pista.duration > necesario:
                # La COLA de la pista, no su principio: es donde esta el remate
                # por el que la elegiste.
                cierre = pista.subclipped(pista.duration - necesario, pista.duration)
            else:
                cierre = pista.subclipped(0, min(pista.duration, necesario))
            dur_cierre = cierre.duration
            arranque = max(0.0, target - dur_cierre)   # que termine con el video
            cierre = cierre.with_effects([
                afx.MultiplyVolume(
                    self._ganancia_musica(final_path, config.MUSIC_FINAL_BELOW_VOICE_DB)),
                afx.AudioFadeIn(min(config.MUSIC_FINAL_CROSSFADE, dur_cierre / 2)),
                afx.AudioFadeOut(min(config.MUSIC_FADE, dur_cierre / 2)),
            ]).with_start(arranque)
            # La cama se corta donde entra el cierre, con solape para que se
            # enlacen en vez de dar un salto.
            corte = min(target, arranque + config.MUSIC_FINAL_CROSSFADE)
            music = music.subclipped(0, corte)
            trozo = "cola" if config.MUSIC_FINAL_USAR_COLA else "principio"
            # El volumen no se anuncia aqui: lo calcula e imprime _ganancia_musica.
            print(f"  Pista de cierre: {final_path.name} — {trozo} de "
                  f"{pista.duration:.1f}s, entra en {arranque:.1f}s "
                  f"y dura {dur_cierre:.1f}s")

        music = music.with_effects([
            afx.MultiplyVolume(self._ganancia_musica(music_path, config.MUSIC_BELOW_VOICE_DB)),
            afx.AudioFadeIn(config.MUSIC_FADE),
            afx.AudioFadeOut(config.MUSIC_FINAL_CROSSFADE if cierre else config.MUSIC_FADE),
        ])

        capas = [final.audio] if final.audio else []
        capas.append(music)
        if cierre is not None:
            capas.append(cierre)
        mixed = CompositeAudioClip(capas) if len(capas) > 1 else capas[0]
        return final.with_audio(mixed)


def medir_lufs(path: Path) -> Optional[float]:
    """Sonoridad integrada de un archivo de audio, en LUFS. None si no se puede.

    LUFS mide volumen PERCIBIDO (pondera las frecuencias como las oye el oido),
    que es lo que hace falta para mezclar voz contra musica: dos pistas al mismo
    LUFS suenan igual de fuertes aunque sus formas de onda no se parezcan.

    Se usa el ffmpeg que ya trae imageio (dependencia de MoviePy) para no exigir
    una instalacion aparte en la maquina de nadie.
    """
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
    try:
        r = subprocess.run(
            [exe, "-hide_banner", "-nostats", "-i", str(path),
             "-af", "loudnorm=print_format=json", "-f", "null", "-"],
            capture_output=True, text=True, timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None
    try:
        v = float(json.loads(m[-1])["input_i"])
    except (ValueError, KeyError):
        return None
    return None if v < -70 else v      # -inf: pista en silencio


def _combinar_lufs(medidas: list) -> Optional[float]:
    """Sonoridad del conjunto de varias pistas, ponderada por duracion.

    La sonoridad es energia media, asi que no se promedian los decibelios: se
    pasan a energia lineal, se promedia pesando por duracion, y se vuelve.
    """
    utiles = [(l, d) for l, d in medidas if l is not None and d and d > 0]
    if not utiles:
        return None
    total = sum(d for _, d in utiles)
    energia = sum(d * (10 ** (l / 10.0)) for l, d in utiles) / total
    return 10 * math.log10(energia) if energia > 0 else None


def _should_freeze(path: Path) -> bool:
    """True si este archivo debe CONGELAR su ultimo frame en vez de repetirse.

    Se decide por el nombre (config.VIDEO_FREEZE_MARKERS): asi el guion y el
    pipeline no necesitan saber que hay dentro del video, basta con nombrarlo
    bien. Ver ADR-022.
    """
    name = str(path).lower()
    return any(m.lower() in name for m in config.VIDEO_FREEZE_MARKERS)


def _quitar_fondo_plano(img: Image.Image) -> Image.Image:
    """Vuelve transparente el fondo uniforme de un logo, si lo tiene (ADR-028).

    El problema: un logo descargado suele traer fondo blanco HORNEADO, sin canal
    alfa. Aplanarlo sobre el gris de marca lo dejaria igual de blanco, y sobre el
    negro del video eso es un fogonazo.

    El metodo es un relleno DESDE LOS BORDES hacia dentro, no una sustitucion por
    color global. Esa distincion importa: un logo blanco sobre fondo blanco no se
    borra a si mismo, porque su interior no toca el borde.

    Es conservador a proposito. Solo actua si el borde es casi de un solo color
    -una fotografia real nunca lo es-, y se echa atras si lo detectado es
    demasiado poco (no compensa) o demasiado (algo salio mal). Ante la duda, no
    toca nada: es preferible un logo con fondo que una foto agujereada.
    """
    if not config.LOGO_BG_REMOVE:
        return img
    if img.mode in ("RGBA", "LA") and img.getchannel("A").getextrema()[0] < 255:
        return img  # ya trae transparencia propia: se respeta

    rgb = img.convert("RGB")
    a = np.asarray(rgb).astype(np.int16)
    h, w, _ = a.shape
    if h < 8 or w < 8:
        return img

    # ¿Es el borde de un solo color? Si no, no es un logo recortable.
    borde = np.concatenate([a[0, :, :], a[-1, :, :], a[:, 0, :], a[:, -1, :]])
    if float(borde.std(axis=0).max()) > config.LOGO_BG_EDGE_STD_MAX:
        return img
    color = borde.mean(axis=0)

    # Relleno por inundacion desde los bordes (BFS iterativo sobre la mascara de
    # "parecido al color de fondo"), para no invadir zonas interiores del logo.
    parecido = (np.abs(a - color).max(axis=2) <= config.LOGO_BG_TOLERANCE)
    fondo = np.zeros((h, w), dtype=bool)
    from collections import deque
    cola = deque()
    for x in range(w):
        for y in (0, h - 1):
            if parecido[y, x] and not fondo[y, x]:
                fondo[y, x] = True
                cola.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if parecido[y, x] and not fondo[y, x]:
                fondo[y, x] = True
                cola.append((y, x))
    while cola:
        y, x = cola.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and parecido[ny, nx] and not fondo[ny, nx]:
                fondo[ny, nx] = True
                cola.append((ny, nx))

    ratio = float(fondo.mean())
    if not (config.LOGO_BG_MIN_RATIO <= ratio <= config.LOGO_BG_MAX_RATIO):
        return img

    salida = np.dstack([np.asarray(rgb), np.where(fondo, 0, 255).astype(np.uint8)])
    print(f"    (fondo plano detectado y eliminado: {ratio * 100:.0f}% de la imagen)")
    out = Image.fromarray(salida, mode="RGBA")
    out.info["logo_recortado"] = True   # lo lee el encaje: un logo no lleva blur
    return out

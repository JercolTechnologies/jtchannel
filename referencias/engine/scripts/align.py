# -*- coding: utf-8 -*-
# Ruta: engine/scripts/align.py
#
# MODULO OPCIONAL - Alineacion forzada de marcadores (ADR-018).
# Convierte los marcadores <<slot|...>> del guion en SEGUNDOS EXACTOS, para que
# cada asset entre justo cuando la voz lo menciona. Escribe start/end/duration en
# cada 'shot' del manifest; luego el assembler los coloca con corte preciso.
#
# Como obtiene los tiempos (plomeria "opcion 1", torch NO obligatorio):
#   1. Si existe audio/NN_audio.json (lista {palabra,inicio,fin}), lo usa tal cual.
#      Es el formato que produce tu propio timestamps.py con whisper local.
#   2. Si no existe y 'openai-whisper' esta instalado, lo genera y lo cachea.
#   3. Si no hay ninguno, avisa y deja el shot sin timing (el assembler cae a
#      reparto igual para esa escena).
#
# Punto fino: whisper TRANSCRIBE (puede escribir mal una palabra, "Egocio"...),
# pero aqui SOLO usamos sus TIEMPOS. El texto de cada shot sale de TU guion: se
# empareja tu secuencia de palabras (la correcta) con la de whisper por posicion
# (difflib) y se toma el segundo. Los errores de whisper nunca llegan al manifest.

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

try:
    from . import config
except ImportError:  # ejecucion directa
    import config


class TimestampAligner:
    """Rellena el timing de los 'shots' de cada escena narrada del manifest."""

    def __init__(self, manifest_path: Path, audio_dir: Path):
        self.manifest_path = Path(manifest_path)
        self.audio_dir = Path(audio_dir)

    # -----------------------------------------------------------------------
    # ORQUESTACION
    # -----------------------------------------------------------------------
    def run(self, only: Optional[set] = None, overwrite: bool = False) -> dict:
        """Alinea los shots de las escenas narradas y guarda el manifest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"No existe el manifest: {self.manifest_path}. Corre primero el parser."
            )
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        alineadas = 0
        for scene in manifest["scenes"]:
            if scene.get("type") != "narrated" or not (scene.get("shots") or scene.get("overlays")):
                continue
            if only is not None and scene["index"] not in only:
                continue

            idx = scene["index"]
            duration = scene.get("audio_duration")
            if not duration:
                print(f"  Escena {idx:02d}: sin audio_duration (corre 'tts' antes). Se omite.")
                continue

            words = self._load_words(idx, overwrite=overwrite)
            if words is None:
                print(f"  Escena {idx:02d}: sin timestamps y sin whisper; se deja "
                      f"para reparto igual.")
                continue

            self._align_scene(scene, words, duration)
            alineadas += 1

        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nAlineacion lista. Escenas con shots alineados: {alineadas}.")
        return manifest

    # -----------------------------------------------------------------------
    # ORIGEN DE LOS TIMESTAMPS
    # -----------------------------------------------------------------------
    def _load_words(self, index: int, overwrite: bool) -> Optional[list]:
        """Devuelve la lista de palabras {palabra,inicio,fin} de una escena.

        Prioridad: JSON cacheado -> generar con whisper local (si esta) -> None.
        """
        json_path = self.audio_dir / f"{index:02d}_audio{config.ALIGN_JSON_SUFFIX}"
        if json_path.exists() and not overwrite:
            return self._normalize_words(json.loads(json_path.read_text(encoding="utf-8")))

        mp3_path = self.audio_dir / f"{index:02d}_audio.mp3"
        if not mp3_path.exists():
            return None

        words = self._whisper_words(mp3_path)
        if words is None:
            return None
        json_path.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
        return words

    @staticmethod
    def _whisper_words(mp3_path: Path) -> Optional[list]:
        """Genera timestamps por palabra con whisper local (import diferido/opcional)."""
        try:
            import whisper  # openai-whisper (opcional; no esta en requirements)
        except ImportError:
            return None
        print(f"    (whisper local: transcribiendo {mp3_path.name} para timestamps...)")
        model = whisper.load_model(config.WHISPER_MODEL)
        result = model.transcribe(
            str(mp3_path), word_timestamps=True, language=config.WHISPER_LANGUAGE
        )
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words.append({
                    "palabra": (w.get("word") or "").strip(),
                    "inicio": w.get("start"),
                    "fin": w.get("end"),
                })
        return words

    @staticmethod
    def _normalize_words(data) -> list:
        """Acepta varios formatos de JSON y devuelve lista {palabra,inicio,fin}."""
        if isinstance(data, dict) and "words" in data:
            data = data["words"]
        if isinstance(data, dict) and "segments" in data:
            flat = []
            for seg in data.get("segments", []):
                for w in seg.get("words", []):
                    flat.append({
                        "palabra": (w.get("word") or "").strip(),
                        "inicio": w.get("start"),
                        "fin": w.get("end"),
                    })
            return flat
        out = []
        for w in data:  # lista de dicts (tu formato o el crudo de whisper)
            out.append({
                "palabra": (w.get("palabra") or w.get("word") or "").strip(),
                "inicio": w.get("inicio", w.get("start")),
                "fin": w.get("fin", w.get("end")),
            })
        return out

    # -----------------------------------------------------------------------
    # EMPAREJADO MARCADOR -> SEGUNDO
    # -----------------------------------------------------------------------
    def _align_scene(self, scene: dict, words: list, duration: float) -> None:
        """Fija el timing de shots (start/end/duration) y overlays (start) por word_index."""
        idx = scene["index"]

        # Tokenizacion EXPANDIDA (ADR-033). Nuestro texto y el de Whisper no cortan
        # las palabras igual: el guion escribe "seven-point-six-billion-dollar" como
        # UNA palabra y Whisper oye CINCO ("seven point six billion dollar"). Con
        # _norm a secas eso da un token que no casa con nada, el marcador se queda
        # sin ancla, y el respaldo de vecindad le roba el segundo al plano de al
        # lado: dos planos en el mismo instante y uno de 0.00s. Partiendo por guion
        # y barra antes de comparar, cada pieza casa con su palabra de Whisper.
        #
        # 'duenos' guarda a que palabra ORIGINAL pertenece cada pieza, porque los
        # word_index de los marcadores los puso el parser sobre .split() y tienen
        # que seguir apuntando a lo mismo.
        our_tokens: list[str] = []
        duenos: list[int] = []
        for i_orig, bruto in enumerate((scene.get("audio_text") or "").split()):
            piezas = [p for p in re.split(r"[-\u2010-\u2015/]", bruto) if self._norm(p)]
            for pieza in (piezas or [bruto]):
                our_tokens.append(self._norm(pieza))
                duenos.append(i_orig)

        # Primera pieza de cada palabra original: es donde empieza a sonar.
        primera_pieza: dict[int, int] = {}
        for pos, orig in enumerate(duenos):
            primera_pieza.setdefault(orig, pos)

        wh_tokens = [self._norm(w["palabra"]) for w in words]
        wh_starts = [w["inicio"] for w in words]

        # Mapa pieza_nuestra -> palabra_whisper por bloques coincidentes (difflib).
        o2w = {}
        sm = SequenceMatcher(a=our_tokens, b=wh_tokens, autojunk=False)
        for block in sm.get_matching_blocks():
            for k in range(block.size):
                o2w[block.a + k] = block.b + k

        total_piezas = max(len(our_tokens), 1)

        def time_of_word(our_idx: int, label: str) -> float:
            """Segundo en que empieza la palabra our_idx del texto original.

            Si esa palabra no anclo, se acepta una VECINA CERCANA (hasta
            MAX_ANCLA_VECINA piezas). El limite es el punto: antes la busqueda
            recorria la escena entera, asi que un fallo de alineacion terminaba
            devolviendo la palabra donde arranca el plano SIGUIENTE — silenciosamente,
            porque tecnicamente habia encontrado un ancla. Con el limite, un fallo
            se degrada a estimacion por proporcion y AVISA, que es ruidoso pero
            honesto.
            """
            base = primera_pieza.get(our_idx)
            if base is None:  # marcador al final del texto
                base = min(our_idx, total_piezas - 1)

            for d in range(config.MAX_ANCLA_VECINA + 1):
                for cand in (base + d, base - d):
                    w = o2w.get(cand)
                    if w is not None and 0 <= w < len(wh_starts) and wh_starts[w] is not None:
                        return float(wh_starts[w])

            t = round(duration * (base / total_piezas), 3)
            print(f"  [AVISO] Escena {idx:02d} {label}: no se pudo alinear con el audio; "
                  f"estimado por proporcion en {t:.1f}s.")
            return t

        # --- SHOTS: se reparten para llenar la escena (cada uno hasta el siguiente) ---
        shots = scene.get("shots")
        if shots:
            starts = [0.0]  # la primera toma abre la escena
            for shot in shots[1:]:
                starts.append(time_of_word(shot["word_index"], f"shot '{shot['slot']}'"))
            starts = [min(max(s, 0.0), duration) for s in starts]
            for i in range(1, len(starts)):
                starts[i] = max(starts[i], starts[i - 1])  # monotono creciente
            for i, shot in enumerate(shots):
                start = starts[i]
                end = starts[i + 1] if i + 1 < len(shots) else duration
                shot["start"] = round(start, 3)
                shot["end"] = round(end, 3)
                shot["duration"] = round(end - start, 3)
                if shot["duration"] < config.SHOT_MIN_DURATION_WARN:
                    print(f"  [AVISO] Escena {idx:02d} shot '{shot['slot']}': dura solo "
                          f"{shot['duration']:.2f}s (marcadores muy juntos).")
            print(f"  Escena {idx:02d}: {len(shots)} shots -> "
                  + ", ".join(f"{s['slot']}={s['start']:.1f}s" for s in shots))

        # --- OVERLAYS: cada uno entra en su segundo y dura lo suyo (no se reparten) ---
        overlays = scene.get("overlays")
        if overlays:
            for ov in overlays:
                label = f"overlay '{(ov.get('content') or '')[:20]}'"
                start = min(max(time_of_word(ov["word_index"], label), 0.0), duration)
                dur = ov.get("duration") or config.OVERLAY_DEFAULT_DURATION
                ov["start"] = round(start, 3)
                ov["duration"] = round(min(dur, max(0.0, duration - start)), 3)  # no excede la escena
            print(f"  Escena {idx:02d}: {len(overlays)} overlays -> "
                  + ", ".join(f"\"{(o.get('content') or '')[:12]}\"@{o['start']:.1f}s" for o in overlays))

    @staticmethod
    def _norm(token: str) -> str:
        """Normaliza una palabra para comparar: sin tildes, minusculas, solo alfanumerico."""
        t = unicodedata.normalize("NFKD", token)
        t = "".join(c for c in t if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]", "", t.lower())

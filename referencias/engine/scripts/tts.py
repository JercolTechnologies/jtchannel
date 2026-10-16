# -*- coding: utf-8 -*-
# Ruta: engine/scripts/tts.py
#
# MODULO 2 - Generador de Voces (OpenAI Text-to-Speech).
# Toma las escenas "narrated" del manifest, envia su texto a la API de OpenAI
# (modelo tts-1-hd, voz onyx) y guarda los audios como 01_audio.mp3, 02_audio.mp3...
#
# Reglas del brief:
#   - Limite duro de 4096 caracteres por peticion -> se maneja con chunking
#     defensivo (aunque los bloques del guion siempre son cortos).
#   - Los audios se guardan secuencialmente, numerados por indice de escena.
# Ademas escribe de vuelta la duracion real de cada audio en el manifest, para
# que puedas previsualizar los tiempos antes de ensamblar.

import json
import os
import re
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

try:
    from . import config
except ImportError:
    import config


# Modelos que aceptan el parametro 'speed' del endpoint /v1/audio/speech.
#
# NO es una lista de canales ni de preferencias: es una CAPACIDAD DEL MODELO. La
# diferencia importa. 'tts-1' y 'tts-1-hd' regulan el ritmo con 'speed'; los
# modelos construidos sobre un LLM lo regulan con 'instructions', en prosa.
# Mandar el parametro que no toca es un error de API.
#
# Se consulta el modelo, nunca el canal. Un 'if canal == "x"' aqui dentro seria
# el motor ramificandose por canal, que es justo lo que ADR-037 vino a evitar.
MODELOS_CON_SPEED = {"tts-1", "tts-1-hd"}


class VoiceGenerator:
    """Genera los archivos de voz de un proyecto a partir de su manifest.json."""

    def __init__(self, manifest_path: Path, audio_dir: Path, speed: float | None = None):
        self.manifest_path = Path(manifest_path)
        self.audio_dir = Path(audio_dir)
        # Velocidad de la voz: la de --speed si se paso, si no la de config.
        self.speed = speed if speed is not None else config.TTS_SPEED
        self.modelo = config.TTS_MODEL
        self.instrucciones = getattr(config, "TTS_INSTRUCTIONS", None)
        self.client = self._init_client()
        self._avisar_de_los_parametros_ignorados()

    def _avisar_de_los_parametros_ignorados(self) -> None:
        """Dice en voz alta que parametro no se va a mandar, y por que.

        Un parametro que se ignora en silencio es una regresion invisible: se
        pide velocidad 1.15, no pasa nada, y nadie se entera hasta escuchar doce
        minutos de audio. Preferimos ruido en la terminal a una sorpresa en el mp3.
        """
        acepta_speed = self.modelo in MODELOS_CON_SPEED
        if not acepta_speed and self.speed != 1.0:
            print(f"[AVISO] '{self.modelo}' no acepta 'speed'; se ignora "
                  f"velocidad {self.speed}. Pide el ritmo en voz.instrucciones.")
        if acepta_speed and self.instrucciones:
            print(f"[AVISO] '{self.modelo}' no acepta 'instructions'; se ignora "
                  f"voz.instrucciones del canal.json.")

    def _init_client(self) -> OpenAI:
        """Carga la API key desde engine/.env y crea el cliente de OpenAI."""
        load_dotenv(config.ENV_FILE)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                f"Falta OPENAI_API_KEY. Crea el archivo {config.ENV_FILE} "
                f"(basado en engine/.env.example) con tu clave."
            )
        return OpenAI(api_key=api_key)

    def _load_manifest(self) -> dict:
        """Lee el manifest.json del proyecto."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"No existe el manifest: {self.manifest_path}. Corre primero el parser."
            )
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _save_manifest(self, manifest: dict) -> None:
        """Guarda el manifest actualizado (con las duraciones de audio)."""
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def _split_text(text: str, limit: int) -> list[str]:
        """Divide un texto largo en trozos <= limit, cortando en fin de oracion.

        Solo se activa si un bloque supera el limite de la API (caso raro en este
        guion). Corta preferentemente tras '. ', '! ' o '? ' para no partir frases.
        """
        if len(text) <= limit:
            return [text]

        # Separamos por oraciones conservando el signo de puntuacion.
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks, current = [], ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= limit:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    chunks.append(current)
                # Si una sola oracion excede el limite, se trocea a la fuerza.
                if len(sentence) > limit:
                    for i in range(0, len(sentence), limit):
                        chunks.append(sentence[i:i + limit])
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append(current)
        return chunks

    def _synthesize(self, text: str, out_path: Path) -> None:
        """Envia el texto a OpenAI TTS y escribe el mp3 resultante en out_path.

        Si el texto excede el limite de la API, se sintetiza por trozos y se
        concatenan los audios en un solo mp3 (usando moviepy solo en ese caso).
        """
        chunks = self._split_text(text, config.TTS_CHAR_LIMIT)

        if len(chunks) == 1:
            self._synthesize_chunk(chunks[0], out_path)
            return

        # Caso poco comun: multiples trozos -> se generan y luego se concatenan.
        print(f"    (texto largo: {len(text)} chars -> {len(chunks)} peticiones)")
        part_paths = []
        for i, chunk in enumerate(chunks, start=1):
            part = out_path.with_name(f"{out_path.stem}_part{i}{out_path.suffix}")
            self._synthesize_chunk(chunk, part)
            part_paths.append(part)
        self._concatenate_audio(part_paths, out_path)
        for part in part_paths:  # limpieza de temporales
            part.unlink(missing_ok=True)

    def _synthesize_chunk(self, text: str, out_path: Path) -> None:
        """Genera un unico mp3 (un trozo) via streaming a disco.

        'speed' e 'instructions' son EXCLUYENTES y dependen del modelo, no del
        canal: cada uno se manda solo donde existe (ver MODELOS_CON_SPEED).
        """
        extra = {}
        if self.modelo in MODELOS_CON_SPEED:
            extra["speed"] = self.speed
        elif self.instrucciones:
            extra["instructions"] = self.instrucciones

        with self.client.audio.speech.with_streaming_response.create(
            model=self.modelo,
            voice=config.TTS_VOICE,
            input=text,
            response_format=config.TTS_FORMAT,
            **extra,
        ) as response:
            response.stream_to_file(out_path)

    @staticmethod
    def _concatenate_audio(parts: list[Path], out_path: Path) -> None:
        """Une varios mp3 en uno solo (import diferido de moviepy: solo si hace falta)."""
        from moviepy import AudioFileClip, concatenate_audioclips

        clips = [AudioFileClip(str(p)) for p in parts]
        final = concatenate_audioclips(clips)
        final.write_audiofile(str(out_path), logger=None)
        for clip in clips:
            clip.close()
        final.close()

    @staticmethod
    def _measure_duration(path: Path) -> float:
        """Devuelve la duracion en segundos de un mp3 (import diferido de moviepy)."""
        from moviepy import AudioFileClip

        clip = AudioFileClip(str(path))
        duration = clip.duration
        clip.close()
        return round(duration, 3)

    def generate(self, overwrite: bool = False, only: set[int] | None = None) -> dict:
        """Genera el audio de las escenas narradas y actualiza el manifest.

        overwrite=False -> respeta audios ya existentes (no regenera ni regasta API).
        only=None        -> procesa todas las escenas narradas.
        only={1, 2, 3}   -> procesa solo esas escenas (util para pruebas baratas).
        """
        manifest = self._load_manifest()
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        for scene in manifest["scenes"]:
            if scene["type"] != "narrated":
                continue  # las title cards no llevan voz
            if only is not None and scene["index"] not in only:
                continue  # fuera del subconjunto pedido para esta corrida

            out_path = self.audio_dir / f"{scene['index']:02d}_audio.mp3"

            if out_path.exists() and not overwrite:
                print(f"  Escena {scene['index']:02d}: audio ya existe, se omite.")
            else:
                print(f"  Escena {scene['index']:02d}: generando voz...")
                self._synthesize(scene["audio_text"], out_path)

            # Guardamos ruta y duracion en el manifest (siempre, exista o no).
            scene["audio_file"] = f"audio/{out_path.name}"
            scene["audio_duration"] = self._measure_duration(out_path)

        self._save_manifest(manifest)
        total = sum(s.get("audio_duration") or 0 for s in manifest["scenes"])
        print(f"\nAudios listos. Duracion total narrada: ~{total:.1f}s ({total/60:.1f} min).")
        return manifest

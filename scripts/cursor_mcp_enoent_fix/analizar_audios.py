# -*- coding: utf-8 -*-
"""
Análisis forense de tiempos de palabra y silencios de los 3 audios TTS de Video 03
para aplicar la Regla 11 bis (cola de 1.0 a 1.2 segundos tras la última palabra hablada).
"""

import json
import re
import subprocess
from pathlib import Path
import whisper

AUDIOS_DIR = Path("output/cursor_mcp_enoent_fix/audios")


def medir_silencedetect(ruta: Path) -> float:
    """Detecta el fin real de la voz mediante silencedetect de FFmpeg."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(ruta),
        "-af", "silencedetect=noise=-40dB:d=0.15",
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    starts = re.findall(r"silence_start:\s*([0-9.]+)", res.stderr)
    if starts:
        return float(starts[-1])
    return 0.0


def main():
    model = whisper.load_model("base")
    manifest_path = AUDIOS_DIR / "manifest_audios.json"
    datos = json.loads(manifest_path.read_text(encoding="utf-8"))

    for item in datos:
        ruta = Path(item["path"])
        res = model.transcribe(str(ruta), word_timestamps=True, language="en")
        last_word_end = 0.0
        words_info = []
        for seg in res.get("segments", []):
            for w in seg.get("words", []):
                last_word_end = max(last_word_end, float(w["end"]))
                words_info.append(f"{w['word'].strip()}({w['start']:.2f}-{w['end']:.2f})")

        sil_end = medir_silencedetect(ruta)
        real_speech_end = max(last_word_end, sil_end) if sil_end > 0 else last_word_end
        item["whisper_last_word_end"] = round(last_word_end, 3)
        item["ffmpeg_silence_start"] = round(sil_end, 3)
        item["speech_end"] = round(real_speech_end, 3)
        item["target_video_dur"] = round(real_speech_end + 1.10, 2)

        print(f"\n=== {item['id']} ({item['duration']:.2f}s total mp3) ===")
        print(f"Whisper last word end : {last_word_end:.2f}s")
        print(f"FFmpeg silence_start  : {sil_end:.2f}s")
        print(f"Target video (+1.10s) : {item['target_video_dur']:.2f}s")
        print("Palabras:", " ".join(words_info))

    manifest_path.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

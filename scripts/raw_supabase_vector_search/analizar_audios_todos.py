import whisper
from pathlib import Path

model = whisper.load_model('base')
audios_dir = Path("output/raw_supabase_vector_search/audios")

for i in range(2, 6):
    audio_path = audios_dir / f"tramo_{i:02d}.mp3"
    res = model.transcribe(str(audio_path), word_timestamps=True)
    last_word_end = 0.0
    full_text = []
    for seg in res['segments']:
        full_text.append(seg['text'])
        for w in seg.get('words', []):
            last_word_end = max(last_word_end, w['end'])
    
    print(f"\n--- TRAMO {i:02d} ---")
    print(f"File: {audio_path.name}")
    print(f"Text: {' '.join(full_text)}")
    print(f"Last word end: {last_word_end:.2f}s")
    print(f"Target video duration (last_word + 1.1s): {last_word_end + 1.1:.2f}s")

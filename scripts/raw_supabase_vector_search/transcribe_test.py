import whisper

model = whisper.load_model('base')
res = model.transcribe('output/raw_supabase_vector_search/audios/tramo_01.mp3', word_timestamps=True)
for seg in res['segments']:
    print(f"{seg['start']:.2f}s - {seg['end']:.2f}s: {seg['text']}")
    for w in seg.get('words', []):
        print(f"   {w['start']:.2f}s - {w['end']:.2f}s: {w['word']}")

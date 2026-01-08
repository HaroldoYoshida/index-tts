#!/usr/bin/env python3
from indextts.infer_v2 import IndexTTS2
import os

print('🎤 Loading IndexTTS2 for Batch Generation...')
tts = IndexTTS2(
    cfg_path='checkpoints/config.yaml',
    model_dir='checkpoints',
    use_fp16=True
)

print('✅ Model loaded!')

samples = [
    {
        "filename": "anbi_en_combat.wav",
        "text": "Target locked! Engaging enemy forces! Watch your back!",
        "emotion": "Urgent, loud, combat shout"
    },
    {
        "filename": "anbi_en_casual.wav",
        "text": "I think I'll grab a burger after this mission. Want to come along? My treat.",
        "emotion": "Casual, relaxed, friendly"
    },
    {
        "filename": "anbi_en_serious.wav",
        "text": "The Hollow activity is increasing rapidly. We need to proceed with extreme caution.",
        "emotion": "Serious, whispery, tense"
    }
]

for sample in samples:
    print(f"\n🚀 Generating: {sample['filename']}")
    print(f"   Text: {sample['text']}")
    print(f"   Emotion Context: {sample['emotion']}")
    
    tts.infer(
        spk_audio_prompt='examples/anbi_reference.wav',
        text=sample['text'],
        output_path=sample['filename'],
        # Note: Zero-shot emotion control largely comes from the prompt, 
        # but we can try to influence it if we had specific emotion prompts.
        # Here we rely on the implementation's text processing and the reference audio's inherent tone.
        # If we had emotion reference audios, we would pass them as 'emo_audio_prompt'.
        verbose=True
    )
    print(f"✨ Saved to {sample['filename']}")

print('\n✅ All samples generated!')

#!/usr/bin/env python3
from indextts.infer_v2 import IndexTTS2

print('Loading IndexTTS2...')
tts = IndexTTS2(
    cfg_path='checkpoints/config.yaml',
    model_dir='checkpoints',
    use_fp16=True
)

print('Model loaded!')
print('Generating audio...')

tts.infer(
    spk_audio_prompt='examples/anbi_reference.wav',
    text='Watch out! They are coming from the left!',
    output_path='test_anbi_en.wav',
    verbose=True
)

print('Done! Audio saved to test_anbi_en.wav')

#!/usr/bin/env python3
from indextts.infer_v2 import IndexTTS2

print('Loading IndexTTS2...')
tts = IndexTTS2(
    cfg_path='checkpoints/config.yaml',
    model_dir='checkpoints',
    use_fp16=True
)

print('Model loaded!')
print('Generating PT-BR audio...')

# Cross-lingual test: EN voice prompt -> PT text
tts.infer(
    spk_audio_prompt='examples/anbi_reference.wav',
    text='Cuidado! Eles estão vindo pela direita, preparem-se para o ataque!',
    output_path='test_anbi_pt.wav',
    verbose=True
)

print('Done! Audio saved to test_anbi_pt.wav')

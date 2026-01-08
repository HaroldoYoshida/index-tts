#!/usr/bin/env python3
"""
Script de teste para clonagem de voz usando IndexTTS2.
Usa as vozes extraídas do ZZZ para gerar falas em português.
"""

import sys
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from indextts.infer_v2 import IndexTTS2


def test_voice_cloning(voice_path: str, text: str, output_path: str, emotion_desc: str = None):
    """
    Testa a clonagem de voz com uma referência do ZZZ.
    
    Args:
        voice_path: Caminho para o arquivo de voz de referência
        text: Texto para sintetizar
        output_path: Caminho para salvar o áudio gerado
        emotion_desc: Descrição da emoção (opcional)
    """
    print(f"🎤 Carregando IndexTTS2...")
    tts = IndexTTS2(
        cfg_path="checkpoints/config.yaml",
        model_dir="checkpoints",
        use_fp16=True,  # Otimizado para RTX 4090
        use_cuda_kernel=False,
        use_deepspeed=False
    )
    
    print(f"✅ Modelo carregado!")
    print(f"📢 Voz de referência: {voice_path}")
    print(f"💬 Texto: {text}")
    
    # Parâmetros de inferência
    kwargs = {
        "spk_audio_prompt": voice_path,
        "text": text,
        "output_path": output_path,
        "verbose": True
    }
    
    # Adiciona controle emocional se especificado
    if emotion_desc:
        print(f"🎭 Emoção: {emotion_desc}")
        kwargs["use_emo_text"] = True
        kwargs["emo_text"] = emotion_desc
        kwargs["emo_alpha"] = 0.7
    
    print(f"\n🚀 Gerando áudio...")
    tts.infer(**kwargs)
    
    print(f"\n✨ Áudio gerado com sucesso: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste de clonagem de voz com IndexTTS2")
    parser.add_argument("--voice", required=True, help="Caminho para o arquivo de voz de referência (.wav)")
    parser.add_argument("--text", required=True, help="Texto para sintetizar")
    parser.add_argument("--output", default="output_test.wav", help="Arquivo de saída")
    parser.add_argument("--emotion", help="Descrição da emoção (ex: 'Gritando com raiva')")
    
    args = parser.parse_args()
    
    test_voice_cloning(args.voice, args.text, args.output, args.emotion)

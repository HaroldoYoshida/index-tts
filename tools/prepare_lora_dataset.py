import os
import argparse
from pathlib import Path
import whisper
import tqdm

def prepare_dataset(audio_dir, output_file, language="en"):
    """
    Gera o arquivo de lista para treinamento (caminho|transcrição).
    Usa Whisper para transcrever os áudios automaticamente.
    """
    print(f"📦 Carregando modelo Whisper ({language})...")
    model = whisper.load_model("medium.en" if language == "en" else "medium")
    
    audio_files = list(Path(audio_dir).glob("**/*.wav"))
    print(f"🔍 Encontrados {len(audio_files)} arquivos de áudio.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for audio_path in tqdm.tqdm(audio_files):
            try:
                # Transcreve
                result = model.transcribe(str(audio_path), language=language)
                text = result["text"].strip()
                
                # Formato: /abs/path/to/audio.wav|Texto transcrito
                if text:
                    f.write(f"{audio_path.absolute()}|{text}\n")
            except Exception as e:
                print(f"⚠️ Erro ao processar {audio_path.name}: {e}")

    print(f"✅ Dataset pronto em: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_dir", required=True, help="Pasta com os áudios (wav) do personagem")
    parser.add_argument("--output", default="filelists/train.txt", help="Arquivo de saída")
    parser.add_argument("--lang", default="en", help="Idioma dos áudios (en, ja, pt)")
    
    args = parser.parse_args()
    
    prepare_dataset(args.audio_dir, args.output, args.lang)

import os
import shutil
import argparse
from pathlib import Path

def sync_voices(source_dir, target_dir, characters=None):
    """
    Sincroniza arquivos de voz extraídos para a pasta do projeto IndexTTS2.
    """
    src = Path(source_dir)
    dst = Path(target_dir) / "examples" / "voices_zzz"
    
    if not src.exists():
        print(f"Erro: Pasta de origem não encontrada: {src}")
        return

    dst.mkdir(parents=True, exist_ok=True)
    
    print(f"Sincronizando de {src} para {dst}...")
    
    count = 0
    # AnimeWwise costuma organizar por pastas de personagens ou nomes de arquivos específicos
    for root, dirs, files in os.walk(src):
        for file in files:
            if file.endswith(('.wav', '.mp3', '.ogg')):
                # Se characters for especificado, filtra por nome de personagem no path ou nome do arquivo
                if characters:
                    if not any(char.lower() in (root + file).lower() for char in characters):
                        continue
                
                rel_path = os.path.relpath(os.path.join(root, file), src)
                target_path = dst / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(os.path.join(root, file), target_path)
                count += 1
                if count % 100 == 0:
                    print(f"Copiados {count} arquivos...")

    print(f"Sucesso! {count} arquivos de voz sincronizados em {dst}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync ZZZ voices to IndexTTS2")
    parser.add_argument("--src", default="/mnt/e/Extraidos", help="Pasta onde você extraiu os áudios no Windows")
    parser.add_argument("--chars", nargs="+", help="Nomes de personagens para filtrar (opcional)")
    
    args = parser.parse_args()
    
    # Target fixo no projeto atual
    project_root = "/home/vmadmin/projects/IndexTTS2"
    
    sync_voices(args.src, project_root, args.chars)

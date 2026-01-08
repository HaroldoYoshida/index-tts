
import os
import argparse
import shutil
import librosa
import soundfile as sf
from pathlib import Path
from tqdm import tqdm

def process_audio(file_path, output_path, target_sr=24000):
    """
    Loads audio, converts to mono 24khz, and saves to target path.
    """
    try:
        # Load audio (librosa handles resampling and mono conversion)
        y, sr = librosa.load(file_path, sr=target_sr, mono=True)
        # Trim silence
        y, _ = librosa.effects.trim(y, top_db=20)
        # Save
        sf.write(output_path, y, target_sr)
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Ingest and standardize character voice datasets.")
    parser.add_argument("--input-dir", type=str, required=True, help="Path to folder containing raw wav/mp3 files")
    parser.add_argument("--game", type=str, required=True, help="Game prefix (e.g., zzz, gen)")
    parser.add_argument("--char", type=str, required=True, help="Character ID/Name (e.g., anbi, hutao)")
    parser.add_argument("--gender", type=str, required=True, choices=['f', 'm'], help="Gender (f/m)")
    parser.add_argument("--lang", type=str, required=True, help="Language code (e.g., jp, en)")
    parser.add_argument("--output-base", type=str, default="data", help="Base data directory")
    
    args = parser.parse_args()

    # Construct standard ID
    std_id = f"{args.game}_{args.char}_{args.gender}_{args.lang}"
    output_dir = Path(args.output_base) / std_id
    
    print(f"--- LoRA Factory Ingestion ---")
    print(f"Target ID: {std_id}")
    print(f"Input: {args.input_dir}")
    print(f"Output: {output_dir}")
    
    if output_dir.exists():
        print(f"Warning: Output directory {output_dir} already exists. Merging/Overwriting.")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Find Audio Files
    search_path = Path(args.input_dir)
    audio_extensions = ['.wav', '.mp3', '.flac', '.ogg']
    files = []
    for ext in audio_extensions:
        files.extend(list(search_path.rglob(f"*{ext}")))
    
    print(f"Found {len(files)} audio files.")
    
    # Process
    success_count = 0
    for i, file_path in enumerate(tqdm(files)):
        # New Filename: std_id_0001.wav
        new_name = f"{std_id}_{i+1:04d}.wav"
        out_path = output_dir / new_name
        
        if process_audio(file_path, out_path):
            success_count += 1
            
    print(f"--- Ingestion Complete ---")
    print(f"Successfully processed: {success_count}/{len(files)}")
    print(f"Ready for transcription/training at: {output_dir}")

if __name__ == "__main__":
    main()

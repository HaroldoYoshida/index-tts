#!/usr/bin/env python3
"""
Script to transcribe valid Japanese audio files using Whisper and update the JSONL manifest.
Usage: python tools/transcribe_jp_jsonl.py --input data/.../manifest.jsonl --output filelists/train.jsonl --audio_dir data/.../
"""
import argparse
import json
import whisper
import tqdm
from pathlib import Path

def transcribe_manifest(input_path, output_path, audio_dir=None, model_size="medium", lang="ja"):
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    audio_base = Path(audio_dir) if audio_dir else None
    
    if not input_path.exists():
        print(f"Input manifest {input_path} not found.")
        return

    print("Reading input manifest...")
    entries = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    print(f"Processing {len(entries)} entries...")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Open output file for streaming write (in case of crash)
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for entry in tqdm.tqdm(entries):
            current_audio = Path(entry['audio'])
            
            # Resolve full path
            if audio_base and not current_audio.is_absolute():
                full_audio_path = audio_base / current_audio
            else:
                full_audio_path = current_audio
            
            if not full_audio_path.exists():
                print(f"Warning: Audio file not found: {full_audio_path}")
                continue
                
            try:
                # Transcribe
                result = model.transcribe(str(full_audio_path), language=lang)
                text = result["text"].strip()
                
                # Update entry with TRANSCRIPTION and ABSOLUTE PATH
                entry['text'] = text
                entry['audio'] = str(full_audio_path.resolve())
                
                # Write immediately
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f_out.flush()
                
            except Exception as e:
                print(f"Error transcribing {full_audio_path}: {e}")

    print(f"Done! Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audio_dir", help="Base directory for audio files if relative in manifest")
    parser.add_argument("--model", default="medium")
    parser.add_argument("--lang", default="ja")
    
    args = parser.parse_args()
    
    transcribe_manifest(args.input, args.output, args.audio_dir, args.model, args.lang)

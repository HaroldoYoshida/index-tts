#!/usr/bin/env python3
"""
Transcribe audio directory to IndexTTS2 manifest JSONL format using Whisper.
Required input for preprocess_data.py.
"""

import argparse
import json
import uuid
import whisper
import sys
from pathlib import Path
from tqdm import tqdm


def transcribe_to_manifest(
    audio_dir: Path,
    output_file: Path,
    language: str,
    speaker_name: str,
    device: str = "cuda"
):
    print(f"📦 Loading Whisper model (medium)...")
    try:
        model = whisper.load_model("medium", device=device)
    except Exception as e:
        print(f"⚠️ Failed to load on {device}, falling back to cpu: {e}")
        model = whisper.load_model("medium", device="cpu")

    audio_files = sorted(list(audio_dir.glob("*.wav")))
    print(f"🔍 Found {len(audio_files)} WAV files in {audio_dir}")

    if not audio_files:
        print("❌ No audio files found!")
        sys.exit(1)

    with open(output_file, "w", encoding="utf-8") as f:
        for audio_path in tqdm(audio_files, desc="Transcribing"):
            try:
                # Transcribe
                result = model.transcribe(
                    str(audio_path),
                    language=language,
                    beam_size=5,
                    best_of=5
                )
                text = result["text"].strip()
                
                if not text:
                    continue

                # Create manifest entry
                # ID format: speaker_filename
                uid = f"{speaker_name}_{audio_path.stem}"
                
                record = {
                    "id": uid,
                    "audio": str(audio_path.absolute()),
                    "text": text,
                    "speaker": speaker_name,
                    "language": language,
                    "duration": result.get("segments", [{}])[-1].get("end", 0.0)
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                
            except Exception as e:
                print(f"⚠️ Error processing {audio_path.name}: {e}")

    print(f"✅ Manifest saved to {output_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--language", default="ja", help="Audio language (ja, en)")
    parser.add_argument("--speaker", required=True, help="Speaker identifier")
    
    args = parser.parse_args()
    
    transcribe_to_manifest(
        args.audio_dir,
        args.output,
        args.language,
        args.speaker
    )


if __name__ == "__main__":
    main()

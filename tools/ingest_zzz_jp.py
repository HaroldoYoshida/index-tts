#!/usr/bin/env python3
"""
Script to ingest extracted ZZZ Japanese voice files.
It filters for 'Anbi' (or other characters) and creates the necessary project structure.
Usage: python tools/ingest_zzz_jp.py --src /mnt/e/AnimeWwise/ZZZ_JP --dest data/anbi_jp --manifest filelists/train_anbi_jp.jsonl
"""
import os
import shutil
import argparse
from pathlib import Path
from tqdm import tqdm
import json

# Filters
CHARACTER_ID = "Anbi" 

def ingest(source_dir, dest_dir, manifest_path):
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)
    manifest_path = Path(manifest_path)

    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning {source_dir} recursively for *Anbi*.wav...")
    all_wavs = list(source_dir.rglob("*.wav"))
    
    anbi_files = [f for f in all_wavs if "Anbi" in f.name or "anbi" in f.name]

    if not anbi_files:
         print(f"No Anbi .wav files found in {source_dir}")
         return

    print(f"Found {len(anbi_files)} Anbi files (out of {len(all_wavs)} total wavs). Copying to {dest_dir}...")
    
    jsonl_entries = []
    
    for src_file in tqdm(anbi_files):
        dest_file = dest_dir / src_file.name
        
        # Only copy if not exists or size diff
        if not dest_file.exists() or dest_file.stat().st_size != src_file.stat().st_size:
            shutil.copy2(src_file, dest_file)
            
        # Build JSONL entry using ABSOLUTE path for the TARGET environment
        # Since we might run this locally but train remotely, we need to be careful.
        # Strategy: Use relative path in JSONL or fix it later?
        # Jarod's pipeline often likes absolute paths.
        # Let's save the LOCAL path for now, and we can run a sed command to fix paths on remote if needed.
        # OR better: assume the folder structure mirrors.
        # Let's just use the filename and let the preprocess script resolve it? 
        # No, preprocess needs full path usually.
        # We will fix the paths in the transcription step (which runs on remote).
        
        entry = {
            "id": src_file.stem,
            "text": "Japanese text placeholder", 
            "audio": src_file.name, # Storing filename only for now, will fix path on remote
            "speaker": "anbi",
            "language": "ja"
        }
        jsonl_entries.append(entry)

    print(f"Copied {len(jsonl_entries)} files.")
    
    # Save partial manifest
    temp_manifest = manifest_path.with_suffix(".temp.jsonl")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_manifest, 'w', encoding='utf-8') as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"Created temporary manifest at {temp_manifest}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="Source directory with extracted audio")
    parser.add_argument("--dest", required=True, help="Destination directory for filtered audio")
    parser.add_argument("--manifest", required=True, help="Output manifest path")
    args = parser.parse_args()
    
    ingest(args.src, args.dest, args.manifest)

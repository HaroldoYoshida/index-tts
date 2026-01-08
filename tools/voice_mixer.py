#!/usr/bin/env python3
"""
Voice Mixer for Multi-Character LoRA Factory.
Combines audio datasets from multiple characters to create hybrid voice LoRAs.
"""

import argparse
import json
import os
import random
import shutil
from pathlib import Path
from typing import List, Tuple


def get_audio_files(source_dir: Path) -> List[Path]:
    """Get all WAV files from a source directory."""
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("*.wav"))


def validate_same_gender(source_ids: List[str], catalog_path: Path) -> Tuple[bool, str]:
    """Validate that all source characters have the same gender."""
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    
    char_map = {c["id"]: c for c in catalog.get("characters", [])}
    genders = set()
    
    for sid in source_ids:
        if sid in char_map:
            genders.add(char_map[sid].get("gender", "unknown"))
        else:
            # Try to infer from ID pattern: xxx_name_[f|m]_lang
            parts = sid.split("_")
            if len(parts) >= 4:
                genders.add(parts[-2])
    
    if len(genders) > 1:
        return False, f"Mixed genders detected: {genders}"
    
    return True, list(genders)[0] if genders else "unknown"


def mix_datasets(
    sources: List[str],
    output_id: str,
    data_base: Path,
    ratio: List[int],
    max_samples: int = 0,
    seed: int = 42,
) -> int:
    """Mix audio files from multiple source datasets."""
    random.seed(seed)
    
    # Collect files from each source
    source_files = []
    for sid in sources:
        src_path = data_base / sid
        files = get_audio_files(src_path)
        if not files:
            print(f"⚠️  No files found in {src_path}")
        source_files.append(files)
        print(f"  {sid}: {len(files)} files")
    
    # Calculate sample counts based on ratio
    total_ratio = sum(ratio)
    sample_counts = []
    
    for i, files in enumerate(source_files):
        target_ratio = ratio[i] / total_ratio
        available = len(files)
        
        if max_samples > 0:
            target_count = int(max_samples * target_ratio)
        else:
            # Use the smallest source as reference
            min_available = min(len(f) for f in source_files if f)
            target_count = int(min_available * (ratio[i] / min(ratio)))
        
        actual_count = min(target_count, available)
        sample_counts.append(actual_count)
    
    print(f"\n📊 Sample distribution: {list(zip(sources, sample_counts))}")
    
    # Create output directory
    output_dir = data_base / output_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files
    file_counter = 0
    for i, (sid, files, count) in enumerate(zip(sources, source_files, sample_counts)):
        if not files:
            continue
        
        # Random sample if we need fewer files
        selected = random.sample(files, count) if count < len(files) else files
        
        for src_file in selected:
            file_counter += 1
            # New filename: output_id_XXXX.wav
            dst_name = f"{output_id}_{file_counter:04d}.wav"
            dst_path = output_dir / dst_name
            shutil.copy2(src_file, dst_path)
    
    return file_counter


def create_mix_manifest(
    sources: List[str],
    output_id: str,
    data_base: Path,
    gender: str,
) -> None:
    """Create a manifest JSON for the mixed dataset."""
    manifest = {
        "id": output_id,
        "type": "mixed",
        "sources": sources,
        "gender": gender,
        "sample_count": len(list((data_base / output_id).glob("*.wav"))),
    }
    
    manifest_path = data_base / output_id / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"📝 Manifest saved: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Mix voice datasets for hybrid LoRA training")
    parser.add_argument("--sources", type=str, nargs="+", required=True, help="Source character IDs to mix")
    parser.add_argument("--output", type=str, required=True, help="Output mixed dataset ID")
    parser.add_argument("--data-base", type=str, default="data", help="Base data directory")
    parser.add_argument("--catalog", type=str, default="data/character_catalog.json", help="Character catalog path")
    parser.add_argument("--ratio", type=str, default="50:50", help="Mix ratio (e.g., 50:50, 60:40)")
    parser.add_argument("--max-samples", type=int, default=0, help="Maximum total samples (0 = use all)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--skip-validation", action="store_true", help="Skip gender validation")
    
    args = parser.parse_args()
    
    data_base = Path(args.data_base)
    catalog_path = Path(args.catalog)
    
    # Parse ratio
    ratio = [int(r) for r in args.ratio.split(":")]
    if len(ratio) != len(args.sources):
        # Extend ratio if needed (default to equal)
        ratio = [1] * len(args.sources)
    
    print(f"🎭 Voice Mixer")
    print(f"  Sources: {args.sources}")
    print(f"  Output: {args.output}")
    print(f"  Ratio: {ratio}")
    print("-" * 50)
    
    # Validate gender
    if not args.skip_validation and catalog_path.exists():
        valid, gender = validate_same_gender(args.sources, catalog_path)
        if not valid:
            print(f"❌ Error: {gender}")
            print("   Use --skip-validation to override")
            return
        print(f"✅ Gender validated: {gender}")
    else:
        gender = "unknown"
        print("⚠️  Skipping gender validation")
    
    # Mix datasets
    total = mix_datasets(
        sources=args.sources,
        output_id=args.output,
        data_base=data_base,
        ratio=ratio,
        max_samples=args.max_samples,
        seed=args.seed,
    )
    
    # Create manifest
    create_mix_manifest(args.sources, args.output, data_base, gender)
    
    print("-" * 50)
    print(f"✅ Created {args.output} with {total} samples")
    print(f"📁 Location: {data_base / args.output}")


if __name__ == "__main__":
    main()

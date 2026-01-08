#!/usr/bin/env python3
"""
Batch ingestion script for Multi-Character LoRA Factory.
Processes all characters in character_catalog.json through ingest_character.py.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def load_catalog(catalog_path: Path) -> dict:
    """Load character catalog JSON."""
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_characters(
    characters: List[dict],
    gender: Optional[str] = None,
    game: Optional[str] = None,
    lang: Optional[str] = None,
    char_ids: Optional[List[str]] = None,
) -> List[dict]:
    """Filter characters by criteria."""
    filtered = characters
    
    if gender:
        filtered = [c for c in filtered if c.get("gender") == gender]
    if game:
        filtered = [c for c in filtered if c.get("game") == game]
    if lang:
        filtered = [c for c in filtered if c.get("lang") == lang]
    if char_ids:
        filtered = [c for c in filtered if c.get("id") in char_ids]
    
    return filtered


def ingest_character(char: dict, source_base: str, output_base: str, dry_run: bool = False) -> bool:
    """Run ingest_character.py for a single character."""
    source_path = Path(source_base) / char["source"]
    
    if not source_path.exists():
        print(f"  ⚠️  Source not found: {source_path}")
        return False
    
    cmd = [
        sys.executable, "tools/ingest_character.py",
        "--input-dir", str(source_path),
        "--game", char["game"],
        "--char", char["name"].lower().replace(" ", ""),
        "--gender", char["gender"],
        "--lang", char["lang"],
        "--output-base", output_base,
    ]
    
    print(f"  → {char['id']}: {source_path}")
    
    if dry_run:
        print(f"    [DRY RUN] Would run: {' '.join(cmd)}")
        return True
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"    ❌ Error: {result.stderr[:200]}")
            return False
        print(f"    ✅ Success")
        return True
    except subprocess.TimeoutExpired:
        print(f"    ❌ Timeout")
        return False
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch ingest characters for LoRA Factory")
    parser.add_argument("--catalog", type=str, default="data/character_catalog.json", help="Path to character catalog")
    parser.add_argument("--output-base", type=str, default="data", help="Base output directory")
    parser.add_argument("--gender", type=str, choices=["f", "m"], help="Filter by gender")
    parser.add_argument("--game", type=str, help="Filter by game (genshin, zzz)")
    parser.add_argument("--lang", type=str, help="Filter by language (jp, en)")
    parser.add_argument("--chars", type=str, nargs="+", help="Specific character IDs to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without processing")
    parser.add_argument("--limit", type=int, help="Limit number of characters to process")
    
    args = parser.parse_args()
    
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"❌ Catalog not found: {catalog_path}")
        sys.exit(1)
    
    catalog = load_catalog(catalog_path)
    source_base = catalog.get("source_base", "/mnt/e/AnimeWwise")
    characters = catalog.get("characters", [])
    
    print(f"📚 Loaded catalog: {len(characters)} characters")
    print(f"📂 Source base: {source_base}")
    
    # Apply filters
    filtered = filter_characters(
        characters,
        gender=args.gender,
        game=args.game,
        lang=args.lang,
        char_ids=args.chars,
    )
    
    if args.limit:
        filtered = filtered[:args.limit]
    
    print(f"🎯 Processing {len(filtered)} characters")
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print("-" * 50)
    
    success = 0
    failed = 0
    
    for char in filtered:
        if ingest_character(char, source_base, args.output_base, args.dry_run):
            success += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Upload trained LoRA checkpoints to S3/MinIO cold storage.
Organizes by gender and cleans up local intermediate checkpoints.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_mc_alias() -> str:
    """Detect configured MinIO alias."""
    result = subprocess.run(["mc", "alias", "ls"], capture_output=True, text=True)
    if "minio" in result.stdout:
        return "minio"
    return "local"  # fallback


def get_gender_from_id(char_id: str) -> str:
    """Extract gender from character ID pattern: game_name_[f|m]_lang."""
    parts = char_id.split("_")
    if len(parts) >= 3:
        gender = parts[-2]
        if gender in ("f", "m"):
            return "female" if gender == "f" else "male"
    return "unknown"


def upload_checkpoint(
    checkpoint_dir: Path,
    char_id: str,
    bucket: str = "voice-loras",
    mc_alias: str = "minio",
    dry_run: bool = False,
) -> bool:
    """Upload the latest checkpoint to S3."""
    # Find the latest checkpoint
    checkpoints = sorted(checkpoint_dir.glob("model_step*.pth"))
    if not checkpoints:
        print(f"❌ No checkpoints found in {checkpoint_dir}")
        return False
    
    latest = checkpoints[-1]
    print(f"📦 Latest checkpoint: {latest.name} ({latest.stat().st_size / 1e9:.2f} GB)")
    
    # Determine S3 path
    gender = get_gender_from_id(char_id)
    s3_path = f"{mc_alias}/{bucket}/{gender}/{char_id}/"
    
    # Create metadata
    metadata = {
        "id": char_id,
        "gender": gender,
        "checkpoint": latest.name,
        "uploaded_at": datetime.utcnow().isoformat(),
        "size_bytes": latest.stat().st_size,
    }
    
    metadata_file = checkpoint_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    if dry_run:
        print(f"[DRY RUN] Would upload to: {s3_path}")
        print(f"  - {latest.name}")
        print(f"  - metadata.json")
        return True
    
    # Upload checkpoint
    print(f"⬆️  Uploading to {s3_path}...")
    
    cmd1 = ["mc", "cp", str(latest), f"{s3_path}model.pth"]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    if result1.returncode != 0:
        print(f"❌ Upload failed: {result1.stderr}")
        return False
    
    cmd2 = ["mc", "cp", str(metadata_file), f"{s3_path}metadata.json"]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    if result2.returncode != 0:
        print(f"❌ Metadata upload failed: {result2.stderr}")
        return False
    
    print(f"✅ Uploaded to {s3_path}")
    return True


def cleanup_local(checkpoint_dir: Path, keep_latest: bool = True, dry_run: bool = False):
    """Remove intermediate checkpoints to free disk space."""
    checkpoints = sorted(checkpoint_dir.glob("model_step*.pth"))
    
    if keep_latest and len(checkpoints) > 1:
        to_delete = checkpoints[:-1]
    else:
        to_delete = []
    
    freed = 0
    for ckpt in to_delete:
        size = ckpt.stat().st_size
        if dry_run:
            print(f"[DRY RUN] Would delete: {ckpt.name} ({size / 1e9:.2f} GB)")
        else:
            ckpt.unlink()
            print(f"🗑️  Deleted: {ckpt.name}")
        freed += size
    
    if freed > 0:
        print(f"💾 Freed: {freed / 1e9:.2f} GB")


def main():
    parser = argparse.ArgumentParser(description="Upload LoRA checkpoints to S3 cold storage")
    parser.add_argument("character_id", help="Character ID (e.g., gen_ayaka_f_jp)")
    parser.add_argument("--checkpoints-dir", type=str, default="trained_ckpts", help="Base checkpoints directory")
    parser.add_argument("--bucket", type=str, default="voice-loras", help="S3 bucket name")
    parser.add_argument("--mc-alias", type=str, default="", help="MinIO client alias (auto-detect if empty)")
    parser.add_argument("--cleanup", action="store_true", help="Delete intermediate checkpoints after upload")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading/deleting")
    
    args = parser.parse_args()
    
    checkpoint_dir = Path(args.checkpoints_dir) / args.character_id
    
    if not checkpoint_dir.exists():
        print(f"❌ Directory not found: {checkpoint_dir}")
        sys.exit(1)
    
    mc_alias = args.mc_alias or get_mc_alias()
    
    print(f"📤 Upload to S3")
    print(f"  Character: {args.character_id}")
    print(f"  Source: {checkpoint_dir}")
    print(f"  Bucket: {args.bucket}")
    print(f"  Alias: {mc_alias}")
    print("-" * 50)
    
    success = upload_checkpoint(
        checkpoint_dir=checkpoint_dir,
        char_id=args.character_id,
        bucket=args.bucket,
        mc_alias=mc_alias,
        dry_run=args.dry_run,
    )
    
    if success and args.cleanup:
        print("\n🧹 Cleanup")
        cleanup_local(checkpoint_dir, keep_latest=True, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

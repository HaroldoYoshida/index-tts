#!/bin/bash
# LoRA Factory Training Wrapper
# ⚠️ MUST RUN ON gpu-node (192.168.31.200) WITH RTX 4090
# Usage: ./train_lora_factory.sh <character_id> [epochs]

set -e

# GPU Check - prevent running on wrong machine
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if [[ ! "$GPU_NAME" =~ "4090" ]]; then
    echo "❌ ERRO: Este script deve rodar no gpu-node com RTX 4090!"
    echo "   GPU detectada: $GPU_NAME"
    echo "   Conecte via: ssh vmadmin@192.168.31.200"
    exit 1
fi

CHARACTER_ID="${1:?Usage: $0 <character_id> [epochs]}"
EPOCHS="${2:-15}"

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$BASE_DIR/data/$CHARACTER_ID"
OUTPUT_DIR="$BASE_DIR/trained_ckpts/$CHARACTER_ID"

echo "🏭 LoRA Factory Training"
echo "  Character: $CHARACTER_ID"
echo "  Epochs: $EPOCHS"
echo "  Data: $DATA_DIR"
echo "  Output: $OUTPUT_DIR"
echo "---"

# Check for paired manifests
TRAIN_MANIFEST="$DATA_DIR/train_paired.jsonl"
VAL_MANIFEST="$DATA_DIR/val_paired.jsonl"

# Determine language from character ID (e.g., gen_ayaka_f_jp -> jp)
LANG_SUFFIX=$(echo "$CHARACTER_ID" | rev | cut -d'_' -f1 | rev)
# Map suffix to standard language codes
if [[ "$LANG_SUFFIX" == "jp" ]]; then LANG="ja"; else LANG="en"; fi

echo "  Language: $LANG_SUFFIX -> $LANG"

# --- Preprocessing Flow ---
export PYTHONPATH="$(pwd)/temp_jarod:$PYTHONPATH"
TRAIN_MANIFEST="$DATA_DIR/train_paired.jsonl"
VAL_MANIFEST="$DATA_DIR/val_paired.jsonl"

if [[ ! -f "$TRAIN_MANIFEST" ]]; then
    echo "⚙️  Preprocessing needed..."
    
    # 1. Transcribe (Whisper)
    RAW_MANIFEST="$DATA_DIR/manifest_raw.jsonl"
    if [[ ! -f "$RAW_MANIFEST" ]]; then
        echo "  🎤 Transcribing audio (Whisper)..."
        uv run python tools/transcribe_to_manifest.py \
            --audio-dir "$DATA_DIR" \
            --output "$RAW_MANIFEST" \
            --language "$LANG" \
            --speaker "$CHARACTER_ID"
    fi

    # 2. Preprocess (Extract Features)
    PROCESSED_DIR="$DATA_DIR/processed"
    PREPROCESSED_MANIFEST="$PROCESSED_DIR/train_manifest.jsonl"
    if [[ ! -f "$PREPROCESSED_MANIFEST" ]]; then
        echo "  🧠 Extracting semantic features..."
        uv run python temp_jarod/tools/preprocess_data.py \
            --manifest "$RAW_MANIFEST" \
            --output-dir "$PROCESSED_DIR" \
            --tokenizer checkpoints/bpe.model \
            --config checkpoints/config.yaml \
            --gpt-checkpoint checkpoints/gpt.pth \
            --language "$LANG" \
            --val-ratio 0.05
    fi

    # 3. Build Pairs
    echo "  🔗 Building prompt-target pairs..."
    uv run python temp_jarod/tools/build_gpt_prompt_pairs.py \
        --manifest "$PREPROCESSED_MANIFEST" \
        --output "$TRAIN_MANIFEST" \
        --pairs-per-target 2

    # Use same file for validation if val_manifest.jsonl is small/empty or just use split
    # Actually preprocess_data.py generates stats.json and val_manifest.jsonl if ratio > 0
    # Let's process validation pairs too if they exist
    VAL_RAW="$PROCESSED_DIR/val_manifest.jsonl"
    if [[ -f "$VAL_RAW" && -s "$VAL_RAW" ]]; then
        uv run python temp_jarod/tools/build_gpt_prompt_pairs.py \
            --manifest "$VAL_RAW" \
            --output "$VAL_MANIFEST" \
            --pairs-per-target 1
    else
         cp "$TRAIN_MANIFEST" "$VAL_MANIFEST"
    fi
    
    echo "✅ Preprocessing complete"
fi

# Run training with 50k tokenizer (CRITICAL: never use 12k)
cd "$BASE_DIR"
uv run python temp_jarod/trainers/train_gpt_v2.py \
    --train-manifest "$TRAIN_MANIFEST::$LANG" \
    --val-manifest "$VAL_MANIFEST::$LANG" \
    --tokenizer checkpoints/bpe.model \
    --config checkpoints/config.yaml \
    --base-checkpoint checkpoints/gpt.pth \
    --output-dir "$OUTPUT_DIR" \
    --batch-size 2 \
    --epochs "$EPOCHS" \
    --save-interval 2500 \
    --grad-accumulation 2 \
    --learning-rate 1.5e-5 \
    --warmup-steps 500 \
    --amp \
    --resume auto

echo "✅ Training complete: $OUTPUT_DIR"

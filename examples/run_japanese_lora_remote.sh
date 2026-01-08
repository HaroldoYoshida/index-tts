#!/bin/bash
# Script to test the trained Japanese LoRA on the remote server

set -e

# Config
BASE_DIR="$HOME/projects/IndexTTS-Jarod"
CONFIG="$BASE_DIR/checkpoints/config_lora_jp.yaml"
CHECKPOINT="$BASE_DIR/checkpoints/voice_jp_v1.pth"
REF_AUDIO="$BASE_DIR/data/anime_female_jp_01/Accompany_Anbi_Doubt_01.wav"
OUTPUT_DIR="$BASE_DIR/outputs"
OUTPUT_FILE="$OUTPUT_DIR/test_jp_anbi_v3.wav"
TEXT="お疲れ様です。日本語のテストをしています。声の質はどうでしょうか？"

mkdir -p "$OUTPUT_DIR"

echo "🚀 Starting Japanese Inference..."
echo "Reference: $REF_AUDIO"
echo "Checkpoint: $CHECKPOINT"
echo "Text: $TEXT"

cd "$BASE_DIR"
~/.local/bin/uv run python inference_script.py \
    --config "$CONFIG" \
    --gpt-checkpoint "$CHECKPOINT" \
    --tokenizer "$BASE_DIR/checkpoints/japanese_bpe.model" \
    --speaker "$REF_AUDIO" \
    --text "$TEXT" \
    --output "$OUTPUT_FILE" \
    --device cuda

echo "✅ Inference complete! Saved to $OUTPUT_FILE"

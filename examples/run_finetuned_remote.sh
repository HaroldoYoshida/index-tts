#!/bin/bash
# Script to run inference using the latest trained checkpoint on the remote GPU

SERVER="vmadmin@100.114.21.15"
REMOTE_DIR="~/projects/IndexTTS-Jarod"
CHECKPOINT_DIR="trained_ckpts_anbi"
OUTPUT_REMOTE="output_finetuned.wav"
OUTPUT_LOCAL="output_finetuned.wav"

TEXT=${1:-"This is a test of the fine-tuned Anbi voice."}

echo "Connectig to $SERVER..."

ssh $SERVER "cd $REMOTE_DIR && \
    LATEST_CKPT=\$(ls -t $CHECKPOINT_DIR/*.pth 2>/dev/null | head -n1); \
    if [ -z \"\$LATEST_CKPT\" ]; then \
        echo 'No checkpoints found in $CHECKPOINT_DIR yet!'; \
        exit 1; \
    fi; \
    echo \"Using checkpoint: \$LATEST_CKPT\"; \
    ~/.local/bin/uv run python inference_script.py \
        --config checkpoints/config.yaml \
        --gpt-checkpoint \$LATEST_CKPT \
        --speaker \"data/anbi_en/wavs/Anbi_EN_0001.wav\" \
        --text \"$TEXT\" \
        --output $OUTPUT_REMOTE \
        --device cuda"

if [ $? -eq 0 ]; then
    echo "Downloading audio..."
    scp $SERVER:$REMOTE_DIR/$OUTPUT_REMOTE $OUTPUT_LOCAL
    echo "Saved to $OUTPUT_LOCAL"
else
    echo "Inference failed."
fi

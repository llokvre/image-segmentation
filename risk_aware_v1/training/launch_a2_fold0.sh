#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/autodl-tmp/nnunet_brats
TRAIN_DIR="$ROOT/risk_aware_v1_a2_training"
LOG="$TRAIN_DIR/a2_launch_log.txt"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate nnunet
export nnUNet_raw="$ROOT/nnUNet_raw"
export nnUNet_preprocessed="$ROOT/nnUNet_preprocessed"
export nnUNet_results="$ROOT/nnUNet_results"
export PYTHONPATH="$TRAIN_DIR/trainer_package${PYTHONPATH:+:$PYTHONPATH}"
export nnUNet_compile=false
cd "$ROOT"
{
  printf 'START_TIME=%s\n' "$(date -Is)"
  printf 'HOSTNAME=%s\n' "$(hostname)"
  printf 'GPU='; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
  printf 'NNUNET_RAW=%s\nNNUNET_PREPROCESSED=%s\nNNUNET_RESULTS=%s\n' "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
  printf 'NNUNET_COMPILE=%s\n' "$nnUNet_compile"
  sha256sum "$TRAIN_DIR/trainer_package/risk_aware_core.py" "$TRAIN_DIR/trainer_package/availability_integration.py" "$TRAIN_DIR/trainer_package/nnUNetTrainerModDropAvailabilityMask.py" "$TRAIN_DIR/launch_a2_fold0.py" "$TRAIN_DIR/launch_a2_fold0.sh"
  python -u "$TRAIN_DIR/launch_a2_fold0.py"
} 2>&1 | tee -a "$LOG"

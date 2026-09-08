#!/usr/bin/env bash
set -u
ROOT=/root/autodl-tmp/nnunet_brats
A1="$ROOT/nnUNet_results/Dataset501_BraTS2023/nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres/fold_0"
A2="$ROOT/nnUNet_results/Dataset501_BraTS2023/nnUNetTrainerModDropAvailabilityMask__nnUNetPlans__3d_fullres/fold_0"
BEFORE="$ROOT/risk_aware_v1_a2_training/runtime/a1_before_manifest.txt"
if tmux has-session -t a2_fold0_train 2>/dev/null; then echo 'TMUX_SESSION=EXISTS'; else echo 'TMUX_SESSION=ABSENT'; fi
MAIN=$(pgrep -o -f '^python -u /root/autodl-tmp/nnunet_brats/risk_aware_v1_a2_training/launch_a2_fold0.py$' || true)
printf 'MAIN_TRAINING_PID=%s\n' "${MAIN:-NONE}"
if [ -n "${MAIN:-}" ]; then ps -p "$MAIN" -o pid,ppid,etime,stat,cmd; printf 'DATALOADER_CHILDREN=%s\n' "$(pgrep -P "$MAIN" | wc -l)"; fi
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.free --format=csv,noheader,nounits
printf 'A2_OUTPUT=%s\n' "$A2"
find "$A2" -maxdepth 1 -type f \( -name 'training_log*.txt' -o -name 'checkpoint*.pth' -o -name 'progress.png' \) -printf '%TY-%Tm-%TdT%TH:%TM:%TS %s %p\n' 2>/dev/null | sort || true
LOG=$(find "$A2" -maxdepth 1 -name 'training_log*.txt' -type f 2>/dev/null | sort | tail -1)
if [ -n "${LOG:-}" ]; then tail -50 "$LOG"; grep -Ein 'nan|inf|out of memory|oom|traceback|shape mismatch|importerror' "$LOG" | tail -20 || true; fi
python3 - "$A1" "$BEFORE" <<'PY'
from pathlib import Path
import sys,hashlib
root=Path(sys.argv[1]); before=Path(sys.argv[2]).read_text(); rows=[]
for p in sorted(x for x in root.rglob('*') if x.is_file()):
 h=hashlib.sha256(p.read_bytes()).hexdigest(); s=p.stat(); rows.append(f'{p.relative_to(root)}\t{s.st_size}\t{s.st_mtime_ns}\t{h}')
print('A1_DIRECTORY_UNCHANGED='+('YES' if '\n'.join(rows)+'\n'==before else 'NO'))
PY

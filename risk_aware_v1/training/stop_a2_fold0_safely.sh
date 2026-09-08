#!/usr/bin/env bash
set -euo pipefail
SESSION=a2_fold0_train
if ! tmux has-session -t "$SESSION" 2>/dev/null; then echo 'Session not found'; exit 1; fi
PANE_PID=$(tmux display-message -p -t "$SESSION" '#{pane_pid}')
echo "SESSION=$SESSION PANE_PID=$PANE_PID"
ps -o pid,ppid,etime,cmd --forest -g "$(ps -o sid= -p "$PANE_PID" | tr -d ' ')" || true
echo 'Sending SIGINT through tmux foreground terminal'
tmux send-keys -t "$SESSION" C-c
for _ in $(seq 1 60); do tmux has-session -t "$SESSION" 2>/dev/null || { echo 'Stopped safely'; exit 0; }; sleep 1; done
echo 'Still running after 60 seconds; no force kill was used.'
exit 2

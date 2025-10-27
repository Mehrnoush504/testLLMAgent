#!/usr/bin/env bash
# Simple runner: start scheduler in background and run FastAPI
export PYTHONPATH=$(pwd)
python -c "from app.scheduler import start_scheduler; start_scheduler(); import time; print('Scheduler started.');
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    pass
"

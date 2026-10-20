#!/bin/bash
set -e

cd /opt/albaydacourtbot
source /opt/albaydacourtbot/venv/bin/activate

mkdir -p /opt/albaydacourtbot/logs
exec python /opt/albaydacourtbot/bot.py >> /opt/albaydacourtbot/logs/bot.log 2>&1

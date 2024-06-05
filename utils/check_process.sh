#!/bin/bash

# Путь к вашему скрипту
SCRIPT_PATH="$(dirname "$0")/zapier.py"
NOHUP_PATH="$(dirname "$0")/nohup.out"

# Проверяем, запущен ли процесс
if ps aux | grep "$SCRIPT_PATH" | grep -v grep > /dev/null; then
  echo "Process is running"
else
  echo "Process is not running"

  rm "$NOHUP_PATH"
  nohup python3 "$SCRIPT_PATH" &

# Очищаем nohup.out, если его размер превышает 10 МБ
if [ $(stat -c%s "$NOHUP_PATH") -gt 10000000 ]; then
    > "$NOHUP_PATH"
fi
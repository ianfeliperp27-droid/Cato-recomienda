#!/bin/bash
set -e

# Oryx descomprime el codigo en /tmp/<hash>/, no en /home/site/wwwroot.
# Detectamos donde quedo y nos paramos ahi para que gunicorn encuentre main.py.
APP_PATH=""
for d in /tmp/*/; do
  if [ -f "$d/main.py" ]; then
    APP_PATH="$d"
    break
  fi
done

if [ -n "$APP_PATH" ]; then
  cd "$APP_PATH"
else
  cd /home/site/wwwroot
  [ -d "Api" ] && cd Api
fi

mkdir -p static/uploads

exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
  --bind=0.0.0.0:8000 --timeout 600 \
  --access-logfile - --error-logfile - \
  main:app

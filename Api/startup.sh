#!/bin/bash
# Azure App Service - Cato Recomienda
# Si despliegas el contenido de Api/ directo a wwwroot, usa: FastApi:app
# Si despliegas la raiz del repo (con la carpeta Api/), usa: Api.FastApi:app

cd /home/site/wwwroot

# Si existe la carpeta Api/, entrar a ella
if [ -d "Api" ]; then
  cd Api
fi

# Instalar dependencias por si Oryx no las dejo bien
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Levantar el servidor
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --timeout 600 FastApi:app

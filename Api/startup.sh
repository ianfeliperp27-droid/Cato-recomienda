set -e

cd /home/site/wwwroot

# Si el deploy trajo la carpeta Api/, entrar a ella
if [ -d "Api" ]; then
  cd Api
fi

# Asegurar que static/uploads exista (donde caen las imagenes subidas)
mkdir -p static/uploads

# Instalar dependencias (Oryx ya lo hace, pero por si acaso)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 2 workers es lo recomendable para capa B1 (1 vCPU, ~1.75 GB RAM).
# Para capas mas grandes subirlo a (2 * vCPU + 1). timeout 600 da margen
# para uploads de imagenes y arranques en frio.
exec gunicorn \
  -w 2 \
  -k uvicorn.workers.UvicornWorker \
  --bind=0.0.0.0:8000 \
  --timeout 600 \
  --access-logfile - \
  --error-logfile - \
  FastApi:app

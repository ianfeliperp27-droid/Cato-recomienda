cat > startup.sh << 'EOF' 

#!/bin/bash 

# Script de inicio para FastAPI en Azure App Service 


# El puerto lo asigna Azure automáticamente 

PORT=${PORT:-8000} 

 

echo "==========================================" 

echo "🚀 Iniciando FastAPI en el puerto $PORT" 

echo "📁 Archivo principal: FastApi.py" 

echo "🔧 Instancia de FastAPI: app" 

echo "==========================================" 

 

# Iniciar la aplicación con Gunicorn 

# IMPORTANTE: Si su archivo no es FastApi.py o la instancia no es app, 

# cambien "FastApi:app" por "app" 

 

gunicorn -w 4 -k uvicorn.workers.UvicornWorker FastApi:app --bind 0.0.0.0:$PORT 

EOF 
"""
conftest.py - Configuración global de pytest para Cato-Recomienda
"""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-cato-2026"
os.environ["HTML_DIR"] = "./static"
os.environ["ENTORNO"] = "test"

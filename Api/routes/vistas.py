import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse


router = APIRouter(tags=["vistas"])

HTML_DIR = os.getenv("HTML_DIR", "./static")


@router.get("/")
def home():
    """Dashboard como pagina principal, sin login obligatorio."""
    return FileResponse(os.path.join(HTML_DIR, "dashboard.html"))


@router.get("/login")
def login_view():
    return FileResponse(os.path.join(HTML_DIR, "login.html"))


@router.get("/dashboard")
def dashboard_view():
    return FileResponse(os.path.join(HTML_DIR, "dashboard.html"))


@router.get("/health")
def health():
    return {"status": "ok", "service": "cato-recomienda"}


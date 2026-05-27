import os
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(tags=["vistas"])

HTML_DIR = os.getenv("HTML_DIR", "./static")


@router.get("/")
def home():
    return FileResponse(os.path.join(HTML_DIR, "dashboard.html"))


@router.get("/dashboard")
def dashboard_view():
    return FileResponse(os.path.join(HTML_DIR, "dashboard.html"))


@router.get("/health")
def health():
    return {"status": "ok", "service": "cato-recomienda"}

"""
ContrastCraft — Application Entry Point
FastAPI web server serving the REST API and the frontend single-page interface.
"""

from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .api.routes import router

app = FastAPI(
    title="ContrastCraft — Automated Web Accessibility Contrast Auditor",
    description="WCAG 2.1 & 2.2 Compliant Color Contrast & Accessibility Audit Tool",
    version="1.0.0"
)

# CORS middleware for local developer flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount frontend directories
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    css_dir = frontend_dir / "css"
    js_dir = frontend_dir / "js"

    @app.get("/favicon.ico", include_in_schema=False)
    def serve_favicon():
        return Response(status_code=204)

    @app.get("/js/app.bundle.js", include_in_schema=False)
    def serve_bundle():
        bundle_file = js_dir / "app.bundle.js"
        if bundle_file.exists():
            return FileResponse(
                str(bundle_file),
                media_type="application/javascript",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
        return Response(status_code=404)

    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(
                str(index_file),
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
        return {"message": "ContrastCraft Frontend not found at frontend/index.html"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

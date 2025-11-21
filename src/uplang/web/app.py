"""FastAPI application for web translation interface."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from uplang.web.api import create_router


def create_app(resourcepack_dir: Path) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="UpLang Translation Interface",
        description="Web interface for managing Minecraft modpack translations",
        version="1.0.0",
    )

    api_router = create_router(resourcepack_dir)
    app.include_router(api_router)

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():
        """Serve the main HTML page."""
        return FileResponse(static_dir / "index.html")

    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon to avoid 404 errors."""
        from fastapi.responses import Response

        return Response(status_code=204)

    return app


def start_server(
    resourcepack_dir: Path, host: str = "127.0.0.1", port: int = 8000
) -> None:
    """Start the web server."""
    import uvicorn

    app = create_app(resourcepack_dir)
    uvicorn.run(app, host=host, port=port)

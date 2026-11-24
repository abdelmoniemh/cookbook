"""App factory and the ``cookbook-serve`` entry point."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .. import db as dbmod
from .routers import catalog, imports, plans, recipes

# src/cookbook/server/app.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WEB_DIST = Path(os.environ.get("COOKBOOK_WEB_DIST", REPO_ROOT / "web" / "dist"))

NO_UI_MESSAGE = ("Cookbook API is running. The web UI has not been built yet: "
                 "run `cd web && npm ci && npm run build`, then restart. API: /api/health, docs: /docs\n")


def create_app(data_dir: Path | str | None = None, web_dist: Path | str | None = None) -> FastAPI:
    data_dir = Path(data_dir or os.environ.get("COOKBOOK_DATA_DIR") or dbmod.DEFAULT_DATA_DIR)
    web_dist = Path(web_dist or DEFAULT_WEB_DIST)

    # create the data folder, tables and WAL mode once at startup
    dbmod.connect(data_dir).close()

    app = FastAPI(title="Cookbook", version="0.1.0")
    app.state.data_dir = data_dir
    for r in (recipes.router, catalog.router, imports.router, plans.router):
        app.include_router(r)

    app.mount("/images", StaticFiles(directory=data_dir / "images", check_dir=False), name="images")

    index = web_dist / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path == "api" or path.startswith("api/") or path.startswith("images/"):
            raise HTTPException(404, "Not Found")
        if not index.is_file():
            if path == "":
                return PlainTextResponse(NO_UI_MESSAGE)
            raise HTTPException(404, "Not Found")
        if path:
            candidate = (web_dist / path).resolve()
            if candidate.is_file() and candidate.is_relative_to(web_dist.resolve()):
                return FileResponse(candidate)
        return FileResponse(index)

    return app


def main(argv: list[str] | None = None) -> int:
    import uvicorn

    ap = argparse.ArgumentParser(description="Serve the cookbook web app and API.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--data-dir", type=Path, default=dbmod.DEFAULT_DATA_DIR)
    ap.add_argument("--web-dist", type=Path, default=DEFAULT_WEB_DIST, help="built UI folder (default: web/dist)")
    args = ap.parse_args(argv)
    uvicorn.run(create_app(args.data_dir, args.web_dist), host=args.host, port=args.port, proxy_headers=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

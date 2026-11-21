import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import app.models  # Ensure all models are imported for metadata
from app.api.v1 import api_v1_router
from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Automatically populate seed problems and curriculum on fresh startup
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.problem import Problem
        from app.seeds.seed_data import seed_database

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Problem).limit(1))
            has_problems = result.scalars().first() is not None

        if not has_problems:
            await seed_database()
    except Exception as e:
        print(f"Auto-seed notification: {e}")

    yield
    await engine.dispose()


app = FastAPI(
    title="ThinkFree API",
    description="Thinking-first learning platform preventing AI over-reliance by scaffolding learning",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 router
app.include_router(api_v1_router)


# Single-Service Web Hosting: Serve React frontend if dist exists
dist_candidates = [
    Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "dist",
    Path(__file__).resolve().parent.parent.parent.parent / "apps" / "web" / "dist",
    Path("apps/web/dist"),
    Path("dist"),
]
web_dist_dir = next((p for p in dist_candidates if p.exists() and (p / "index.html").exists()), None)

if web_dist_dir:
    assets_dir = web_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        # Do not hijack API or docs
        if full_path.startswith(("api", "docs", "redoc", "openapi.json")):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = web_dist_dir / full_path
        if full_path and target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(web_dist_dir / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "app": "ThinkFree API",
            "version": "0.1.0",
            "docs": "/docs",
            "description": "Duolingo for independent thinking",
        }


def export_openapi_schema(output_path: str = "openapi.json"):
    """Export the current OpenAPI schema to a static JSON file for TypeScript codegen."""
    schema = app.openapi()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"OpenAPI schema successfully exported to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "export-openapi":
        export_openapi_schema()
    else:
        import uvicorn

        uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

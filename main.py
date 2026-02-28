"""
Instagram Clone API — application entry point.

Start the server with:
    uvicorn instagram_app.main:app --reload

Interactive docs available at:
    http://localhost:8000/docs
"""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from instagram_app.routers import users, posts, follows, likes, comments, feed, explore

app = FastAPI(
    title="Instagram Clone API",
    description="A full-featured Instagram-like REST API with in-memory storage.",
    version="1.0.0",
)

# ── Register all routers ──────────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(follows.router)
app.include_router(likes.router)
app.include_router(comments.router)
app.include_router(feed.router)
app.include_router(explore.router)

# ── Serve frontend static files ───────────────────────────────────────────────
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    """Serve the frontend SPA entry point (index.html)."""
    index_path = os.path.join(_STATIC_DIR, "index.html")
    return FileResponse(index_path)

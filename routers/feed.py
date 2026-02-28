"""
Feed endpoint.

Routes
------
GET /feed/{user_id}  — Personalised feed: posts from followed users, newest-first
"""

from typing import List

from fastapi import APIRouter, HTTPException

import instagram_app.storage as store
from instagram_app.models import PostOut
from instagram_app.routers.posts import _build_post_out

router = APIRouter(tags=["feed"])


@router.get("/feed/{user_id}", response_model=List[PostOut])
def get_feed(user_id: str) -> List[PostOut]:
    """Return a personalised feed for user_id.

    Includes posts from users that user_id follows, sorted newest-first.
    Does NOT include the user's own posts.
    Returns an empty list if the user follows nobody.
    Returns 404 if user_id does not exist.
    """
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    following_ids = store.follows.get(user_id, set())
    if not following_ids:
        return []

    feed_posts = [
        p for p in store.posts.values()
        if p["user_id"] in following_ids
    ]
    feed_posts.sort(key=lambda p: p["created_at"], reverse=True)
    return [_build_post_out(p) for p in feed_posts]

"""
Explore / discovery endpoints.

Routes
------
GET /explore                     — Recent posts from ALL users (newest-first, ?limit=N)
GET /explore/trending            — Top 10 hashtags by number of associated posts
GET /explore/hashtag/{tag}       — Posts tagged with a specific hashtag, newest-first

IMPORTANT: /explore/trending MUST be declared before /explore/hashtag/{tag}
so FastAPI does not greedily match "trending" as a {tag} path parameter.
"""

from typing import List

from fastapi import APIRouter, Query

import instagram_app.storage as store
from instagram_app.models import HashtagCount, PostOut
from instagram_app.routers.posts import _build_post_out

router = APIRouter(tags=["explore"])


@router.get("/explore", response_model=List[PostOut])
def explore_recent(
    limit: int = Query(default=20, ge=1, le=100, description="Max posts to return"),
) -> List[PostOut]:
    """Return the most recent posts from all users.

    Supports optional ?limit=N query parameter (default 20, max 100).
    """
    all_posts = sorted(store.posts.values(), key=lambda p: p["created_at"], reverse=True)
    return [_build_post_out(p) for p in all_posts[:limit]]


@router.get("/explore/trending", response_model=List[HashtagCount])
def explore_trending() -> List[HashtagCount]:
    """Return the top 10 hashtags ranked by number of associated posts.

    Hashtags with zero posts (orphaned entries) are excluded.

    NOTE: This route is intentionally declared BEFORE /explore/hashtag/{tag}
    to prevent FastAPI from matching "trending" as a {tag} path parameter.
    """
    tag_counts = [
        HashtagCount(tag=tag, count=len(post_ids))
        for tag, post_ids in store.hashtag_posts.items()
        if post_ids  # exclude tags with no posts
    ]
    tag_counts.sort(key=lambda tc: tc.count, reverse=True)
    return tag_counts[:10]


@router.get("/explore/hashtag/{tag}", response_model=List[PostOut])
def explore_by_hashtag(tag: str) -> List[PostOut]:
    """Return all posts that contain a given hashtag, newest-first.

    Tag lookup is case-insensitive — the tag is lowercased before lookup
    to match the normalized storage format set at post-creation time.
    Returns an empty list if no posts use the tag.
    """
    normalized_tag = tag.lower()
    post_ids = store.hashtag_posts.get(normalized_tag, set())
    tagged_posts = [store.posts[pid] for pid in post_ids if pid in store.posts]
    tagged_posts.sort(key=lambda p: p["created_at"], reverse=True)
    return [_build_post_out(p) for p in tagged_posts]

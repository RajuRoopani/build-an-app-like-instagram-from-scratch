"""
Post management endpoints.

Routes
------
POST   /posts                      — Create a new post (with hashtag extraction)
GET    /posts/{post_id}            — Fetch a single post
GET    /users/{user_id}/posts      — List all posts by a user (newest-first)
DELETE /posts/{post_id}            — Delete a post and all related data
"""

import re
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

import instagram_app.storage as store
from instagram_app.models import PostCreate, PostOut

router = APIRouter(tags=["posts"])

# Matches #word patterns; we lowercase tags before storage for case-insensitive lookup.
_HASHTAG_RE = re.compile(r"#(\w+)")


def _build_post_out(post: dict) -> PostOut:
    """Construct a PostOut from the raw storage dict, computing derived counts."""
    pid = post["id"]
    return PostOut(
        id=pid,
        user_id=post["user_id"],
        media_url=post["media_url"],
        media_type=post["media_type"],
        caption=post["caption"],
        hashtags=post["hashtags"],
        created_at=post["created_at"],
        like_count=len(store.likes.get(pid, set())),
        comment_count=len(store.post_comments.get(pid, [])),
    )


@router.post("/posts", status_code=201, response_model=PostOut)
def create_post(payload: PostCreate) -> PostOut:
    """Create a new photo or video post.

    Hashtags are extracted automatically from the caption via #word patterns
    and normalized to lowercase for consistent lookup.
    Returns 404 if the referenced user_id does not exist.
    """
    if payload.user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    pid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    # Normalize hashtags to lowercase so /explore/hashtag/{tag} lookups are consistent
    hashtags = [tag.lower() for tag in _HASHTAG_RE.findall(payload.caption)]

    post = {
        "id": pid,
        "user_id": payload.user_id,
        "media_url": payload.media_url,
        "media_type": payload.media_type,
        "caption": payload.caption,
        "hashtags": hashtags,
        "created_at": now,
    }
    store.posts[pid] = post

    # Initialise auxiliary indexes
    store.likes.setdefault(pid, set())
    store.post_comments.setdefault(pid, [])

    # Update hashtag index (tags already lowercased)
    for tag in hashtags:
        store.hashtag_posts.setdefault(tag, set()).add(pid)

    return _build_post_out(post)


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: str) -> PostOut:
    """Fetch a single post by ID.

    Returns 404 if the post does not exist.
    """
    post = store.posts.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _build_post_out(post)


@router.get("/users/{user_id}/posts", response_model=List[PostOut])
def get_user_posts(user_id: str) -> List[PostOut]:
    """Return all posts authored by a specific user, newest-first.

    Returns 404 if the user does not exist.
    """
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    user_posts = [p for p in store.posts.values() if p["user_id"] == user_id]
    user_posts.sort(key=lambda p: p["created_at"], reverse=True)
    return [_build_post_out(p) for p in user_posts]


@router.delete("/posts/{post_id}", status_code=200, response_model=dict)
def delete_post(post_id: str) -> dict:
    """Delete a post along with its likes, comments, and hashtag index entries.

    Cascade removes:
      - All likes on the post (store.likes)
      - All comments on the post (store.comments + store.post_comments)
      - Hashtag index entries pointing to this post (store.hashtag_posts)

    Returns 200 on success, 404 if the post does not exist.
    """
    post = store.posts.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Remove from hashtag index
    for tag in post.get("hashtags", []):
        tag_set = store.hashtag_posts.get(tag)
        if tag_set:
            tag_set.discard(post_id)

    # Cascade-delete all associated comments (from both indexes)
    for comment_id in store.post_comments.pop(post_id, []):
        store.comments.pop(comment_id, None)

    # Remove likes index for this post
    store.likes.pop(post_id, None)

    # Remove the post itself
    del store.posts[post_id]

    return {"detail": "Post deleted"}

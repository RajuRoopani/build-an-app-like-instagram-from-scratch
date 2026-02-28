"""
Like / unlike endpoints.

Routes
------
POST   /posts/{post_id}/like   — Like a post
DELETE /posts/{post_id}/like   — Unlike a post (user_id in query param)
GET    /posts/{post_id}/likes  — List users who liked a post
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query

import instagram_app.storage as store
from instagram_app.models import LikeAction, UserOut
from instagram_app.routers.users import _build_user_out

router = APIRouter(tags=["likes"])


@router.post("/posts/{post_id}/like", status_code=201)
def like_post(post_id: str, payload: LikeAction) -> dict:
    """Like a post on behalf of a user.

    Returns:
      404 if the post or user does not exist
      409 if the user already liked this post
    """
    if post_id not in store.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    if payload.user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    liked_by = store.likes.setdefault(post_id, set())
    if payload.user_id in liked_by:
        raise HTTPException(status_code=409, detail="Post already liked by this user")

    liked_by.add(payload.user_id)
    return {"detail": "Post liked"}


@router.delete("/posts/{post_id}/like", status_code=200, response_model=dict)
def unlike_post(
    post_id: str,
    user_id: str = Query(..., description="UUID of the user unliking the post"),
) -> dict:
    """Unlike a post.

    user_id is passed as a query parameter: DELETE /posts/{post_id}/like?user_id=...
    Returns 404 if the post does not exist or the user has not liked it.
    """
    if post_id not in store.posts:
        raise HTTPException(status_code=404, detail="Post not found")

    liked_by = store.likes.get(post_id, set())
    if user_id not in liked_by:
        raise HTTPException(status_code=404, detail="Like not found")

    liked_by.discard(user_id)
    return {"detail": "Post unliked"}


@router.get("/posts/{post_id}/likes", response_model=List[UserOut])
def get_post_likes(post_id: str) -> List[UserOut]:
    """Return a list of users who liked the given post.

    Returns 404 if the post does not exist.
    """
    if post_id not in store.posts:
        raise HTTPException(status_code=404, detail="Post not found")

    liked_by = store.likes.get(post_id, set())
    result = []
    for uid in liked_by:
        user = store.users.get(uid)
        if user:
            result.append(_build_user_out(user))
    return result

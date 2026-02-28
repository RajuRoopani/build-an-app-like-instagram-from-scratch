"""
Comment endpoints.

Routes
------
POST   /posts/{post_id}/comments  — Add a comment to a post
GET    /posts/{post_id}/comments  — List comments on a post (oldest-first)
DELETE /comments/{comment_id}     — Delete a comment
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

import instagram_app.storage as store
from instagram_app.models import CommentCreate, CommentOut

router = APIRouter(tags=["comments"])


def _build_comment_out(comment: dict) -> CommentOut:
    """Convert a raw storage dict into a CommentOut model."""
    return CommentOut(
        id=comment["id"],
        user_id=comment["user_id"],
        post_id=comment["post_id"],
        text=comment["text"],
        created_at=comment["created_at"],
    )


@router.post("/posts/{post_id}/comments", status_code=201, response_model=CommentOut)
def add_comment(post_id: str, payload: CommentCreate) -> CommentOut:
    """Add a comment to a post.

    Returns:
      422 if text is blank (enforced by Pydantic validator on CommentCreate)
      404 if the post or user does not exist
    """
    if post_id not in store.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    if payload.user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    cid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    comment = {
        "id": cid,
        "user_id": payload.user_id,
        "post_id": post_id,
        "text": payload.text,
        "created_at": now,
    }
    store.comments[cid] = comment
    store.post_comments.setdefault(post_id, []).append(cid)

    return _build_comment_out(comment)


@router.get("/posts/{post_id}/comments", response_model=List[CommentOut])
def get_comments(post_id: str) -> List[CommentOut]:
    """Return all comments on a post, ordered oldest-first.

    Returns 404 if the post does not exist.
    """
    if post_id not in store.posts:
        raise HTTPException(status_code=404, detail="Post not found")

    comment_ids = store.post_comments.get(post_id, [])
    result = []
    for cid in comment_ids:
        comment = store.comments.get(cid)
        if comment:
            result.append(_build_comment_out(comment))
    return result


@router.delete("/comments/{comment_id}", status_code=200, response_model=dict)
def delete_comment(comment_id: str) -> dict:
    """Delete a comment by its ID.

    Also removes the comment_id from the parent post's ordered comment list.
    Gracefully handles the case where the parent post was already deleted.
    Returns 404 if the comment does not exist.
    """
    comment = store.comments.get(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    post_id = comment["post_id"]
    # Remove from post's ordered list (graceful if post was already cascade-deleted)
    comment_list = store.post_comments.get(post_id, [])
    if comment_id in comment_list:
        comment_list.remove(comment_id)

    del store.comments[comment_id]
    return {"detail": "Comment deleted"}

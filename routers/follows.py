"""
Follow / unfollow endpoints.

Routes
------
POST   /users/{user_id}/follow/{target_id}  — Follow another user
DELETE /users/{user_id}/follow/{target_id}  — Unfollow a user
GET    /users/{user_id}/followers           — List users who follow user_id
GET    /users/{user_id}/following           — List users that user_id follows
"""

from typing import List

from fastapi import APIRouter, HTTPException

import instagram_app.storage as store
from instagram_app.models import UserOut
from instagram_app.routers.users import _build_user_out

router = APIRouter(tags=["follows"])


@router.post("/users/{user_id}/follow/{target_id}", status_code=201)
def follow_user(user_id: str, target_id: str) -> dict:
    """Follow another user.

    Returns:
      400 if user_id == target_id (self-follow not allowed)
      404 if either user does not exist
      409 if the follow relationship already exists
    """
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")
    if target_id not in store.users:
        raise HTTPException(status_code=404, detail="Target user not found")

    following_set = store.follows.setdefault(user_id, set())
    if target_id in following_set:
        raise HTTPException(status_code=409, detail="Already following this user")

    # Dual-write: update both indexes atomically
    following_set.add(target_id)
    store.followers.setdefault(target_id, set()).add(user_id)

    return {"detail": "Followed successfully"}


@router.delete("/users/{user_id}/follow/{target_id}", status_code=200, response_model=dict)
def unfollow_user(user_id: str, target_id: str) -> dict:
    """Unfollow a user.

    Dual-writes to both follow indexes (follows + followers) atomically.
    Returns 404 if either user is not found or the follow relationship
    does not currently exist.
    """
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")
    if target_id not in store.users:
        raise HTTPException(status_code=404, detail="Target user not found")

    following_set = store.follows.get(user_id, set())
    if target_id not in following_set:
        raise HTTPException(status_code=404, detail="Not following this user")

    # Dual-write: remove from both indexes
    following_set.discard(target_id)
    store.followers.get(target_id, set()).discard(user_id)

    return {"detail": "Unfollowed successfully"}


@router.get("/users/{user_id}/followers", response_model=List[UserOut])
def get_followers(user_id: str) -> List[UserOut]:
    """Return the list of users who follow user_id.

    Returns 404 if user_id does not exist.
    """
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    follower_ids = store.followers.get(user_id, set())
    result = []
    for fid in follower_ids:
        user = store.users.get(fid)
        if user:
            result.append(_build_user_out(user))
    return result


@router.get("/users/{user_id}/following", response_model=List[UserOut])
def get_following(user_id: str) -> List[UserOut]:
    """Return the list of users that user_id follows.

    Returns 404 if user_id does not exist.
    """
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")

    following_ids = store.follows.get(user_id, set())
    result = []
    for fid in following_ids:
        user = store.users.get(fid)
        if user:
            result.append(_build_user_out(user))
    return result

"""
User management endpoints.

Routes
------
POST   /users              — Register a new user
GET    /users/{user_id}    — Fetch a user's profile
PUT    /users/{user_id}    — Update a user's profile
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

import instagram_app.storage as store
from instagram_app.models import UserCreate, UserOut, UserUpdate

router = APIRouter(tags=["users"])


def _build_user_out(user: dict) -> UserOut:
    """Construct a UserOut from the raw storage dict, computing derived counts."""
    uid = user["id"]
    return UserOut(
        id=uid,
        username=user["username"],
        display_name=user["display_name"],
        bio=user["bio"],
        profile_pic_url=user["profile_pic_url"],
        created_at=user["created_at"],
        follower_count=len(store.followers.get(uid, set())),
        following_count=len(store.follows.get(uid, set())),
        post_count=sum(1 for p in store.posts.values() if p["user_id"] == uid),
    )


@router.post("/users", status_code=201, response_model=UserOut)
def create_user(payload: UserCreate) -> UserOut:
    """Register a new user.

    Returns 409 if the username is already taken.
    """
    # Enforce unique username
    if any(u["username"] == payload.username for u in store.users.values()):
        raise HTTPException(status_code=409, detail="Username already taken")

    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    user = {
        "id": uid,
        "username": payload.username,
        "display_name": payload.display_name,
        "bio": payload.bio,
        "profile_pic_url": payload.profile_pic_url,
        "created_at": now,
    }
    store.users[uid] = user
    # Initialise follow indexes
    store.follows.setdefault(uid, set())
    store.followers.setdefault(uid, set())
    return _build_user_out(user)


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str) -> UserOut:
    """Fetch a user profile by ID.

    Returns 404 if the user does not exist.
    """
    user = store.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_user_out(user)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate) -> UserOut:
    """Update a user's profile fields (display_name, bio, profile_pic_url).

    Only provided (non-None) fields are updated.
    Returns 404 if the user does not exist.
    """
    user = store.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.display_name is not None:
        user["display_name"] = payload.display_name
    if payload.bio is not None:
        user["bio"] = payload.bio
    if payload.profile_pic_url is not None:
        user["profile_pic_url"] = payload.profile_pic_url

    return _build_user_out(user)

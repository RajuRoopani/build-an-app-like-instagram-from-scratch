"""
Pydantic request/response models for the Instagram Clone API.

All models use strict type hints and Field validators where needed.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ── User models ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for registering a new user."""

    username: str = Field(..., min_length=1, description="Unique handle (e.g. 'john_doe')")
    display_name: str = Field(..., min_length=1, description="Human-readable name")
    bio: str = Field(default="", description="Short user biography")
    profile_pic_url: str = Field(default="", description="URL of the profile picture")


class UserUpdate(BaseModel):
    """Payload for updating an existing user's profile.  All fields optional."""

    display_name: Optional[str] = Field(default=None, description="New display name")
    bio: Optional[str] = Field(default=None, description="New biography")
    profile_pic_url: Optional[str] = Field(default=None, description="New profile picture URL")


class UserOut(BaseModel):
    """Full user representation returned by the API."""

    id: str = Field(..., description="UUID of the user")
    username: str
    display_name: str
    bio: str
    profile_pic_url: str
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")
    follower_count: int = Field(..., ge=0)
    following_count: int = Field(..., ge=0)
    post_count: int = Field(..., ge=0)


# ── Post models ───────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    """Payload for creating a new post."""

    user_id: str = Field(..., description="UUID of the post author")
    media_url: str = Field(..., min_length=1, description="URL of the uploaded media")
    media_type: Literal["image", "video"] = Field(..., description="Media type discriminator")
    caption: str = Field(default="", description="Caption text — may include #hashtags")


class PostOut(BaseModel):
    """Full post representation returned by the API."""

    id: str = Field(..., description="UUID of the post")
    user_id: str
    media_url: str
    media_type: Literal["image", "video"]
    caption: str
    hashtags: List[str] = Field(default_factory=list, description="Extracted hashtag words (no #)")
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")
    like_count: int = Field(..., ge=0)
    comment_count: int = Field(..., ge=0)


# ── Comment models ────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    """Payload for posting a comment."""

    user_id: str = Field(..., description="UUID of the commenter")
    text: str = Field(..., description="Comment body — must be non-empty")

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        """Reject comments that are empty or whitespace-only."""
        if not v.strip():
            raise ValueError("Comment text must not be blank")
        return v


class CommentOut(BaseModel):
    """Full comment representation returned by the API."""

    id: str = Field(..., description="UUID of the comment")
    user_id: str
    post_id: str
    text: str
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")


# ── Like model ────────────────────────────────────────────────────────────────

class LikeAction(BaseModel):
    """Payload for liking or unliking a post."""

    user_id: str = Field(..., description="UUID of the user performing the action")


# ── Hashtag/explore model ─────────────────────────────────────────────────────

class HashtagCount(BaseModel):
    """Trending hashtag entry."""

    tag: str = Field(..., description="Hashtag word (no #)")
    count: int = Field(..., ge=0, description="Number of posts using this tag")

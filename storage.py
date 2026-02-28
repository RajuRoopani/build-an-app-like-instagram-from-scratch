"""
Centralized in-memory storage for the Instagram Clone API.

All collections are module-level dicts/sets so every router shares
the same reference. Call reset_storage() between tests to wipe state.

Dual-index pattern for follows:
  - follows[user_id]    = set of target_ids  that user_id follows
  - followers[user_id]  = set of follower_ids that follow user_id
Both sides are updated atomically in the router helpers.
"""

from typing import Dict, List, Set

# ── User store ────────────────────────────────────────────────────────────────
users: Dict[str, dict] = {}
"""Keyed by user_id (UUID string) → user dict."""

# ── Post store ────────────────────────────────────────────────────────────────
posts: Dict[str, dict] = {}
"""Keyed by post_id (UUID string) → post dict."""

# ── Follow indexes ────────────────────────────────────────────────────────────
follows: Dict[str, Set[str]] = {}
"""user_id → set of target_ids this user follows."""

followers: Dict[str, Set[str]] = {}
"""user_id → set of follower_ids who follow this user (reverse index)."""

# ── Likes store ───────────────────────────────────────────────────────────────
likes: Dict[str, Set[str]] = {}
"""post_id → set of user_ids who liked the post."""

# ── Comment stores ────────────────────────────────────────────────────────────
comments: Dict[str, dict] = {}
"""Keyed by comment_id (UUID string) → comment dict."""

post_comments: Dict[str, List[str]] = {}
"""post_id → ordered list of comment_ids (oldest first)."""

# ── Hashtag index ─────────────────────────────────────────────────────────────
hashtag_posts: Dict[str, Set[str]] = {}
"""tag (lowercase, no #) → set of post_ids that contain that tag."""


def reset_storage() -> None:
    """Clear ALL in-memory collections.  Called by the test suite between runs."""
    users.clear()
    posts.clear()
    follows.clear()
    followers.clear()
    likes.clear()
    comments.clear()
    post_comments.clear()
    hashtag_posts.clear()

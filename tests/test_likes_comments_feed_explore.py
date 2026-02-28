"""
Test suite for likes, comments, feed, and explore endpoints.

Tests cover:
  - Likes: create, delete, conflicts, retrieval, count updates
  - Comments: create, blank validation, retrieval (ordering), deletion, count updates
  - Feed: empty feed, followed users, self-exclusion, 404 cases, follow + fetch
  - Explore: recent posts with pagination, hashtag filtering, trending hashtags
"""

import pytest
from fastapi.testclient import TestClient


# ────────────────────────────────────────────────────────────────────────────
# Helper functions for test setup
# ────────────────────────────────────────────────────────────────────────────


def _create_user(client: TestClient, username: str = "testuser", display_name: str = "Test User") -> dict:
    """Create a user and return the response JSON."""
    resp = client.post("/users", json={
        "username": username,
        "display_name": display_name,
    })
    assert resp.status_code == 201
    return resp.json()


def _create_post(
    client: TestClient,
    user_id: str,
    caption: str = "Hello #world",
    media_url: str = "https://img.com/1.jpg",
) -> dict:
    """Create a post and return the response JSON."""
    resp = client.post("/posts", json={
        "user_id": user_id,
        "media_url": media_url,
        "media_type": "image",
        "caption": caption,
    })
    assert resp.status_code == 201
    return resp.json()


# ────────────────────────────────────────────────────────────────────────────
# LIKE TESTS (8 tests)
# ────────────────────────────────────────────────────────────────────────────


class TestLikes:
    """Test suite for like/unlike endpoints."""

    def test_like_post_success(self, client: TestClient) -> None:
        """POST /posts/{post_id}/like → 201, post liked."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})
        assert resp.status_code == 201
        assert resp.json()["detail"] == "Post liked"

    def test_like_post_nonexistent_post(self, client: TestClient) -> None:
        """POST /posts/{non_existent_post_id}/like → 404."""
        user = _create_user(client)

        resp = client.post("/posts/invalid-post-id/like", json={"user_id": user["id"]})
        assert resp.status_code == 404
        assert "Post not found" in resp.json()["detail"]

    def test_like_post_nonexistent_user(self, client: TestClient) -> None:
        """POST /posts/{post_id}/like with non-existent user → 404."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.post(f"/posts/{post['id']}/like", json={"user_id": "invalid-user-id"})
        assert resp.status_code == 404
        assert "User not found" in resp.json()["detail"]

    def test_like_post_already_liked(self, client: TestClient) -> None:
        """POST /posts/{post_id}/like when already liked → 409."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # First like succeeds
        resp1 = client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})
        assert resp1.status_code == 201

        # Second like fails with 409 Conflict
        resp2 = client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})
        assert resp2.status_code == 409
        assert "already liked" in resp2.json()["detail"]

    def test_unlike_post_success(self, client: TestClient) -> None:
        """DELETE /posts/{post_id}/like → 200, post unliked."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # First, like the post
        client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})

        # Then, unlike it
        resp = client.delete(f"/posts/{post['id']}/like?user_id={user['id']}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Post unliked"

    def test_unlike_post_not_liked(self, client: TestClient) -> None:
        """DELETE /posts/{post_id}/like when not liked → 404."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.delete(f"/posts/{post['id']}/like?user_id={user['id']}")
        assert resp.status_code == 404
        assert "Like not found" in resp.json()["detail"]

    def test_get_post_likes_success(self, client: TestClient) -> None:
        """GET /posts/{post_id}/likes → list of UserOut (likers)."""
        user1 = _create_user(client, username="user1", display_name="User 1")
        user2 = _create_user(client, username="user2", display_name="User 2")
        post = _create_post(client, user1["id"])

        # Both users like the post
        client.post(f"/posts/{post['id']}/like", json={"user_id": user1["id"]})
        client.post(f"/posts/{post['id']}/like", json={"user_id": user2["id"]})

        # Get the list of likers
        resp = client.get(f"/posts/{post['id']}/likes")
        assert resp.status_code == 200
        likers = resp.json()
        assert len(likers) == 2
        liker_ids = {u["id"] for u in likers}
        assert user1["id"] in liker_ids
        assert user2["id"] in liker_ids

    def test_like_count_increments(self, client: TestClient) -> None:
        """GET /posts/{post_id} → like_count reflects current likes."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # Post starts with 0 likes
        assert post["like_count"] == 0

        # Like the post
        client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})

        # Fetch post again and check like_count
        resp = client.get(f"/posts/{post['id']}")
        updated_post = resp.json()
        assert updated_post["like_count"] == 1


# ────────────────────────────────────────────────────────────────────────────
# COMMENT TESTS (9 tests)
# ────────────────────────────────────────────────────────────────────────────


class TestComments:
    """Test suite for comment endpoints."""

    def test_add_comment_success(self, client: TestClient) -> None:
        """POST /posts/{post_id}/comments → 201, returns CommentOut."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "Great post!",
        })
        assert resp.status_code == 201
        comment = resp.json()
        assert comment["id"] is not None
        assert comment["user_id"] == user["id"]
        assert comment["post_id"] == post["id"]
        assert comment["text"] == "Great post!"
        assert comment["created_at"] is not None

    def test_add_comment_to_nonexistent_post(self, client: TestClient) -> None:
        """POST /posts/{non_existent_post_id}/comments → 404."""
        user = _create_user(client)

        resp = client.post("/posts/invalid-post-id/comments", json={
            "user_id": user["id"],
            "text": "Great post!",
        })
        assert resp.status_code == 404
        assert "Post not found" in resp.json()["detail"]

    def test_add_comment_nonexistent_user(self, client: TestClient) -> None:
        """POST /posts/{post_id}/comments with non-existent user → 404."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": "invalid-user-id",
            "text": "Great post!",
        })
        assert resp.status_code == 404
        assert "User not found" in resp.json()["detail"]

    def test_add_comment_blank_text(self, client: TestClient) -> None:
        """POST /posts/{post_id}/comments with blank text → 422 (Pydantic validator)."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        resp = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "   ",  # whitespace only
        })
        assert resp.status_code == 422

    def test_get_comments_ordered_oldest_first(self, client: TestClient) -> None:
        """GET /posts/{post_id}/comments → comments ordered oldest-first."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # Add three comments
        resp1 = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "First comment",
        })
        comment1 = resp1.json()

        resp2 = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "Second comment",
        })
        comment2 = resp2.json()

        resp3 = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "Third comment",
        })
        comment3 = resp3.json()

        # Retrieve comments
        resp = client.get(f"/posts/{post['id']}/comments")
        assert resp.status_code == 200
        comments = resp.json()
        assert len(comments) == 3
        assert comments[0]["id"] == comment1["id"]
        assert comments[1]["id"] == comment2["id"]
        assert comments[2]["id"] == comment3["id"]

    def test_get_comments_nonexistent_post(self, client: TestClient) -> None:
        """GET /posts/{non_existent_post_id}/comments → 404."""
        resp = client.get("/posts/invalid-post-id/comments")
        assert resp.status_code == 404
        assert "Post not found" in resp.json()["detail"]

    def test_delete_comment_success(self, client: TestClient) -> None:
        """DELETE /comments/{comment_id} → 200, comment removed."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # Create a comment
        resp1 = client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "Test comment",
        })
        comment = resp1.json()

        # Delete it
        resp2 = client.delete(f"/comments/{comment['id']}")
        assert resp2.status_code == 200
        assert resp2.json()["detail"] == "Comment deleted"

        # Verify it's gone
        resp3 = client.get(f"/posts/{post['id']}/comments")
        assert len(resp3.json()) == 0

    def test_delete_nonexistent_comment(self, client: TestClient) -> None:
        """DELETE /comments/{non_existent_comment_id} → 404."""
        resp = client.delete("/comments/invalid-comment-id")
        assert resp.status_code == 404
        assert "Comment not found" in resp.json()["detail"]

    def test_comment_count_increments(self, client: TestClient) -> None:
        """GET /posts/{post_id} → comment_count reflects current comments."""
        user = _create_user(client)
        post = _create_post(client, user["id"])

        # Post starts with 0 comments
        assert post["comment_count"] == 0

        # Add a comment
        client.post(f"/posts/{post['id']}/comments", json={
            "user_id": user["id"],
            "text": "Test comment",
        })

        # Fetch post again and check comment_count
        resp = client.get(f"/posts/{post['id']}")
        updated_post = resp.json()
        assert updated_post["comment_count"] == 1


# ────────────────────────────────────────────────────────────────────────────
# FEED TESTS (5 tests)
# ────────────────────────────────────────────────────────────────────────────


class TestFeed:
    """Test suite for feed endpoint."""

    def test_feed_empty_for_user_following_nobody(self, client: TestClient) -> None:
        """GET /feed/{user_id} for user with no follows → empty list."""
        user = _create_user(client)

        resp = client.get(f"/feed/{user['id']}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_feed_shows_followed_users_newest_first(self, client: TestClient) -> None:
        """GET /feed/{user_id} → shows posts from followed users, newest-first."""
        user_a = _create_user(client, username="user_a", display_name="User A")
        user_b = _create_user(client, username="user_b", display_name="User B")
        follower = _create_user(client, username="follower", display_name="Follower")

        # User A and B post
        post_a = _create_post(client, user_a["id"], caption="Post A")
        post_b = _create_post(client, user_b["id"], caption="Post B")

        # Follower follows A and B
        client.post(f"/users/{follower['id']}/follow/{user_a['id']}")
        client.post(f"/users/{follower['id']}/follow/{user_b['id']}")

        # Get feed
        resp = client.get(f"/feed/{follower['id']}")
        assert resp.status_code == 200
        posts = resp.json()
        assert len(posts) == 2
        # Posts should be newest-first (B posted after A)
        assert posts[0]["id"] == post_b["id"]
        assert posts[1]["id"] == post_a["id"]

    def test_feed_excludes_users_own_posts(self, client: TestClient) -> None:
        """GET /feed/{user_id} → does NOT include user's own posts."""
        user = _create_user(client)
        other_user = _create_user(client, username="other", display_name="Other")

        # User posts
        _create_post(client, user["id"], caption="My post")

        # Other user posts
        _create_post(client, other_user["id"], caption="Other's post")

        # User follows other_user
        client.post(f"/users/{user['id']}/follow/{other_user['id']}")

        # Get user's feed
        resp = client.get(f"/feed/{user['id']}")
        assert resp.status_code == 200
        posts = resp.json()
        assert len(posts) == 1
        assert posts[0]["user_id"] == other_user["id"]

    def test_feed_nonexistent_user(self, client: TestClient) -> None:
        """GET /feed/{non_existent_user_id} → 404."""
        resp = client.get("/feed/invalid-user-id")
        assert resp.status_code == 404
        assert "User not found" in resp.json()["detail"]

    def test_feed_updates_after_follow(self, client: TestClient) -> None:
        """GET /feed/{user_id} → posts appear after following a user."""
        user_a = _create_user(client, username="user_a", display_name="User A")
        follower = _create_user(client, username="follower", display_name="Follower")

        # User A posts
        post = _create_post(client, user_a["id"], caption="A's post")

        # Feed is empty before follow
        resp1 = client.get(f"/feed/{follower['id']}")
        assert len(resp1.json()) == 0

        # Follower follows A
        client.post(f"/users/{follower['id']}/follow/{user_a['id']}")

        # Feed now includes A's post
        resp2 = client.get(f"/feed/{follower['id']}")
        assert len(resp2.json()) == 1
        assert resp2.json()[0]["id"] == post["id"]


# ────────────────────────────────────────────────────────────────────────────
# EXPLORE TESTS (5 tests)
# ────────────────────────────────────────────────────────────────────────────


class TestExplore:
    """Test suite for explore endpoints."""

    def test_explore_recent_returns_all_posts_newest_first(self, client: TestClient) -> None:
        """GET /explore → returns all posts newest-first."""
        user1 = _create_user(client, username="user1", display_name="User 1")
        user2 = _create_user(client, username="user2", display_name="User 2")

        # Create posts
        post1 = _create_post(client, user1["id"], caption="Post 1")
        post2 = _create_post(client, user2["id"], caption="Post 2")

        # Get explore
        resp = client.get("/explore")
        assert resp.status_code == 200
        posts = resp.json()
        assert len(posts) == 2
        # Newest first: post2 before post1
        assert posts[0]["id"] == post2["id"]
        assert posts[1]["id"] == post1["id"]

    def test_explore_with_limit_query_param(self, client: TestClient) -> None:
        """GET /explore?limit=2 → returns max 2 posts."""
        user = _create_user(client)

        # Create 5 posts
        for i in range(5):
            _create_post(client, user["id"], caption=f"Post {i}")

        # Get explore with limit=2
        resp = client.get("/explore?limit=2")
        assert resp.status_code == 200
        posts = resp.json()
        assert len(posts) == 2

    def test_explore_hashtag_returns_correct_posts(self, client: TestClient) -> None:
        """GET /explore/hashtag/{tag} → returns posts with that hashtag."""
        user1 = _create_user(client, username="user1", display_name="User 1")
        user2 = _create_user(client, username="user2", display_name="User 2")

        # Create posts with #python and #javascript
        post1 = _create_post(client, user1["id"], caption="Learning #python #webdev")
        post2 = _create_post(client, user2["id"], caption="Learning #javascript")
        post3 = _create_post(client, user1["id"], caption="More #python tips")

        # Get posts with #python
        resp = client.get("/explore/hashtag/python")
        assert resp.status_code == 200
        posts = resp.json()
        assert len(posts) == 2
        post_ids = {p["id"] for p in posts}
        assert post1["id"] in post_ids
        assert post3["id"] in post_ids
        assert post2["id"] not in post_ids

    def test_explore_hashtag_no_matching_posts(self, client: TestClient) -> None:
        """GET /explore/hashtag/{tag} with no matches → empty list."""
        user = _create_user(client)
        _create_post(client, user["id"], caption="Post with #python")

        resp = client.get("/explore/hashtag/nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_explore_trending_returns_hashtags_by_count(self, client: TestClient) -> None:
        """GET /explore/trending → returns hashtags sorted by post count."""
        user = _create_user(client)

        # Create posts with various hashtags
        _create_post(client, user["id"], caption="Post #python #webdev")
        _create_post(client, user["id"], caption="Post #python")
        _create_post(client, user["id"], caption="Post #javascript #webdev")
        _create_post(client, user["id"], caption="Post #devops")

        # Get trending
        resp = client.get("/explore/trending")
        assert resp.status_code == 200
        hashtags = resp.json()

        # Verify ordering: webdev (2), python (2), javascript (1), devops (1)
        # Among ties, order may vary, but top should have count=2
        assert hashtags[0]["count"] == 2
        assert hashtags[1]["count"] == 2
        assert hashtags[2]["count"] == 1
        assert hashtags[3]["count"] == 1

        # Verify all expected tags are present
        tag_names = {ht["tag"] for ht in hashtags}
        assert "python" in tag_names
        assert "webdev" in tag_names
        assert "javascript" in tag_names
        assert "devops" in tag_names

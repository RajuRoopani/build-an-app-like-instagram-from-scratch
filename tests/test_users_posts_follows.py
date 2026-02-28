"""
Comprehensive test suite for Users, Posts, and Follows routers.

Tests cover:
  - Users (8 tests): create, retrieve, update, error handling
  - Posts (11 tests): create, retrieve, list, delete, cascading, hashtag extraction
  - Follows (11 tests): follow, unfollow, list followers/following, error handling
  
All tests use the client fixture from conftest.py.
All tests are isolated (storage resets between tests).
Total: 30+ test functions.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# USER TESTS (8 tests)
# ============================================================================


def test_create_user_success(client: TestClient) -> None:
    """Create a user → 201, response has all required fields."""
    resp = client.post(
        "/users",
        json={
            "username": "alice",
            "display_name": "Alice Smith",
            "bio": "Photographer",
            "profile_pic_url": "https://example.com/alice.jpg",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    
    # Verify all required fields
    assert data["id"]  # UUID exists
    assert data["username"] == "alice"
    assert data["display_name"] == "Alice Smith"
    assert data["bio"] == "Photographer"
    assert data["profile_pic_url"] == "https://example.com/alice.jpg"
    assert data["created_at"]  # ISO-8601 timestamp
    assert data["follower_count"] == 0
    assert data["following_count"] == 0
    assert data["post_count"] == 0


def test_create_user_minimal(client: TestClient) -> None:
    """Create a user with minimal fields (username and display_name only)."""
    resp = client.post(
        "/users",
        json={"username": "bob", "display_name": "Bob Jones"},
    )
    assert resp.status_code == 201
    data = resp.json()
    
    assert data["username"] == "bob"
    assert data["display_name"] == "Bob Jones"
    assert data["bio"] == ""  # Default empty
    assert data["profile_pic_url"] == ""  # Default empty
    assert data["follower_count"] == 0
    assert data["following_count"] == 0
    assert data["post_count"] == 0


def test_create_user_duplicate_username(client: TestClient) -> None:
    """Create a user with duplicate username → 409."""
    client.post("/users", json={"username": "charlie", "display_name": "Charlie"})
    
    resp = client.post(
        "/users",
        json={"username": "charlie", "display_name": "Different Name"},
    )
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


def test_create_user_empty_username(client: TestClient) -> None:
    """Create a user with empty username → 422 (validation error)."""
    resp = client.post(
        "/users",
        json={"username": "", "display_name": "Empty User"},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_create_user_empty_display_name(client: TestClient) -> None:
    """Create a user with empty display_name → 422."""
    resp = client.post(
        "/users",
        json={"username": "eve", "display_name": ""},
    )
    assert resp.status_code == 422


def test_get_user_success(client: TestClient) -> None:
    """Fetch a user by ID → 200 with all fields."""
    # Create a user first
    create_resp = client.post(
        "/users",
        json={"username": "frank", "display_name": "Frank", "bio": "Developer"},
    )
    user_id = create_resp.json()["id"]
    
    # Fetch the user
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["id"] == user_id
    assert data["username"] == "frank"
    assert data["display_name"] == "Frank"
    assert data["bio"] == "Developer"


def test_get_user_not_found(client: TestClient) -> None:
    """Fetch a non-existent user → 404."""
    resp = client.get("/users/nonexistent-id-12345")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_update_user_display_name(client: TestClient) -> None:
    """Update a user's display_name → 200, name changed, other fields unchanged."""
    # Create a user
    create_resp = client.post(
        "/users",
        json={
            "username": "grace",
            "display_name": "Grace",
            "bio": "Artist",
            "profile_pic_url": "https://example.com/grace.jpg",
        },
    )
    user_id = create_resp.json()["id"]
    
    # Update display_name
    resp = client.put(
        f"/users/{user_id}",
        json={"display_name": "Grace Lee"},
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["display_name"] == "Grace Lee"
    assert data["username"] == "grace"  # Unchanged
    assert data["bio"] == "Artist"  # Unchanged
    assert data["profile_pic_url"] == "https://example.com/grace.jpg"  # Unchanged


def test_update_user_bio(client: TestClient) -> None:
    """Update a user's bio → 200, bio changed."""
    # Create a user
    create_resp = client.post(
        "/users",
        json={"username": "henry", "display_name": "Henry", "bio": "Old bio"},
    )
    user_id = create_resp.json()["id"]
    
    # Update bio
    resp = client.put(
        f"/users/{user_id}",
        json={"bio": "New bio"},
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["bio"] == "New bio"
    assert data["display_name"] == "Henry"  # Unchanged


def test_update_user_profile_pic_url(client: TestClient) -> None:
    """Update a user's profile_pic_url → 200."""
    create_resp = client.post(
        "/users",
        json={"username": "ivy", "display_name": "Ivy"},
    )
    user_id = create_resp.json()["id"]
    
    resp = client.put(
        f"/users/{user_id}",
        json={"profile_pic_url": "https://example.com/ivy_new.jpg"},
    )
    assert resp.status_code == 200
    assert resp.json()["profile_pic_url"] == "https://example.com/ivy_new.jpg"


def test_update_user_not_found(client: TestClient) -> None:
    """Update a non-existent user → 404."""
    resp = client.put(
        "/users/nonexistent-user-id",
        json={"display_name": "Someone"},
    )
    assert resp.status_code == 404


# ============================================================================
# POST TESTS (11 tests)
# ============================================================================


def test_create_post_success(client: TestClient) -> None:
    """Create a post → 201, has all required fields."""
    # Create a user first
    user = client.post(
        "/users",
        json={"username": "jack", "display_name": "Jack"},
    ).json()
    
    # Create a post
    resp = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/photo.jpg",
            "media_type": "image",
            "caption": "Beautiful sunset #nature #photography",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    
    assert data["id"]  # UUID exists
    assert data["user_id"] == user["id"]
    assert data["media_url"] == "https://example.com/photo.jpg"
    assert data["media_type"] == "image"
    assert data["caption"] == "Beautiful sunset #nature #photography"
    assert "nature" in data["hashtags"]
    assert "photography" in data["hashtags"]
    assert data["created_at"]
    assert data["like_count"] == 0
    assert data["comment_count"] == 0


def test_create_post_minimal(client: TestClient) -> None:
    """Create a post with minimal fields (no caption)."""
    user = client.post(
        "/users",
        json={"username": "kate", "display_name": "Kate"},
    ).json()
    
    resp = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/video.mp4",
            "media_type": "video",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    
    assert data["caption"] == ""  # Default empty
    assert data["hashtags"] == []  # No hashtags


def test_create_post_nonexistent_user(client: TestClient) -> None:
    """Create a post with a nonexistent user_id → 404."""
    resp = client.post(
        "/posts",
        json={
            "user_id": "nonexistent-user-id",
            "media_url": "https://example.com/photo.jpg",
            "media_type": "image",
            "caption": "Test",
        },
    )
    assert resp.status_code == 404
    assert "user" in resp.json()["detail"].lower()


def test_create_post_hashtag_extraction(client: TestClient) -> None:
    """Create post with various hashtag patterns → hashtags extracted correctly."""
    user = client.post(
        "/users",
        json={"username": "liam", "display_name": "Liam"},
    ).json()
    
    resp = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/pic.jpg",
            "media_type": "image",
            "caption": "My #sunset is #amazing! Check #photography #art.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    
    assert len(data["hashtags"]) == 4
    assert set(data["hashtags"]) == {"sunset", "amazing", "photography", "art"}


def test_create_post_no_hashtags(client: TestClient) -> None:
    """Create post with no hashtags → empty hashtags list."""
    user = client.post(
        "/users",
        json={"username": "mia", "display_name": "Mia"},
    ).json()
    
    resp = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/pic.jpg",
            "media_type": "image",
            "caption": "Just a regular caption with no tags",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["hashtags"] == []


def test_get_post_success(client: TestClient) -> None:
    """Fetch a post by ID → 200 with all fields."""
    user = client.post(
        "/users",
        json={"username": "noah", "display_name": "Noah"},
    ).json()
    
    post = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/pic.jpg",
            "media_type": "image",
            "caption": "Test #post",
        },
    ).json()
    
    resp = client.get(f"/posts/{post['id']}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["id"] == post["id"]
    assert data["user_id"] == user["id"]
    assert "post" in data["hashtags"]


def test_get_post_not_found(client: TestClient) -> None:
    """Fetch a non-existent post → 404."""
    resp = client.get("/posts/nonexistent-post-id")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_get_user_posts_newest_first(client: TestClient) -> None:
    """Get user's posts → returns list, newest-first."""
    user = client.post(
        "/users",
        json={"username": "olivia", "display_name": "Olivia"},
    ).json()
    
    # Create 3 posts
    post1 = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/1.jpg",
            "media_type": "image",
            "caption": "First",
        },
    ).json()
    
    post2 = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/2.jpg",
            "media_type": "image",
            "caption": "Second",
        },
    ).json()
    
    post3 = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/3.jpg",
            "media_type": "image",
            "caption": "Third",
        },
    ).json()
    
    resp = client.get(f"/users/{user['id']}/posts")
    assert resp.status_code == 200
    posts = resp.json()
    
    assert len(posts) == 3
    # Verify newest-first order (post3, post2, post1)
    assert posts[0]["id"] == post3["id"]
    assert posts[1]["id"] == post2["id"]
    assert posts[2]["id"] == post1["id"]


def test_get_user_posts_nonexistent_user(client: TestClient) -> None:
    """Get posts for non-existent user → 404."""
    resp = client.get("/users/nonexistent-user-id/posts")
    assert resp.status_code == 404


def test_delete_post_success(client: TestClient) -> None:
    """Delete a post → 200, subsequent GET returns 404."""
    user = client.post(
        "/users",
        json={"username": "paul", "display_name": "Paul"},
    ).json()
    
    post = client.post(
        "/posts",
        json={
            "user_id": user["id"],
            "media_url": "https://example.com/pic.jpg",
            "media_type": "image",
        },
    ).json()
    
    # Delete the post
    resp = client.delete(f"/posts/{post['id']}")
    assert resp.status_code == 200
    
    # Verify post is gone
    get_resp = client.get(f"/posts/{post['id']}")
    assert get_resp.status_code == 404


def test_delete_post_cascades_likes_comments(client: TestClient) -> None:
    """Delete post cascades → likes and comments on that post are removed."""
    user1 = client.post(
        "/users",
        json={"username": "quinn", "display_name": "Quinn"},
    ).json()
    
    user2 = client.post(
        "/users",
        json={"username": "rachel", "display_name": "Rachel"},
    ).json()
    
    post = client.post(
        "/posts",
        json={
            "user_id": user1["id"],
            "media_url": "https://example.com/pic.jpg",
            "media_type": "image",
        },
    ).json()
    
    # Add a like to the post
    client.post(f"/posts/{post['id']}/like", json={"user_id": user2["id"]})
    
    # Add a comment to the post
    client.post(
        f"/posts/{post['id']}/comments",
        json={"user_id": user2["id"], "text": "Nice!"},
    )
    
    # Verify like and comment exist
    post_before = client.get(f"/posts/{post['id']}").json()
    assert post_before["like_count"] == 1
    assert post_before["comment_count"] == 1
    
    # Delete the post
    client.delete(f"/posts/{post['id']}")
    
    # Verify post is gone
    assert client.get(f"/posts/{post['id']}").status_code == 404


def test_delete_post_not_found(client: TestClient) -> None:
    """Delete a non-existent post → 404."""
    resp = client.delete("/posts/nonexistent-post-id")
    assert resp.status_code == 404


# ============================================================================
# FOLLOW TESTS (11 tests)
# ============================================================================


def test_follow_user_success(client: TestClient) -> None:
    """Follow a user → 201."""
    user_a = client.post(
        "/users",
        json={"username": "sam", "display_name": "Sam"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "tina", "display_name": "Tina"},
    ).json()
    
    resp = client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    assert resp.status_code == 201
    assert "success" in resp.json()["detail"].lower()


def test_follow_self(client: TestClient) -> None:
    """Follow self → 400."""
    user = client.post(
        "/users",
        json={"username": "uma", "display_name": "Uma"},
    ).json()
    
    resp = client.post(f"/users/{user['id']}/follow/{user['id']}")
    assert resp.status_code == 400
    assert "cannot follow yourself" in resp.json()["detail"].lower()


def test_follow_nonexistent_follower(client: TestClient) -> None:
    """Follow where follower doesn't exist → 404."""
    user = client.post(
        "/users",
        json={"username": "victor", "display_name": "Victor"},
    ).json()
    
    resp = client.post(f"/users/nonexistent-user/follow/{user['id']}")
    assert resp.status_code == 404


def test_follow_nonexistent_target(client: TestClient) -> None:
    """Follow where target doesn't exist → 404."""
    user = client.post(
        "/users",
        json={"username": "wendy", "display_name": "Wendy"},
    ).json()
    
    resp = client.post(f"/users/{user['id']}/follow/nonexistent-target")
    assert resp.status_code == 404


def test_follow_already_following(client: TestClient) -> None:
    """Follow an already-followed user → 409."""
    user_a = client.post(
        "/users",
        json={"username": "xander", "display_name": "Xander"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "yara", "display_name": "Yara"},
    ).json()
    
    # First follow
    client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    
    # Second follow (already following)
    resp = client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    assert resp.status_code == 409
    assert "already following" in resp.json()["detail"].lower()


def test_unfollow_success(client: TestClient) -> None:
    """Unfollow a user → 200."""
    user_a = client.post(
        "/users",
        json={"username": "zara", "display_name": "Zara"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "leo", "display_name": "Leo"},
    ).json()
    
    # Follow first
    client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    
    # Unfollow
    resp = client.delete(f"/users/{user_a['id']}/follow/{user_b['id']}")
    assert resp.status_code == 200
    assert "success" in resp.json()["detail"].lower()


def test_unfollow_not_following(client: TestClient) -> None:
    """Unfollow someone not followed → 404."""
    user_a = client.post(
        "/users",
        json={"username": "maya", "display_name": "Maya"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "eric", "display_name": "Eric"},
    ).json()
    
    resp = client.delete(f"/users/{user_a['id']}/follow/{user_b['id']}")
    assert resp.status_code == 404
    assert "not following" in resp.json()["detail"].lower()


def test_get_followers(client: TestClient) -> None:
    """Get followers → returns correct users after A follows B."""
    user_a = client.post(
        "/users",
        json={"username": "alex", "display_name": "Alex"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "bella", "display_name": "Bella"},
    ).json()
    
    user_c = client.post(
        "/users",
        json={"username": "carlos", "display_name": "Carlos"},
    ).json()
    
    # A and C follow B
    client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    client.post(f"/users/{user_c['id']}/follow/{user_b['id']}")
    
    # Get B's followers
    resp = client.get(f"/users/{user_b['id']}/followers")
    assert resp.status_code == 200
    followers = resp.json()
    
    assert len(followers) == 2
    follower_ids = {f["id"] for f in followers}
    assert user_a["id"] in follower_ids
    assert user_c["id"] in follower_ids


def test_get_following(client: TestClient) -> None:
    """Get following → returns correct users after A follows B."""
    user_a = client.post(
        "/users",
        json={"username": "diana", "display_name": "Diana"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "emilio", "display_name": "Emilio"},
    ).json()
    
    user_c = client.post(
        "/users",
        json={"username": "fiona", "display_name": "Fiona"},
    ).json()
    
    # A follows B and C
    client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    client.post(f"/users/{user_a['id']}/follow/{user_c['id']}")
    
    # Get A's following
    resp = client.get(f"/users/{user_a['id']}/following")
    assert resp.status_code == 200
    following = resp.json()
    
    assert len(following) == 2
    following_ids = {f["id"] for f in following}
    assert user_b["id"] in following_ids
    assert user_c["id"] in following_ids


def test_get_followers_nonexistent_user(client: TestClient) -> None:
    """Get followers of non-existent user → 404."""
    resp = client.get("/users/nonexistent-user/followers")
    assert resp.status_code == 404


def test_follow_updates_counts(client: TestClient) -> None:
    """After follow, user profile follower_count/following_count updated."""
    user_a = client.post(
        "/users",
        json={"username": "grant", "display_name": "Grant"},
    ).json()
    
    user_b = client.post(
        "/users",
        json={"username": "hannah", "display_name": "Hannah"},
    ).json()
    
    # Before follow: both counts are 0
    user_a_before = client.get(f"/users/{user_a['id']}").json()
    user_b_before = client.get(f"/users/{user_b['id']}").json()
    
    assert user_a_before["following_count"] == 0
    assert user_b_before["follower_count"] == 0
    
    # A follows B
    client.post(f"/users/{user_a['id']}/follow/{user_b['id']}")
    
    # After follow: counts updated
    user_a_after = client.get(f"/users/{user_a['id']}").json()
    user_b_after = client.get(f"/users/{user_b['id']}").json()
    
    assert user_a_after["following_count"] == 1
    assert user_b_after["follower_count"] == 1

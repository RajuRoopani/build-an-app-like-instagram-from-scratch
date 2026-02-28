"""
Targeted regression tests for bugs fixed during router review:

1. Route ordering: GET /explore/trending must NOT be matched by /explore/hashtag/{tag}
2. Hashtag normalization: tags extracted from caption must be lowercase
3. Hashtag lookup: /explore/hashtag/{tag} must be case-insensitive (normalizes to lowercase)
"""

from fastapi.testclient import TestClient


def _make_user(client: TestClient, username: str = "alice") -> dict:
    r = client.post("/users", json={"username": username, "display_name": username.title()})
    assert r.status_code == 201
    return r.json()


def _make_post(client: TestClient, user_id: str, caption: str) -> dict:
    r = client.post("/posts", json={
        "user_id": user_id,
        "media_url": "http://img.test/x.jpg",
        "media_type": "image",
        "caption": caption,
    })
    assert r.status_code == 201
    return r.json()


class TestRouteOrdering:
    """Verify /explore/trending is never hijacked by /explore/hashtag/{tag}."""

    def test_trending_returns_hashtag_counts_not_posts(self, client: TestClient) -> None:
        """
        GET /explore/trending must return List[HashtagCount] with 'tag' and 'count' keys.
        If route ordering is wrong, this endpoint is matched by /explore/hashtag/{tag}
        with tag="trending" and returns a List[PostOut] instead (empty list for tag='trending').
        """
        user = _make_user(client)
        _make_post(client, user["id"], "#python is great")
        _make_post(client, user["id"], "#python and #fastapi")

        r = client.get("/explore/trending")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) > 0, "Trending should return hashtag entries, not an empty list"
        # Must have 'tag' and 'count' — not PostOut fields like 'media_url', 'user_id'
        first = body[0]
        assert "tag" in first, "Expected HashtagCount with 'tag' field — route ordering bug?"
        assert "count" in first, "Expected HashtagCount with 'count' field — route ordering bug?"
        assert "media_url" not in first, "Got PostOut instead of HashtagCount — route ordering bug!"

    def test_hashtag_endpoint_still_works_after_ordering_fix(self, client: TestClient) -> None:
        """After reordering, /explore/hashtag/{tag} must still work correctly."""
        user = _make_user(client)
        post = _make_post(client, user["id"], "#sunset is beautiful")

        r = client.get("/explore/hashtag/sunset")
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert post["id"] in ids

    def test_trending_endpoint_separate_from_hashtag_endpoint(self, client: TestClient) -> None:
        """Ensure both /explore/trending and /explore/hashtag/trending work independently."""
        user = _make_user(client)
        # Post with 'trending' tag and 'python' tag
        post_with_trending = _make_post(client, user["id"], "#trending post")
        _make_post(client, user["id"], "#python post")

        # /explore/trending must return HashtagCount list (sorted by count)
        trending_r = client.get("/explore/trending")
        assert trending_r.status_code == 200
        assert "tag" in trending_r.json()[0]

        # /explore/hashtag/trending must return posts tagged #trending
        hashtag_r = client.get("/explore/hashtag/trending")
        assert hashtag_r.status_code == 200
        ids = [p["id"] for p in hashtag_r.json()]
        assert post_with_trending["id"] in ids


class TestHashtagNormalization:
    """Verify hashtags are stored and queried in lowercase."""

    def test_hashtags_stored_lowercase_in_post_response(self, client: TestClient) -> None:
        """PostOut.hashtags must always be lowercase regardless of caption casing."""
        user = _make_user(client)
        post = _make_post(client, user["id"], "#Python #FASTAPI #WebDev")
        assert set(post["hashtags"]) == {"python", "fastapi", "webdev"}, (
            f"Expected lowercase hashtags, got: {post['hashtags']}"
        )

    def test_hashtag_lookup_case_insensitive_uppercase_first(self, client: TestClient) -> None:
        """Searching for #Python (mixed case in URL) should find posts tagged #Python."""
        user = _make_user(client)
        post = _make_post(client, user["id"], "#Python rocks")

        # Lookup with uppercase P
        r = client.get("/explore/hashtag/Python")
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert post["id"] in ids, "Case-insensitive hashtag lookup failed for /explore/hashtag/Python"

    def test_hashtag_lookup_all_caps_in_url(self, client: TestClient) -> None:
        """Searching with ALL CAPS in URL should still match stored lowercase tag."""
        user = _make_user(client)
        post = _make_post(client, user["id"], "#RUST is fast")

        r = client.get("/explore/hashtag/RUST")
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert post["id"] in ids

    def test_trending_consolidates_mixed_case_captions(self, client: TestClient) -> None:
        """
        Posts tagged #Python, #PYTHON, #python in their captions all refer to the
        same normalized tag 'python' — trending should count them as one tag with count=3.
        """
        user = _make_user(client)
        _make_post(client, user["id"], "#Python post 1")
        _make_post(client, user["id"], "#PYTHON post 2")
        _make_post(client, user["id"], "#python post 3")

        r = client.get("/explore/trending")
        assert r.status_code == 200
        tag_dict = {item["tag"]: item["count"] for item in r.json()}

        # All three should merge into a single 'python' entry with count=3
        assert "python" in tag_dict, f"'python' not in trending tags: {tag_dict}"
        assert tag_dict["python"] == 3, f"Expected count=3, got {tag_dict['python']}"

        # No uppercase variants should exist as separate entries
        assert "Python" not in tag_dict, "Mixed-case 'Python' should not appear in trending"
        assert "PYTHON" not in tag_dict, "ALL CAPS 'PYTHON' should not appear in trending"

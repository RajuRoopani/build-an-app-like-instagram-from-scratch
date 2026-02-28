# Instagram Clone API

A full-featured Instagram-like REST API built with **FastAPI** and **Python**, featuring user management, posts with hashtags, follows, likes, comments, personalized feeds, and discovery endpoints. All data is stored in-memory for quick iteration and testing.

## Features

- **User Management**: Register users, update profiles, track follower/following counts
- **Posts**: Create photo/video posts with automatic hashtag extraction
- **Follows**: Follow/unfollow users with bidirectional relationship tracking
- **Likes**: Like and unlike posts, retrieve list of likers
- **Comments**: Add, retrieve, and delete comments on posts with timestamps
- **Feed**: Personalized feed showing posts from followed users, newest-first
- **Explore**: Discover recent posts, search by hashtags, and view trending hashtags
- **In-Memory Storage**: Fast, zeroed-overhead state management (perfect for prototyping and testing)
- **Type-Safe API**: Full Pydantic models with strict validation
- **Interactive API Docs**: Auto-generated Swagger UI at `/docs`

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) — modern, fast, async-ready web framework
- **Language**: Python 3.11+
- **Data Validation**: [Pydantic](https://docs.pydantic.dev/) — typed models with validation
- **Testing**: pytest with TestClient
- **Documentation**: OpenAPI/Swagger (auto-generated)

## Quick Start

### Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### Running the API

Start the server with hot-reload enabled (great for development):

```bash
uvicorn instagram_app.main:app --reload
```

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Running Tests

Run the complete test suite (47+ tests covering all endpoints):

```bash
cd instagram_app
python -m pytest tests/ -v
```

Or test a specific module:

```bash
python -m pytest tests/test_likes_comments_feed_explore.py -v
```

## Project Structure

```
instagram_app/
├── main.py                          # FastAPI app entry point
├── models.py                        # Pydantic request/response models
├── storage.py                       # In-memory data storage with reset() helper
├── routers/                         # Endpoint implementations
│   ├── __init__.py
│   ├── users.py                     # User registration, profiles
│   ├── posts.py                     # Post CRUD + hashtag extraction
│   ├── follows.py                   # Follow/unfollow relationships
│   ├── likes.py                     # Like/unlike posts
│   ├── comments.py                  # Comments on posts
│   ├── feed.py                      # Personalized feed
│   └── explore.py                   # Discovery: recent, hashtags, trending
├── tests/                           # Comprehensive test suite
│   ├── conftest.py                  # pytest fixtures (clean_storage, client)
│   ├── test_users_posts_follows.py  # 36 tests for users, posts, follows
│   └── test_likes_comments_feed_explore.py  # 27 tests for likes, comments, feed, explore
├── static/                          # Frontend (index.html, CSS, JS)
│   └── index.html
├── designs/                         # UX specifications
│   └── frontend-ux-spec.md
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## API Endpoints

All endpoints return JSON. Timestamps are ISO-8601 UTC format.

### Users (3 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **POST** | `/users` | Register a new user | 201 UserOut, 409 if username taken |
| **GET** | `/users/{user_id}` | Fetch user profile | 200 UserOut, 404 if not found |
| **PUT** | `/users/{user_id}` | Update user profile (bio, display_name, profile_pic_url) | 200 UserOut, 404 if not found |

### Posts (4 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **POST** | `/posts` | Create a new photo/video post (auto-extracts #hashtags) | 201 PostOut, 404 if user not found |
| **GET** | `/posts/{post_id}` | Fetch a single post | 200 PostOut, 404 if not found |
| **GET** | `/users/{user_id}/posts` | List all posts by a user (newest-first) | 200 List[PostOut], 404 if user not found |
| **DELETE** | `/posts/{post_id}` | Delete a post + all related likes & comments | 200, 404 if not found |

### Follows (4 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **POST** | `/users/{user_id}/follow/{target_id}` | Follow another user | 201, 400 self-follow, 404 user not found, 409 already following |
| **DELETE** | `/users/{user_id}/follow/{target_id}` | Unfollow a user | 200, 404 user/follow not found |
| **GET** | `/users/{user_id}/followers` | List followers of a user | 200 List[UserOut], 404 if user not found |
| **GET** | `/users/{user_id}/following` | List users that a user follows | 200 List[UserOut], 404 if user not found |

### Likes (3 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **POST** | `/posts/{post_id}/like` | Like a post | 201, 404 post/user not found, 409 already liked |
| **DELETE** | `/posts/{post_id}/like?user_id=...` | Unlike a post | 200, 404 post/like not found |
| **GET** | `/posts/{post_id}/likes` | List users who liked a post | 200 List[UserOut], 404 if post not found |

### Comments (3 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **POST** | `/posts/{post_id}/comments` | Add a comment to a post | 201 CommentOut, 404 post/user not found, 422 blank text |
| **GET** | `/posts/{post_id}/comments` | Get all comments on a post (oldest-first) | 200 List[CommentOut], 404 if post not found |
| **DELETE** | `/comments/{comment_id}` | Delete a comment | 200, 404 if not found |

### Feed (1 endpoint)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **GET** | `/feed/{user_id}` | Get personalized feed (posts from followed users, newest-first) | 200 List[PostOut], 404 if user not found |

### Explore (3 endpoints)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| **GET** | `/explore?limit=20` | Get recent posts from all users (default limit 20, max 100) | 200 List[PostOut] |
| **GET** | `/explore/hashtag/{tag}` | Get posts tagged with a hashtag (case-sensitive, newest-first) | 200 List[PostOut] |
| **GET** | `/explore/trending` | Get top 10 hashtags ranked by post count | 200 List[HashtagCount] |

## Data Models

### UserOut (Response)

Returned by all user endpoints and included in follower/following lists.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "display_name": "John Doe",
  "bio": "Photography enthusiast",
  "profile_pic_url": "https://example.com/pic.jpg",
  "created_at": "2024-01-15T10:30:00",
  "follower_count": 42,
  "following_count": 15,
  "post_count": 8
}
```

### PostOut (Response)

Returned by post endpoints; includes computed like and comment counts.

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "media_url": "https://cdn.example.com/photo.jpg",
  "media_type": "image",
  "caption": "Beautiful sunset #photography #travel",
  "hashtags": ["photography", "travel"],
  "created_at": "2024-01-15T14:22:00",
  "like_count": 5,
  "comment_count": 2
}
```

### CommentOut (Response)

Returned by comment endpoints.

```json
{
  "id": "a1234567-89ab-cdef-0123-456789abcdef",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "post_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "text": "Stunning view! Where was this taken?",
  "created_at": "2024-01-15T15:05:00"
}
```

### HashtagCount (Response)

Returned by the `/explore/trending` endpoint.

```json
{
  "tag": "photography",
  "count": 42
}
```

## Example Workflows

### 1. Register and Create a Post

```bash
# Register a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "display_name": "Alice Wonder",
    "bio": "Designer & photographer"
  }'

# Response (save the user_id):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "username": "alice",
#   ...
# }

# Create a post
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "media_url": "https://cdn.example.com/photo.jpg",
    "media_type": "image",
    "caption": "Morning coffee #morningroutine #photography"
  }'
```

### 2. Follow a User and View Feed

```bash
# Follow another user
curl -X POST http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000/follow/user-b-id

# View your personalized feed
curl http://localhost:8000/feed/550e8400-e29b-41d4-a716-446655440000
```

### 3. Like a Post and Add a Comment

```bash
# Like a post
curl -X POST http://localhost:8000/posts/post-id/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Add a comment
curl -X POST http://localhost:8000/posts/post-id/comments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Love this shot!"
  }'

# View all comments on the post
curl http://localhost:8000/posts/post-id/comments
```

### 4. Explore Hashtags and Trending

```bash
# Discover recent posts
curl http://localhost:8000/explore?limit=10

# Find posts tagged with #photography
curl http://localhost:8000/explore/hashtag/photography

# See trending hashtags
curl http://localhost:8000/explore/trending
```

## Test Coverage

The test suite includes **47+ tests** covering:

- ✅ **Users** (13 tests): registration, profiles, uniqueness, updates
- ✅ **Posts** (12 tests): creation, retrieval, deletion, hashtag extraction
- ✅ **Follows** (12 tests): follow/unfollow, follower/following lists, bidirectional consistency
- ✅ **Likes** (8 tests): like, unlike, conflicts, likers list, like_count
- ✅ **Comments** (9 tests): add, delete, ordering, blank validation, comment_count
- ✅ **Feed** (5 tests): empty feed, filtered by follows, self-exclusion, updates
- ✅ **Explore** (5 tests): recent, pagination, hashtag search, trending

All tests are **independent** (no order dependencies) and use pytest fixtures for clean state between runs.

### Run All Tests

```bash
cd instagram_app
python -m pytest tests/ -v
```

Expected output: **47 passed** ✓

## Error Handling

All endpoints follow REST conventions:

- **201 Created**: Resource successfully created
- **200 OK**: Request successful
- **400 Bad Request**: Invalid input (e.g., self-follow)
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Business logic conflict (duplicate follow, already liked)
- **422 Unprocessable Entity**: Validation error (blank comment, invalid field type)

Error responses include a `detail` field:

```json
{
  "detail": "User not found"
}
```

## Storage Architecture

The API uses **in-memory dictionaries and sets** for instant iteration and testing. All data is stored in `instagram_app/storage.py`:

- `users`: UUID → user dict
- `posts`: UUID → post dict (includes hashtags list)
- `follows`: user_id → set of followed user_ids
- `followers`: user_id → set of follower user_ids (reverse index)
- `likes`: post_id → set of user_ids who liked
- `comments`: UUID → comment dict
- `post_comments`: post_id → ordered list of comment_ids (oldest first)
- `hashtag_posts`: tag → set of post_ids (for fast hashtag lookup)

**Reset Function**: Call `reset_storage()` between test runs to wipe all state (used by pytest fixtures).

## Development Notes

### Adding New Endpoints

1. Create a function in the appropriate router (e.g., `routers/posts.py`)
2. Use FastAPI decorators: `@router.post()`, `@router.get()`, etc.
3. Use Pydantic models for request/response types
4. Import and include the router in `main.py`
5. Write tests in `tests/test_*.py` following the existing patterns

### Testing Best Practices

- Use the `client` fixture (TestClient) for all HTTP calls
- Use helper functions like `_create_user()` and `_create_post()` to reduce boilerplate
- The `clean_storage` fixture automatically resets state before/after each test
- Test both success and error paths (404, 409, 422)
- Verify response status codes and JSON structure

## Future Enhancements

Potential features for production:

- **Persistent Storage**: Replace in-memory dicts with PostgreSQL/MongoDB
- **Authentication**: JWT tokens, API keys, OAuth2
- **Rate Limiting**: Prevent spam and abuse
- **Search**: Full-text search on captions and hashtags
- **Direct Messages**: Private messaging between users
- **Notifications**: Like/comment/follow notifications
- **Media Upload**: Server-side image/video storage with S3
- **Pagination**: Cursor-based pagination for large result sets
- **WebSockets**: Real-time feed updates

## License

MIT

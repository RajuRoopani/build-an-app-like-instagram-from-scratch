"""
Shared pytest fixtures for the Instagram Clone API test suite.

- clean_storage  (autouse, function-scoped): wipes all in-memory state
                 before AND after every test so tests are fully isolated.
- client         (function-scoped): a fresh FastAPI TestClient per test.
"""

import pytest
from fastapi.testclient import TestClient

from instagram_app.main import app
from instagram_app.storage import reset_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset all storage collections before and after each test."""
    reset_storage()
    yield
    reset_storage()


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient bound to the FastAPI app."""
    return TestClient(app)

"""Shared test fixtures for the inference service."""

from __future__ import annotations

import pytest

from app.auth import DEV_OPERATOR, Operator


@pytest.fixture()
def dev_operator() -> Operator:
    """Return the default dev operator for tests."""
    return DEV_OPERATOR


# Re-export for direct import in tests that use asyncio.run() pattern
TEST_OPERATOR = DEV_OPERATOR

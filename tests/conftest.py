"""
Pytest configuration and fixtures.
"""
import pytest
import os


@pytest.fixture(scope="session")
def test_database_url():
    """Provide test database URL."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/inquiry_automation_test"
    )


@pytest.fixture
def sample_inquiry_text():
    """Provide sample inquiry text for testing."""
    return {
        "technical": "I cannot login to my account. Getting error 500.",
        "billing": "I was charged twice this month. Need a refund.",
        "sales": "Interested in enterprise plan for 50 users.",
        "urgent": "URGENT! System is down! Need help ASAP!",
        "positive": "Your product is amazing! Love it!",
        "negative": "This is terrible. Very disappointed.",
    }


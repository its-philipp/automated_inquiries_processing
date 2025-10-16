"""
Unit tests for the inquiry classifier.
"""
import pytest
from src.models.classifier import InquiryClassifier


@pytest.fixture
def classifier():
    """Create classifier instance."""
    return InquiryClassifier()


def test_classifier_initialization(classifier):
    """Test classifier initializes correctly."""
    assert classifier is not None
    assert classifier.use_zero_shot is True


def test_technical_support_classification(classifier):
    """Test classification of technical support inquiry."""
    text = "I cannot login to my account. Getting authentication error."
    
    category, confidence, _ = classifier.predict(text)
    
    assert category in ["technical_support", "technical support and IT issues"]
    assert 0.0 <= confidence <= 1.0


def test_billing_classification(classifier):
    """Test classification of billing inquiry."""
    text = "I was charged twice for my subscription. Need a refund."
    
    category, confidence, _ = classifier.predict(text)
    
    assert category in ["billing", "billing and payments"]
    assert confidence > 0.3


def test_sales_classification(classifier):
    """Test classification of sales inquiry."""
    text = "I'm interested in the enterprise plan for 100 users. Can you send pricing?"
    
    category, confidence, _ = classifier.predict(text)
    
    assert category in ["sales", "sales and product inquiries"]
    assert confidence > 0.3


def test_prediction_with_all_scores(classifier):
    """Test prediction returns all scores when requested."""
    text = "How do I reset my password?"
    
    category, confidence, all_scores = classifier.predict(text, return_all_scores=True)
    
    assert all_scores is not None
    assert isinstance(all_scores, dict)
    assert len(all_scores) > 0


def test_model_info(classifier):
    """Test model info retrieval."""
    info = classifier.get_model_info()
    
    assert "model_type" in info
    assert "model_name" in info
    assert "device" in info


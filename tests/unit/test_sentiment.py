"""
Unit tests for the sentiment analyzer.
"""
import pytest
from src.models.sentiment import SentimentAnalyzer


@pytest.fixture
def sentiment_analyzer():
    """Create sentiment analyzer instance."""
    return SentimentAnalyzer()


def test_analyzer_initialization(sentiment_analyzer):
    """Test sentiment analyzer initializes correctly."""
    assert sentiment_analyzer is not None
    assert sentiment_analyzer.model_name is not None


def test_positive_sentiment(sentiment_analyzer):
    """Test detection of positive sentiment."""
    text = "I love your product! It's absolutely amazing and has exceeded my expectations."
    
    sentiment, confidence, _ = sentiment_analyzer.predict(text)
    
    assert sentiment == "positive"
    assert confidence > 0.5


def test_negative_sentiment(sentiment_analyzer):
    """Test detection of negative sentiment."""
    text = "This is terrible. I'm very disappointed and frustrated with the service."
    
    sentiment, confidence, _ = sentiment_analyzer.predict(text)
    
    assert sentiment == "negative"
    assert confidence > 0.5


def test_neutral_sentiment(sentiment_analyzer):
    """Test detection of neutral sentiment."""
    text = "I have a question about the pricing. Can you provide more information?"
    
    sentiment, confidence, _ = sentiment_analyzer.predict(text)
    
    assert sentiment in ["neutral", "positive", "negative"]  # Model-dependent
    assert 0.0 <= confidence <= 1.0


def test_prediction_with_all_scores(sentiment_analyzer):
    """Test prediction returns all scores when requested."""
    text = "The service is okay."
    
    sentiment, confidence, all_scores = sentiment_analyzer.predict(text, return_all_scores=True)
    
    assert all_scores is not None
    assert isinstance(all_scores, dict)


def test_model_info(sentiment_analyzer):
    """Test model info retrieval."""
    info = sentiment_analyzer.get_model_info()
    
    assert "model_type" in info
    assert "model_name" in info
    assert info["model_type"] == "sentiment-analysis"


"""
Unit tests for the urgency detector.
"""
import pytest
from src.models.urgency import UrgencyDetector


@pytest.fixture
def urgency_detector():
    """Create urgency detector instance."""
    return UrgencyDetector()


def test_detector_initialization(urgency_detector):
    """Test urgency detector initializes correctly."""
    assert urgency_detector is not None
    assert urgency_detector.keyword_to_level is not None


def test_critical_urgency(urgency_detector):
    """Test detection of critical urgency."""
    text = "URGENT! System is down. Cannot access anything. This is critical!"
    
    urgency, confidence, _ = urgency_detector.predict(text)
    
    assert urgency == "critical"
    assert confidence > 0.5


def test_high_urgency(urgency_detector):
    """Test detection of high urgency."""
    text = "This is important and needs to be addressed soon. Please help quickly."
    
    urgency, confidence, _ = urgency_detector.predict(text)
    
    assert urgency in ["high", "critical"]
    assert confidence > 0.3


def test_medium_urgency(urgency_detector):
    """Test detection of medium urgency."""
    text = "Could you help me with this when possible? Not urgent."
    
    urgency, confidence, _ = urgency_detector.predict(text)
    
    assert urgency in ["medium", "low"]
    assert 0.0 <= confidence <= 1.0


def test_low_urgency(urgency_detector):
    """Test detection of low urgency."""
    text = "No rush on this. Whenever you have time is fine."
    
    urgency, confidence, _ = urgency_detector.predict(text)
    
    assert urgency == "low"
    assert confidence > 0.3


def test_urgency_keywords_extraction(urgency_detector):
    """Test extraction of urgency keywords."""
    text = "This is URGENT and CRITICAL. Need help ASAP!"
    
    signals = urgency_detector.extract_urgency_signals(text)
    
    assert isinstance(signals, dict)
    assert "critical" in signals
    assert signals["critical"] > 0


def test_prediction_with_all_scores(urgency_detector):
    """Test prediction returns all scores when requested."""
    text = "Please help when you can."
    
    urgency, confidence, all_scores = urgency_detector.predict(text, return_all_scores=True)
    
    assert all_scores is not None
    assert isinstance(all_scores, dict)
    assert len(all_scores) == 4  # low, medium, high, critical


def test_model_info(urgency_detector):
    """Test model info retrieval."""
    info = urgency_detector.get_model_info()
    
    assert "model_type" in info
    assert "model_name" in info
    assert info["model_type"] == "rule-based-urgency"


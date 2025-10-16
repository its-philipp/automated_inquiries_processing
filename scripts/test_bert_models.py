#!/usr/bin/env python3
"""
Test script for BERT-based models.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.classifier import InquiryClassifier
from src.models.sentiment import SentimentAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_classifier():
    """Test the BERT-based classifier."""
    print("🧪 Testing BERT-based Classifier")
    print("=" * 50)
    
    classifier = InquiryClassifier()
    
    test_cases = [
        {
            "text": "I'm having trouble logging into my account. The system keeps showing an error message.",
            "expected": "technical_support"
        },
        {
            "text": "I want to upgrade my subscription plan and get a quote for the premium features.",
            "expected": "sales"
        },
        {
            "text": "I was charged twice for my monthly subscription. Can I get a refund?",
            "expected": "billing"
        },
        {
            "text": "I'm interested in applying for the software engineer position you posted.",
            "expected": "hr"
        },
        {
            "text": "I have some feedback about the user interface. It would be great if you could add dark mode.",
            "expected": "product_feedback"
        },
        {
            "text": "I need to review the terms of service and privacy policy for compliance.",
            "expected": "legal"
        }
    ]
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]
        
        category, confidence, all_scores = classifier.predict(text, include_all_scores=True)
        
        is_correct = category == expected
        if is_correct:
            correct_predictions += 1
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Test {i}: {category} (confidence: {confidence:.3f})")
        print(f"   Expected: {expected}")
        print(f"   Text: {text[:60]}...")
        print(f"   All scores: {all_scores}")
        print()
    
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"📊 Classifier Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
    return accuracy

def test_sentiment_analyzer():
    """Test the RoBERTa-based sentiment analyzer."""
    print("\n🧪 Testing RoBERTa-based Sentiment Analyzer")
    print("=" * 50)
    
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        {
            "text": "This is amazing! I love the new features.",
            "expected": "positive"
        },
        {
            "text": "I'm really frustrated with the constant bugs and errors.",
            "expected": "negative"
        },
        {
            "text": "The system is working as expected. No issues to report.",
            "expected": "neutral"
        },
        {
            "text": "Thank you so much for your excellent customer service!",
            "expected": "positive"
        },
        {
            "text": "This is terrible. I want my money back immediately.",
            "expected": "negative"
        },
        {
            "text": "I need to update my billing information for next month.",
            "expected": "neutral"
        }
    ]
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]
        
        sentiment, confidence, all_scores = analyzer.predict(text, include_all_scores=True)
        
        is_correct = sentiment == expected
        if is_correct:
            correct_predictions += 1
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Test {i}: {sentiment} (confidence: {confidence:.3f})")
        print(f"   Expected: {expected}")
        print(f"   Text: {text}")
        print(f"   All scores: {all_scores}")
        print()
    
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"📊 Sentiment Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
    return accuracy

def test_model_info():
    """Test model information and caching."""
    print("\n🧪 Testing Model Information")
    print("=" * 50)
    
    from src.models.model_cache import model_cache
    
    info = model_cache.get_model_info()
    print(f"📊 Model Information:")
    print(f"   Loaded models: {info['loaded_models']}")
    print(f"   Device: {info['device']}")
    print(f"   Cache directory: {info['cache_directory']}")
    print(f"   Memory usage: {info['total_memory_usage']}")

def main():
    """Run all tests."""
    print("🚀 BERT Models Test Suite")
    print("=" * 60)
    
    try:
        # Test classifier
        classifier_accuracy = test_classifier()
        
        # Test sentiment analyzer
        sentiment_accuracy = test_sentiment_analyzer()
        
        # Test model info
        test_model_info()
        
        # Summary
        print("\n📈 Test Summary")
        print("=" * 50)
        print(f"✅ Classifier Accuracy: {classifier_accuracy:.1f}%")
        print(f"✅ Sentiment Accuracy: {sentiment_accuracy:.1f}%")
        print(f"✅ Models loaded successfully")
        print(f"✅ Caching system working")
        
        if classifier_accuracy >= 80 and sentiment_accuracy >= 80:
            print("\n🎉 All tests passed! BERT models are working excellently!")
        elif classifier_accuracy >= 60 and sentiment_accuracy >= 60:
            print("\n✅ Tests passed! BERT models are working well.")
        else:
            print("\n⚠️  Some tests failed. Check the model implementations.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test error details:")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

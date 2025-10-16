"""
Text preprocessing utilities for cleaning and preparing inquiry text for NLP models.
"""
import re
from typing import Tuple
from bs4 import BeautifulSoup


class TextProcessor:
    """Process and clean text from email/ticket inquiries."""
    
    def __init__(self, max_length: int = 5000):
        """
        Initialize text processor.
        
        Args:
            max_length: Maximum allowed text length
        """
        self.max_length = max_length
        
        # Common email signature patterns
        self.signature_patterns = [
            r'\n\s*Best regards,.*',
            r'\n\s*Sincerely,.*',
            r'\n\s*Thanks,.*',
            r'\n\s*Thank you,.*',
            r'\n\s*Regards,.*',
            r'\n\s*Kind regards,.*',
            r'\n\s*Sent from my.*',
            r'\n\s*Get Outlook for.*',
            r'\n\s*---+.*',  # Signature separator
        ]
        
    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()
    
    def remove_email_signature(self, text: str) -> str:
        """Remove common email signatures."""
        for pattern in self.signature_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        return text
    
    def remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.sub(url_pattern, ' ', text)
    
    def remove_email_addresses(self, text: str) -> str:
        """Remove email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, ' ', text)
    
    def remove_phone_numbers(self, text: str) -> str:
        """Remove phone numbers from text."""
        phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        return re.sub(phone_pattern, ' ', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace to single spaces."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def remove_special_characters(self, text: str, keep_punctuation: bool = True) -> str:
        """
        Remove special characters.
        
        Args:
            text: Input text
            keep_punctuation: If True, keep basic punctuation marks
        """
        if keep_punctuation:
            # Keep letters, numbers, and basic punctuation
            text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\'-]', ' ', text)
        else:
            # Keep only letters, numbers, and spaces
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        return text
    
    def clean_text(
        self,
        text: str,
        remove_html: bool = True,
        remove_signatures: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = False,
        remove_phones: bool = False,
        lowercase: bool = False,
        remove_special_chars: bool = False,
    ) -> str:
        """
        Apply full cleaning pipeline to text.
        
        Args:
            text: Input text
            remove_html: Remove HTML tags
            remove_signatures: Remove email signatures
            remove_urls: Remove URLs
            remove_emails: Remove email addresses
            remove_phones: Remove phone numbers
            lowercase: Convert to lowercase
            remove_special_chars: Remove special characters
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length]
        
        # Apply cleaning steps
        if remove_html:
            text = self.remove_html_tags(text)
        
        if remove_signatures:
            text = self.remove_email_signature(text)
        
        if remove_urls:
            text = self.remove_urls(text)
        
        if remove_emails:
            text = self.remove_email_addresses(text)
        
        if remove_phones:
            text = self.remove_phone_numbers(text)
        
        if remove_special_chars:
            text = self.remove_special_characters(text, keep_punctuation=True)
        
        # Normalize whitespace
        text = self.normalize_whitespace(text)
        
        if lowercase:
            text = text.lower()
        
        return text
    
    def process_inquiry(self, subject: str, body: str) -> Tuple[str, str, str]:
        """
        Process both subject and body of an inquiry.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Tuple of (cleaned_subject, cleaned_body, combined_text)
        """
        # Clean subject (more aggressive cleaning)
        cleaned_subject = self.clean_text(
            subject,
            remove_html=True,
            remove_urls=True,
            remove_special_chars=False,
            lowercase=False,
        )
        
        # Clean body (preserve more context)
        cleaned_body = self.clean_text(
            body,
            remove_html=True,
            remove_signatures=True,
            remove_urls=True,
            remove_emails=False,
            remove_phones=False,
            remove_special_chars=False,
            lowercase=False,
        )
        
        # Combine for model input (subject gets more weight)
        combined_text = f"{cleaned_subject}. {cleaned_body}"
        
        return cleaned_subject, cleaned_body, combined_text
    
    def extract_urgency_keywords(self, text: str) -> dict:
        """
        Extract urgency-related keywords from text.
        
        Returns:
            Dictionary with urgency indicators
        """
        text_lower = text.lower()
        
        urgency_keywords = {
            'critical': ['urgent', 'critical', 'asap', 'emergency', 'immediately', 
                        'right away', 'can\'t work', 'blocking', 'stopped'],
            'high': ['important', 'soon', 'quickly', 'priority', 'as soon as possible',
                    'need help', 'please help'],
            'medium': ['when possible', 'at your convenience', 'in the next few days'],
            'low': ['no rush', 'whenever', 'low priority', 'not urgent'],
        }
        
        found_keywords = {}
        for level, keywords in urgency_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                found_keywords[level] = matches
        
        return found_keywords


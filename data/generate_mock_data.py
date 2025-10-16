"""
Generate realistic mock email/ticket data for testing the inquiry automation pipeline.
"""
import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from faker import Faker

fake = Faker()


# Category templates with realistic subjects and body patterns
INQUIRY_TEMPLATES = {
    "technical_support": {
        "subjects": [
            "Login issues with my account",
            "Application keeps crashing",
            "Cannot access dashboard",
            "Error message when uploading files",
            "API integration not working",
            "Database connection timeout",
            "SSL certificate error",
            "Mobile app sync problems",
        ],
        "body_patterns": [
            "I'm experiencing {} when trying to {}. This started happening {}. Could you please help?",
            "Hi, I need urgent assistance with {}. The error message says: {}. This is blocking my work.",
            "Hello support team, {} is not working properly. I've tried {} but the issue persists.",
            "I'm unable to {} due to {}. Can someone look into this ASAP?",
        ],
        "issues": ["authentication errors", "timeout issues", "crashes", "connection problems", "data sync issues"],
        "actions": ["log in", "save my work", "access the system", "upload files", "export data"],
        "timeframes": ["this morning", "yesterday", "a few hours ago", "after the latest update"],
    },
    "billing": {
        "subjects": [
            "Question about recent invoice",
            "Incorrect charge on my account",
            "Request for payment extension",
            "Need a refund for duplicate charge",
            "Update payment method",
            "Upgrade/downgrade subscription",
            "Billing address correction",
            "Tax documentation request",
        ],
        "body_patterns": [
            "I noticed {} on invoice #{}. Could you please {}?",
            "There's a charge of ${} on my account that I don't recognize. {}",
            "I would like to {} my subscription. Can you help me with {}?",
            "Please provide {} for {} period. I need this for {}.",
        ],
        "issues": ["an incorrect amount", "a duplicate charge", "an unexpected fee", "a billing error"],
        "amounts": ["99.99", "299.99", "49.50", "199.00", "500.00"],
    },
    "sales": {
        "subjects": [
            "Interested in enterprise plan",
            "Request for product demonstration",
            "Pricing for team of 50",
            "Partnership opportunity",
            "Volume discount inquiry",
            "Trial extension request",
            "Feature comparison question",
            "Custom solution needed",
        ],
        "body_patterns": [
            "Hi, I'm interested in {} for my company. We have {} employees. {}",
            "Could you provide more information about {}? Specifically, I'd like to know {}.",
            "We're currently evaluating {} and would like to {}. When can we schedule {}?",
            "Our company needs {} with {}. Can you provide a custom quote?",
        ],
        "company_sizes": ["15", "50", "200", "500", "1000"],
        "interests": ["your enterprise plan", "premium features", "API access", "custom integrations"],
    },
    "hr": {
        "subjects": [
            "PTO request for next month",
            "Question about benefits enrollment",
            "W-2 form request",
            "Update emergency contact information",
            "Parental leave inquiry",
            "Health insurance question",
            "401k contribution change",
            "Remote work policy clarification",
        ],
        "body_patterns": [
            "I would like to request {} from {} to {}. {}",
            "Could you please clarify the policy regarding {}? I need this information for {}.",
            "I need to update my {} information. {}",
            "I have a question about {} eligibility. {}",
        ],
    },
    "legal": {
        "subjects": [
            "GDPR data deletion request",
            "Terms of service clarification",
            "Copyright infringement claim",
            "Data processing agreement needed",
            "Privacy policy question",
            "License agreement review",
            "Export compliance inquiry",
            "Right to access personal data",
        ],
        "body_patterns": [
            "Under {}, I am requesting {} for {}.",
            "We need clarification on {} in your {}. This is required for {}.",
            "Please provide {} regarding {}. Our legal team requires this for {}.",
            "I am exercising my right to {} under {}. Please process this request {}.",
        ],
        "regulations": ["GDPR", "CCPA", "HIPAA", "SOC 2 compliance"],
    },
    "product_feedback": {
        "subjects": [
            "Suggestion for new feature",
            "Love the recent update!",
            "Issue with user interface",
            "Feature request: bulk export",
            "Dark mode please!",
            "Integration with Slack needed",
            "Dashboard is confusing",
            "Great product, minor bug found",
        ],
        "body_patterns": [
            "I've been using your product for {} and {}. One suggestion: {}",
            "The recent {} update is {}! However, I think {} could be improved.",
            "Would it be possible to add {}? This would really help with {}.",
            "I love {} feature, but {} could use some work. {}",
        ],
        "durations": ["6 months", "a year", "2 years", "several weeks"],
        "sentiments": ["I love it", "it's great", "it's been very helpful", "I'm impressed"],
    },
}

# Urgency keywords and sentiment modifiers
URGENCY_MODIFIERS = {
    "critical": ["URGENT", "CRITICAL", "ASAP", "immediately", "emergency", "can't work"],
    "high": ["soon", "important", "as soon as possible", "priority", "quickly"],
    "medium": ["when possible", "at your convenience", "in the next few days"],
    "low": ["no rush", "whenever you have time", "low priority"],
}

SENTIMENT_MODIFIERS = {
    "positive": ["Thank you", "Great", "Excellent", "Appreciate", "Love", "Perfect"],
    "neutral": ["Please", "Could you", "I need", "Requesting"],
    "negative": ["frustrated", "disappointed", "unacceptable", "terrible", "worst", "angry"],
}


def generate_inquiry(category: str, urgency: str = None, sentiment: str = None) -> Dict[str, Any]:
    """Generate a single mock inquiry."""
    if urgency is None:
        urgency = random.choices(
            ["low", "medium", "high", "critical"],
            weights=[30, 50, 15, 5],
            k=1
        )[0]
    
    if sentiment is None:
        sentiment = random.choices(
            ["positive", "neutral", "negative"],
            weights=[30, 50, 20],
            k=1
        )[0]
    
    template = INQUIRY_TEMPLATES[category]
    subject = random.choice(template["subjects"])
    
    # Add urgency modifier to subject sometimes
    if urgency in ["critical", "high"] and random.random() > 0.5:
        modifier = random.choice(URGENCY_MODIFIERS[urgency])
        subject = f"{modifier}: {subject}"
    
    # Generate body
    if "body_patterns" in template:
        pattern = random.choice(template["body_patterns"])
        
        # Fill in pattern with appropriate data
        if category == "technical_support":
            body = pattern.format(
                random.choice(template["issues"]),
                random.choice(template["actions"]),
                random.choice(template["timeframes"]),
                f'"{fake.sentence()}"'
            )
        elif category == "billing":
            body = pattern.format(
                random.choice(template["issues"]),
                fake.random_int(min=10000, max=99999),
                "investigate this",
                random.choice(template["amounts"])
            )
        elif category == "sales":
            body = pattern.format(
                random.choice(template["interests"]),
                random.choice(template["company_sizes"]),
                "We are currently evaluating solutions",
                "a demo call"
            )
        else:
            # For patterns that don't have specific fillers, use generic content
            if pattern.count('{}') == 1:
                body = pattern.format(fake.sentence())
            elif pattern.count('{}') == 2:
                body = pattern.format(fake.sentence(), fake.sentence())
            elif pattern.count('{}') == 3:
                body = pattern.format(fake.sentence(), fake.sentence(), fake.sentence())
            else:
                body = fake.paragraph(nb_sentences=3)
    else:
        body = fake.paragraph(nb_sentences=3)
    
    # Add sentiment modifier
    sentiment_word = random.choice(SENTIMENT_MODIFIERS[sentiment])
    if sentiment == "negative":
        body = f"I am {sentiment_word} that {body}"
    elif sentiment == "positive":
        body = f"{sentiment_word}! {body}"
    else:
        body = f"{sentiment_word}, {body}"
    
    # Add urgency context in body
    if urgency == "critical":
        body += f" This is blocking our entire team from working. {random.choice(URGENCY_MODIFIERS['critical'])}"
    elif urgency == "high":
        body += f" Please respond {random.choice(URGENCY_MODIFIERS['high'])}."
    
    # Add signature
    body += f"\n\nBest regards,\n{fake.name()}\n{fake.company()}"
    
    # Generate timestamp (within last 30 days)
    timestamp = datetime.now() - timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    return {
        "subject": subject,
        "body": body,
        "sender_email": fake.email(),
        "sender_name": fake.name(),
        "timestamp": timestamp.isoformat(),
        "metadata": {
            "category": category,  # Ground truth for evaluation
            "urgency": urgency,    # Ground truth for evaluation
            "sentiment": sentiment, # Ground truth for evaluation
            "source": "mock_generator",
        }
    }


def generate_dataset(
    num_samples: int = 1000,
    category_distribution: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """Generate a balanced dataset of mock inquiries."""
    if category_distribution is None:
        # Default balanced distribution
        category_distribution = {
            "technical_support": 0.30,
            "billing": 0.20,
            "sales": 0.15,
            "hr": 0.10,
            "legal": 0.10,
            "product_feedback": 0.15,
        }
    
    dataset = []
    
    for category, proportion in category_distribution.items():
        count = int(num_samples * proportion)
        for _ in range(count):
            dataset.append(generate_inquiry(category))
    
    # Shuffle the dataset
    random.shuffle(dataset)
    
    return dataset


def save_dataset(dataset: List[Dict[str, Any]], output_dir: str = "data/raw"):
    """Save dataset to JSON and CSV formats."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_path = output_path / "sample_inquiries.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(dataset)} inquiries to {json_path}")
    
    # Save as CSV
    csv_path = output_path / "sample_inquiries.csv"
    if dataset:
        # Get all fieldnames including flattened metadata
        sample_row = dataset[0]
        fieldnames = list(sample_row.keys())
        if 'metadata' in fieldnames:
            fieldnames.remove('metadata')
            # Add flattened metadata fields
            for key in sample_row['metadata'].keys():
                fieldnames.append(f'metadata_{key}')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in dataset:
                # Flatten metadata for CSV
                flattened = row.copy()
                if 'metadata' in flattened:
                    metadata = flattened.pop('metadata')
                    for key, value in metadata.items():
                        flattened[f'metadata_{key}'] = value
                writer.writerow(flattened)
        print(f"✓ Saved {len(dataset)} inquiries to {csv_path}")


def main():
    """Generate and save mock inquiry dataset."""
    print("Generating mock inquiry dataset...")
    
    # Generate 1000 sample inquiries
    dataset = generate_dataset(num_samples=1000)
    
    # Print statistics
    categories = {}
    urgencies = {}
    sentiments = {}
    
    for inquiry in dataset:
        cat = inquiry['metadata']['category']
        urg = inquiry['metadata']['urgency']
        sent = inquiry['metadata']['sentiment']
        
        categories[cat] = categories.get(cat, 0) + 1
        urgencies[urg] = urgencies.get(urg, 0) + 1
        sentiments[sent] = sentiments.get(sent, 0) + 1
    
    print(f"\nDataset Statistics:")
    print(f"Total inquiries: {len(dataset)}")
    print(f"\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} ({count/len(dataset)*100:.1f}%)")
    print(f"\nUrgency distribution:")
    for urg, count in sorted(urgencies.items()):
        print(f"  {urg}: {count} ({count/len(dataset)*100:.1f}%)")
    print(f"\nSentiment distribution:")
    for sent, count in sorted(sentiments.items()):
        print(f"  {sent}: {count} ({count/len(dataset)*100:.1f}%)")
    
    # Save dataset
    save_dataset(dataset)
    
    print("\n✓ Mock data generation complete!")


if __name__ == "__main__":
    main()


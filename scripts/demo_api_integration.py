#!/usr/bin/env python3
"""
Demo script showing how to integrate DAG with API for Prometheus metrics.
This is an example of how the DAG could be modified to use the API.
"""

import requests
import json
from datetime import datetime

def send_inquiries_to_api(inquiries):
    """Send inquiries to API instead of direct database insertion."""
    api_url = "http://api:8000/api/v1/inquiries"
    
    success_count = 0
    error_count = 0
    
    for inquiry in inquiries:
        try:
            # Prepare inquiry data for API
            api_data = {
                "subject": inquiry["subject"],
                "body": inquiry["body"],
                "sender_email": inquiry["sender_email"],
                "sender_name": inquiry.get("sender_name"),
                "metadata": inquiry.get("metadata", {})
            }
            
            # Send to API
            response = requests.post(api_url, json=api_data, timeout=10)
            
            if response.status_code == 201:
                success_count += 1
                print(f"✅ Inquiry sent successfully: {inquiry['subject'][:50]}...")
            else:
                error_count += 1
                print(f"❌ API error {response.status_code}: {response.text}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Request failed: {e}")
    
    print(f"\n📊 API Integration Results:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {error_count}")
    print(f"  📈 Success Rate: {(success_count/(success_count+error_count)*100):.1f}%")
    
    return success_count, error_count

# Example usage in DAG:
"""
def store_inquiries_via_api(**context):
    inquiries = context['task_instance'].xcom_pull(
        task_ids='validate_data_quality',
        key='valid_inquiries'
    )
    
    if not inquiries:
        return 0
    
    success_count, error_count = send_inquiries_to_api(inquiries)
    
    # This would generate Prometheus metrics:
    # - HTTP requests to /api/v1/inquiries
    # - Processing duration
    # - Success/failure rates
    # - Model inference metrics
    
    return success_count
"""

if __name__ == "__main__":
    # Demo with sample data
    sample_inquiries = [
        {
            "subject": "Test inquiry 1",
            "body": "This is a test inquiry body",
            "sender_email": "test1@example.com",
            "metadata": {"source": "demo"}
        },
        {
            "subject": "Test inquiry 2", 
            "body": "Another test inquiry",
            "sender_email": "test2@example.com",
            "metadata": {"source": "demo"}
        }
    ]
    
    print("🚀 Demo: Sending inquiries to API...")
    send_inquiries_to_api(sample_inquiries)

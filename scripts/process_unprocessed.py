#!/usr/bin/env python3
"""
Script to process unprocessed inquiries in the database.
"""
import requests
import json
import time
from sqlalchemy import create_engine, text

def process_unprocessed_inquiries():
    """Process all unprocessed inquiries via API."""
    
    # Connect to database
    engine = create_engine("postgresql://postgres:postgres@postgres:5432/inquiry_automation")
    
    # Get unprocessed inquiries
    with engine.connect() as conn:
        query = text("""
            SELECT id, subject, body, sender_email, sender_name, timestamp, meta_data
            FROM inquiries 
            WHERE processed = false
            ORDER BY timestamp DESC
        """)
        
        result = conn.execute(query)
        unprocessed = result.fetchall()
    
    print(f"Found {len(unprocessed)} unprocessed inquiries")
    
    if not unprocessed:
        print("No unprocessed inquiries found!")
        return
    
    success_count = 0
    error_count = 0
    
    for inquiry in unprocessed:
        try:
            # Prepare API request
            metadata = {}
            if inquiry.meta_data:
                if isinstance(inquiry.meta_data, str):
                    metadata = json.loads(inquiry.meta_data)
                elif isinstance(inquiry.meta_data, dict):
                    metadata = inquiry.meta_data
            
            api_data = {
                "subject": inquiry.subject,
                "body": inquiry.body,
                "sender_email": inquiry.sender_email,
                "sender_name": inquiry.sender_name,
                "metadata": metadata
            }
            
            # Submit to API for processing
            response = requests.post(
                "http://api:8000/api/v1/inquiries/submit",
                json=api_data,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Processed inquiry {inquiry.id[:8]}... - Category: {result['data']['category']}")
                success_count += 1
            else:
                print(f"❌ Failed to process inquiry {inquiry.id[:8]}... - {response.status_code}")
                error_count += 1
                
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error processing inquiry {inquiry.id[:8]}... - {str(e)}")
            error_count += 1
    
    print(f"\n📊 Processing Results:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {error_count}")
    print(f"  📈 Success Rate: {(success_count/(success_count+error_count)*100):.1f}%")

if __name__ == "__main__":
    process_unprocessed_inquiries()

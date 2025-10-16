#!/bin/bash
# Test the Inquiry Automation API

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "🧪 Testing Inquiry Automation API"
echo "=================================="
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
HEALTH=$(curl -s "$API_URL/api/v1/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "$HEALTH"
fi
echo ""

# Test 2: Submit Technical Support Inquiry
echo -e "${YELLOW}Test 2: Submit Technical Support Inquiry${NC}"
TECH_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Cannot login to my account",
    "body": "I have been trying to log in for the past hour but keep getting an authentication error. This is blocking my work. Please help ASAP!",
    "sender_email": "tech.user@example.com",
    "sender_name": "Tech User"
  }')

if echo "$TECH_RESPONSE" | grep -q "success"; then
    INQUIRY_ID=$(echo "$TECH_RESPONSE" | grep -o '"inquiry_id":"[^"]*"' | cut -d'"' -f4)
    CATEGORY=$(echo "$TECH_RESPONSE" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
    URGENCY=$(echo "$TECH_RESPONSE" | grep -o '"urgency":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Inquiry submitted successfully${NC}"
    echo "  ID: $INQUIRY_ID"
    echo "  Category: $CATEGORY"
    echo "  Urgency: $URGENCY"
else
    echo -e "${RED}✗ Failed to submit inquiry${NC}"
    echo "$TECH_RESPONSE"
fi
echo ""

# Test 3: Submit Billing Inquiry
echo -e "${YELLOW}Test 3: Submit Billing Inquiry${NC}"
BILLING_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Incorrect charge on my account",
    "body": "I was charged twice for my subscription this month. I need a refund for the duplicate charge of $99.99.",
    "sender_email": "billing.user@example.com",
    "sender_name": "Billing User"
  }')

if echo "$BILLING_RESPONSE" | grep -q "success"; then
    CATEGORY=$(echo "$BILLING_RESPONSE" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
    DEPARTMENT=$(echo "$BILLING_RESPONSE" | grep -o '"department":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Billing inquiry submitted${NC}"
    echo "  Category: $CATEGORY"
    echo "  Department: $DEPARTMENT"
else
    echo -e "${RED}✗ Failed to submit billing inquiry${NC}"
fi
echo ""

# Test 4: Classify Text Only
echo -e "${YELLOW}Test 4: Classify Text (No Save)${NC}"
CLASSIFY_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/inquiries/classify?include_all_scores=false" \
  -H "Content-Type: application/json" \
  -d '"I would like to schedule a demo of your enterprise product for my team."')

if echo "$CLASSIFY_RESPONSE" | grep -q "category"; then
    echo -e "${GREEN}✓ Text classification successful${NC}"
    echo "$CLASSIFY_RESPONSE" | jq '.' 2>/dev/null || echo "$CLASSIFY_RESPONSE"
else
    echo -e "${RED}✗ Classification failed${NC}"
fi
echo ""

# Test 5: Get Statistics
echo -e "${YELLOW}Test 5: Get Statistics${NC}"
STATS=$(curl -s "$API_URL/api/v1/stats")
if echo "$STATS" | grep -q "total_inquiries"; then
    TOTAL=$(echo "$STATS" | grep -o '"total_inquiries":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ Statistics retrieved${NC}"
    echo "  Total Inquiries: $TOTAL"
    echo "$STATS" | jq '.' 2>/dev/null || echo "$STATS"
else
    echo -e "${RED}✗ Failed to get statistics${NC}"
fi
echo ""

# Test 6: Get Inquiry Status (if we have an ID)
if [ ! -z "$INQUIRY_ID" ]; then
    echo -e "${YELLOW}Test 6: Get Inquiry Status${NC}"
    STATUS=$(curl -s "$API_URL/api/v1/inquiries/$INQUIRY_ID")
    if echo "$STATUS" | grep -q "inquiry_id"; then
        echo -e "${GREEN}✓ Inquiry status retrieved${NC}"
        echo "$STATUS" | jq '.' 2>/dev/null || echo "$STATUS"
    else
        echo -e "${RED}✗ Failed to get inquiry status${NC}"
    fi
    echo ""
fi

echo "=================================="
echo -e "${GREEN}Testing complete!${NC}"
echo ""
echo "You can view:"
echo "  • API Docs:  $API_URL/docs"
echo "  • Dashboard: http://localhost:8501"
echo "  • Airflow:   http://localhost:8080"


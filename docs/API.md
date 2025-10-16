# API Documentation

Complete reference for the Inquiry Automation Pipeline API endpoints.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API does not require authentication. For production deployments, JWT authentication should be enabled.

## Endpoints

### Health Check

#### GET `/api/v1/health`

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "services": {
    "api": true,
    "models": true,
    "database": true,
    "routing": true
  }
}
```

**Status Codes:**
- `200 OK` - All services healthy
- `503 Service Unavailable` - One or more services unhealthy

---

### Submit Inquiry

#### POST `/api/v1/inquiries/submit`

Submit a new inquiry for classification and routing.

**Request Body:**
```json
{
  "subject": "URGENT: Cannot login to my account",
  "body": "I have been trying to log in for the past hour but keep getting an authentication error. This is blocking my work. Please help ASAP!",
  "sender_email": "user@example.com",
  "sender_name": "John Doe",
  "metadata": {
    "source": "email",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Inquiry processed successfully",
  "data": {
    "inquiry_id": "550e8400-e29b-41d4-a716-446655440000",
    "category": "technical_support",
    "urgency": "high",
    "sentiment": "negative",
    "department": "technical_support",
    "consultant": "Tech Team A",
    "priority_score": 78.5,
    "escalated": false
  }
}
```

**Validation Rules:**
- `subject`: Required, 1-500 characters
- `body`: Required, 1-10,000 characters
- `sender_email`: Required, valid email format
- `sender_name`: Optional
- `metadata`: Optional object

**Status Codes:**
- `201 Created` - Inquiry processed successfully
- `400 Bad Request` - Invalid request data
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Processing error

---

### Get Inquiry Status

#### GET `/api/v1/inquiries/{inquiry_id}`

Get the status and details of a specific inquiry.

**Path Parameters:**
- `inquiry_id` (string): Unique identifier of the inquiry

**Response:**
```json
{
  "inquiry_id": "550e8400-e29b-41d4-a716-446655440000",
  "subject": "URGENT: Cannot login to my account",
  "sender_email": "user@example.com",
  "timestamp": "2024-01-15T10:30:00Z",
  "processed": true,
  "prediction": {
    "category": "technical_support",
    "urgency": "high",
    "sentiment": "negative"
  },
  "routing": {
    "department": "technical_support",
    "consultant": "Tech Team A",
    "priority_score": 78.5,
    "escalated": false,
    "status": "pending"
  }
}
```

**Status Codes:**
- `200 OK` - Inquiry found
- `404 Not Found` - Inquiry not found
- `500 Internal Server Error` - Database error

---

### Classify Text

#### POST `/api/v1/inquiries/classify`

Classify text without saving to database (useful for testing).

**Query Parameters:**
- `include_all_scores` (boolean, optional): Include confidence scores for all categories (default: false)

**Request Body:**
```json
"Cannot access my dashboard, getting 500 error"
```

**Response:**
```json
{
  "category": "technical_support",
  "category_confidence": 0.89,
  "sentiment": "negative",
  "sentiment_confidence": 0.72,
  "urgency": "high",
  "urgency_confidence": 0.85,
  "all_scores": {
    "category": {
      "technical_support": 0.89,
      "billing": 0.03,
      "sales": 0.02,
      "hr": 0.01,
      "legal": 0.02,
      "product_feedback": 0.03
    },
    "sentiment": {
      "positive": 0.15,
      "neutral": 0.13,
      "negative": 0.72
    },
    "urgency": {
      "low": 0.05,
      "medium": 0.10,
      "high": 0.85,
      "critical": 0.00
    }
  }
}
```

**Status Codes:**
- `200 OK` - Classification successful
- `400 Bad Request` - Invalid text input
- `500 Internal Server Error` - Model error

---

### Get Statistics

#### GET `/api/v1/stats`

Get pipeline statistics and analytics.

**Query Parameters:**
- `days` (integer, optional): Number of days to include in statistics (default: 7)

**Response:**
```json
{
  "total_inquiries": 1250,
  "processed_inquiries": 1245,
  "processing_rate": "99.6%",
  "category_distribution": {
    "technical_support": 375,
    "billing": 250,
    "sales": 200,
    "hr": 125,
    "legal": 100,
    "product_feedback": 300
  },
  "department_distribution": {
    "technical_support": 375,
    "finance": 250,
    "sales": 200,
    "hr": 125,
    "legal": 100,
    "product_management": 300
  },
  "escalated_inquiries": 75,
  "escalation_rate": "6.0%"
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved
- `500 Internal Server Error` - Database error

---

### Prometheus Metrics

#### GET `/api/v1/metrics`

Expose Prometheus metrics for monitoring.

**Response:**
Prometheus-formatted metrics including:
- HTTP request metrics
- Model inference metrics
- Pipeline processing metrics
- Database query metrics
- System health metrics

**Content-Type:** `text/plain; version=0.0.4; charset=utf-8`

---

## Data Models

### InquiryCategory

```json
{
  "technical_support": "Technical Support and IT issues",
  "billing": "Billing and payments",
  "sales": "Sales and product inquiries",
  "hr": "Human resources and HR",
  "legal": "Legal and compliance",
  "product_feedback": "Product feedback and suggestions"
}
```

### UrgencyLevel

```json
{
  "low": "Low priority, no rush",
  "medium": "Medium priority, handle when possible",
  "high": "High priority, needs quick response",
  "critical": "Critical, requires immediate attention"
}
```

### SentimentType

```json
{
  "positive": "Positive sentiment",
  "neutral": "Neutral sentiment",
  "negative": "Negative sentiment"
}
```

### Department

```json
{
  "technical_support": "Technical Support Team",
  "finance": "Finance Team",
  "sales": "Sales Team",
  "hr": "Human Resources",
  "legal": "Legal Team",
  "product_management": "Product Management",
  "escalation": "Senior Management"
}
```

## Error Responses

### Validation Error

```json
{
  "success": false,
  "message": "Validation error",
  "error": "subject: ensure this value has at most 500 characters",
  "data": null
}
```

### Processing Error

```json
{
  "success": false,
  "message": "Error processing inquiry",
  "error": "Model inference failed: CUDA out of memory",
  "data": null
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production, consider implementing:

- Per-IP rate limiting
- Per-user rate limiting
- Burst protection

## CORS

CORS is enabled for all origins in development. For production, configure specific allowed origins.

## Examples

### cURL Examples

**Submit an inquiry:**
```bash
curl -X POST "http://localhost:8000/api/v1/inquiries/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Login issues",
    "body": "Cannot access my account",
    "sender_email": "user@example.com"
  }'
```

**Classify text:**
```bash
curl -X POST "http://localhost:8000/api/v1/inquiries/classify?include_all_scores=true" \
  -H "Content-Type: application/json" \
  -d '"Need help with billing"'
```

**Get statistics:**
```bash
curl "http://localhost:8000/api/v1/stats?days=30"
```

### Python Examples

```python
import requests

# Submit inquiry
response = requests.post(
    "http://localhost:8000/api/v1/inquiries/submit",
    json={
        "subject": "Technical issue",
        "body": "System is not responding",
        "sender_email": "user@example.com"
    }
)
result = response.json()
print(f"Inquiry ID: {result['data']['inquiry_id']}")

# Get inquiry status
inquiry_id = result['data']['inquiry_id']
status = requests.get(f"http://localhost:8000/api/v1/inquiries/{inquiry_id}")
print(status.json())
```

### JavaScript Examples

```javascript
// Submit inquiry
const response = await fetch('http://localhost:8000/api/v1/inquiries/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    subject: 'Technical issue',
    body: 'System is not responding',
    sender_email: 'user@example.com'
  })
});

const result = await response.json();
console.log('Inquiry ID:', result.data.inquiry_id);
```

## SDKs and Client Libraries

Currently, no official SDKs are provided. You can generate client libraries using:

- **OpenAPI Generator**: https://openapi-generator.tech/
- **Swagger Codegen**: https://swagger.io/tools/swagger-codegen/

The OpenAPI specification is available at `/docs` endpoint.

## Support

For API support:
- Check the health endpoint first
- Review error messages in responses
- Check application logs
- Contact the development team

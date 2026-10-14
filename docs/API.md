# API Reference

Base URL: `http://localhost:8000/api/v1`

All authenticated endpoints require: `Authorization: Bearer <access_token>`

---

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register citizen account |
| POST | `/auth/login` | Public | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | Public | Refresh access token |
| POST | `/auth/logout` | Required | Revoke refresh token |
| GET | `/auth/me` | Required | Get current user profile |

### POST /auth/register
```json
// Request
{
  "email": "citizen@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+919876543210"
}

// Response 201
{
  "id": "...",
  "email": "citizen@example.com",
  "full_name": "John Doe",
  "role": "citizen"
}
```

### POST /auth/login
```json
// Request
{ "email": "citizen@example.com", "password": "SecurePass123!" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "role": "citizen", "full_name": "..." }
}
```

---

## Complaints

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/complaints` | Citizen | Submit new complaint |
| GET | `/complaints` | All | List complaints (filtered by role) |
| GET | `/complaints/{id}` | All | Get complaint details |
| PATCH | `/complaints/{id}/status` | Officer/Admin | Update status |
| POST | `/complaints/{id}/resolve` | Officer | Mark resolved with notes + proof |
| GET | `/complaints/{id}/timeline` | All | Status history |

### POST /complaints
```json
// Request (multipart/form-data)
{
  "title": "Broken streetlight on Main Road",
  "description": "Streetlight near bus stop has been non-functional for 2 weeks...",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "address": "Main Road, Sector 12, New Delhi",
  "images": [File, File]  // max 5 images, 5MB each
}

// Response 201
{
  "id": "...",
  "complaint_id": "CMP-2026-00042",
  "status": "ai_processing",
  "ai_metadata": {
    "summary": "Non-functional streetlight on Main Road for 2 weeks",
    "predicted_department": "Public Works",
    "predicted_priority": "medium",
    "confidence_score": 0.92,
    "is_duplicate": false
  }
}
```

### Query Parameters for GET /complaints
```
?status=in_progress
&priority=high
&department_id=...
&page=1
&limit=20
&sort=-created_at
```

---

## Notifications

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/notifications` | All | List user notifications |
| PATCH | `/notifications/{id}/read` | All | Mark as read |
| PATCH | `/notifications/read-all` | All | Mark all as read |

---

## Feedback

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/complaints/{id}/feedback` | Citizen | Submit post-resolution feedback |
| GET | `/complaints/{id}/feedback` | All | View feedback |

---

## Admin

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Admin | List all users |
| POST | `/admin/users` | Admin | Create officer/admin |
| PATCH | `/admin/users/{id}` | Admin | Update user |
| DELETE | `/admin/users/{id}` | Admin | Deactivate user |
| GET | `/admin/departments` | Admin | List departments |
| POST | `/admin/departments` | Admin | Create department |
| PATCH | `/admin/departments/{id}` | Admin | Update department |
| POST | `/admin/complaints/{id}/assign` | Admin | Manually assign officer |

---

## Analytics

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/analytics/overview` | Officer/Admin | Dashboard summary stats |
| GET | `/analytics/by-department` | Officer/Admin | Complaints grouped by department |
| GET | `/analytics/by-location` | Officer/Admin | Geographic distribution |
| GET | `/analytics/trends` | Admin | Time-series complaint trends |
| GET | `/analytics/resolution-time` | Admin | Avg resolution time analysis |
| GET | `/analytics/heatmap` | Officer/Admin | GeoJSON for heatmap |
| GET | `/analytics/officer-workload` | Admin | Officer assignment stats |
| GET | `/analytics/ai-insights` | Admin | AI prediction accuracy metrics |

### GET /analytics/overview Response
```json
{
  "total_complaints": 1247,
  "pending": 89,
  "in_progress": 156,
  "resolved": 982,
  "avg_resolution_hours": 48.5,
  "priority_distribution": {
    "low": 412, "medium": 523, "high": 245, "critical": 67
  },
  "resolution_rate": 78.7
}
```

---

## Error Responses

```json
// 400 Bad Request
{ "detail": "Validation error", "errors": [{ "field": "email", "message": "Invalid email format" }] }

// 401 Unauthorized
{ "detail": "Invalid or expired token" }

// 403 Forbidden
{ "detail": "Insufficient permissions" }

// 404 Not Found
{ "detail": "Complaint not found" }

// 429 Too Many Requests
{ "detail": "Rate limit exceeded. Try again in 60 seconds." }
```

---

## WebSocket (Optional — Real-time Updates)

```
WS /ws/notifications?token=<access_token>

// Server pushes:
{ "type": "status_change", "complaint_id": "...", "new_status": "in_progress" }
{ "type": "new_assignment", "complaint_id": "...", "priority": "high" }
```

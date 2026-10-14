# System Architecture

## Overview

The system is a **modular monolith**: one web portal, one API, one database. Access is role-based. AI routing runs on the server after a citizen submits a complaint.

Print figure: [`architecture-bw.svg`](architecture-bw.svg)

```
1. USERS                 Citizen          Officer          Admin
                                |               |              |
2. WEB PORTAL            Citizen views    Officer views    Admin views
                                      HTTPS / REST + JWT
3. API AND SERVICES      Auth   Complaints   Analytics   Notifications
                                      on new complaint
4. AI PIPELINE           Summarize → Classify → Deduplicate → Prioritize → Assign
                                      persist
5. DATA AND SERVICES     MongoDB          Cloudinary       Gemini / OpenAI
```

## Component Layers

### 1. Presentation Layer (Frontend)
- **Next.js 14 App Router** with role-based route groups
- **React Query** for server state management
- **Shadcn UI + Tailwind** for consistent design system
- **Leaflet.js** for complaint heatmaps

### 2. Application Layer (Backend)
- **FastAPI** REST API with OpenAPI documentation
- **Pydantic v2** for request/response validation
- **Dependency injection** for auth and database sessions
- **Service layer** encapsulating business logic

### 3. AI Processing Layer
- Runs synchronously on complaint submission (async queue optional)
- Pipeline: Summarize → Classify → Detect Duplicates → Predict Priority → Recommend Department
- Models: Sentence Transformers (embeddings), scikit-learn (priority), Gemini (summarization)

### 4. Data Layer
- **MongoDB Atlas** with indexed collections
- **Cloudinary** for image CDN storage
- **Redis** (optional) for caching embeddings and session data

## Authentication Flow

```
Citizen/Officer/Admin
        │
        ▼
   POST /auth/login
        │
        ▼
  Validate credentials (bcrypt)
        │
        ├──► Access Token (JWT, 30 min)
        └──► Refresh Token (JWT, 7 days, stored in DB)
        │
        ▼
  Subsequent requests: Authorization: Bearer <access_token>
        │
        ▼
  RBAC Middleware checks role + permissions
        │
        ▼
  Route handler executes
```

## Complaint Processing Flow

```
Citizen submits complaint
        │
        ▼
  Upload images → Cloudinary
        │
        ▼
  Save complaint (status: PENDING)
        │
        ▼
  AI Pipeline triggered:
    1. Generate summary (Gemini)
    2. Classify department (Sentence Transformers + cosine similarity)
    3. Check duplicates (embedding similarity > 0.85)
    4. Predict priority (keyword + ML classifier)
    5. Recommend department
        │
        ▼
  Update complaint with AI metadata
        │
        ▼
  Auto-assign to department officer (round-robin / workload-based)
        │
        ▼
  Notify officer + citizen
        │
        ▼
  Officer updates status → Citizen notified
        │
        ▼
  Resolution → Citizen provides feedback
```

## Role-Based Access Control

| Resource | Citizen | Officer | Admin |
|----------|---------|---------|-------|
| Submit complaint | ✅ | ❌ | ❌ |
| View own complaints | ✅ | ❌ | ❌ |
| View assigned complaints | ❌ | ✅ | ✅ |
| Update complaint status | ❌ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ✅ |
| Manage departments | ❌ | ❌ | ✅ |
| View analytics | ❌ | ✅ (limited) | ✅ |
| View AI predictions | ❌ | ✅ | ✅ |

## Scalability Considerations

- **Horizontal scaling**: Stateless FastAPI instances behind load balancer
- **Database**: MongoDB sharding by geographic region
- **AI**: Async task queue (Celery + Redis) for high-volume processing
- **CDN**: Cloudinary for global image delivery
- **Caching**: Redis for frequently accessed analytics aggregates

## Security

- JWT with short-lived access tokens + refresh token rotation
- bcrypt password hashing (cost factor 12)
- Input validation via Pydantic
- CORS restricted to frontend origin
- Rate limiting on auth endpoints
- File upload validation (type, size)
- MongoDB field-level encryption for PII (optional)

# Database Schema

MongoDB collections for the Civic Complaint Management System.

## Collections Overview

| Collection | Purpose |
|------------|---------|
| `users` | Citizens, officers, admins |
| `departments` | Government departments |
| `complaints` | Complaint records with AI metadata |
| `notifications` | User notifications |
| `refresh_tokens` | JWT refresh token store |
| `feedback` | Post-resolution citizen feedback |
| `analytics_snapshots` | Pre-computed analytics aggregates |

---

## users

```javascript
{
  _id: ObjectId,
  email: String,              // unique, indexed
  password_hash: String,
  full_name: String,
  phone: String,
  role: String,               // "citizen" | "officer" | "admin"
  department_id: ObjectId,    // officers only, ref: departments
  avatar_url: String,
  is_active: Boolean,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ role: 1 })
db.users.createIndex({ department_id: 1 })
```

---

## departments

```javascript
{
  _id: ObjectId,
  name: String,               // e.g. "Public Works", "Sanitation"
  code: String,               // e.g. "PWD", "SAN" — unique
  description: String,
  keywords: [String],         // for AI classification matching
  head_officer_id: ObjectId,  // ref: users
  is_active: Boolean,
  created_at: ISODate
}

// Indexes
db.departments.createIndex({ code: 1 }, { unique: true })
```

---

## complaints

```javascript
{
  _id: ObjectId,
  complaint_id: String,       // human-readable: "CMP-2026-00001"
  citizen_id: ObjectId,       // ref: users
  title: String,
  description: String,
  images: [{
    url: String,
    public_id: String,        // Cloudinary ID
    uploaded_at: ISODate
  }],
  location: {
    type: "Point",
    coordinates: [Number, Number],  // [longitude, latitude]
    address: String
  },
  status: String,             // see status enum below
  priority: String,           // "low" | "medium" | "high" | "critical"
  department_id: ObjectId,    // assigned department
  assigned_officer_id: ObjectId,
  
  // AI-generated metadata
  ai_metadata: {
    summary: String,
    predicted_department: String,
    predicted_priority: String,
    confidence_score: Number,
    is_duplicate: Boolean,
    duplicate_of: ObjectId,   // ref: complaints
    similarity_score: Number,
    embedding: [Number],      // 384-dim vector for duplicate detection
    processed_at: ISODate
  },

  resolution: {
    notes: String,
    proof_images: [{ url: String, public_id: String }],
    resolved_at: ISODate,
    resolved_by: ObjectId
  },

  status_history: [{
    status: String,
    changed_by: ObjectId,
    changed_at: ISODate,
    note: String
  }],

  created_at: ISODate,
  updated_at: ISODate
}

// Status enum: "pending" | "ai_processing" | "assigned" | "in_progress" | "resolved" | "closed" | "rejected"

// Indexes
db.complaints.createIndex({ complaint_id: 1 }, { unique: true })
db.complaints.createIndex({ citizen_id: 1, created_at: -1 })
db.complaints.createIndex({ assigned_officer_id: 1, status: 1 })
db.complaints.createIndex({ department_id: 1, status: 1 })
db.complaints.createIndex({ priority: 1 })
db.complaints.createIndex({ location: "2dsphere" })
db.complaints.createIndex({ "ai_metadata.is_duplicate": 1 })
db.complaints.createIndex({ created_at: -1 })
```

---

## notifications

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  type: String,               // "status_change" | "assignment" | "resolution" | "system"
  title: String,
  message: String,
  complaint_id: ObjectId,
  is_read: Boolean,
  created_at: ISODate
}

// Indexes
db.notifications.createIndex({ user_id: 1, is_read: 1, created_at: -1 })
```

---

## refresh_tokens

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  token_hash: String,
  expires_at: ISODate,
  created_at: ISODate,
  revoked: Boolean
}

// Indexes
db.refresh_tokens.createIndex({ user_id: 1 })
db.refresh_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
```

---

## feedback

```javascript
{
  _id: ObjectId,
  complaint_id: ObjectId,     // unique per complaint
  citizen_id: ObjectId,
  rating: Number,             // 1-5
  comment: String,
  created_at: ISODate
}

// Indexes
db.feedback.createIndex({ complaint_id: 1 }, { unique: true })
```

---

## analytics_snapshots

```javascript
{
  _id: ObjectId,
  period: String,             // "daily" | "weekly" | "monthly"
  date: ISODate,
  metrics: {
    total_complaints: Number,
    by_status: { pending: Number, in_progress: Number, resolved: Number },
    by_priority: { low: Number, medium: Number, high: Number, critical: Number },
    by_department: [{ department_id: ObjectId, count: Number }],
    avg_resolution_hours: Number,
    top_locations: [{ address: String, count: Number }]
  },
  created_at: ISODate
}
```

---

## Entity Relationship Diagram

```
users ──────────────┐
  │                 │
  │ citizen_id      │ assigned_officer_id
  ▼                 ▼
complaints ◄── department_id ── departments
  │
  ├── notifications
  ├── feedback
  └── ai_metadata (embedded)
```

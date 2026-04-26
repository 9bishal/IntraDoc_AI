# Step 11: API Security — Summary

## What Was Built

All API endpoints are secured with JWT authentication except explicitly public ones.

### Security Configuration

#### DRF Default (`settings.py`)
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

Every view inherits `IsAuthenticated` unless explicitly overridden.

### Endpoint Security Matrix

| Endpoint | Method | Auth Required | Notes |
|----------|--------|--------------|-------|
| `/api/auth/register/` | POST | ❌ No | Public |
| `/api/auth/login/` | POST | ❌ No | Public |
| `/api/auth/profile/` | GET | ✅ Yes | Own profile only |
| `/api/auth/token/refresh/` | POST | ❌ No | Valid refresh token |
| `/api/documents/upload/` | POST | ✅ Yes | + RBAC department check |
| `/api/documents/` | GET | ✅ Yes | Filtered by role |
| `/api/documents/stats/` | GET | ✅ Yes | Filtered by role |
| `/api/chat/` | POST | ✅ Yes | RAG pipeline |
| `/api/chat/history/` | GET | ✅ Yes | Own history only |
| `/api/health/` | GET | ❌ No | System health |

### Authentication Flow
```
1. POST /api/auth/login/  →  { access, refresh }
2. Use header: Authorization: Bearer <access_token>
3. On expiry: POST /api/auth/token/refresh/  →  { new access }
```

### Password Security
- BCryptSHA256 as primary password hasher
- Minimum 8-character password on registration
- Passwords never returned in API responses (`write_only=True`)

### Additional Security Measures
- `SECRET_KEY` loaded from environment variable
- `DEBUG` controlled via environment variable
- `ALLOWED_HOSTS` configured via environment variable
- CSRF protection enabled (Django default)
- Clickjacking protection via `X-Frame-Options` middleware

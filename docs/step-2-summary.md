# Step 2: Authentication — Summary

## What Was Built

JWT-based authentication system using `djangorestframework-simplejwt` with bcrypt password hashing.

### Password Security
- Configured `BCryptSHA256PasswordHasher` as the **primary** password hasher in `settings.py`
- PBKDF2 as fallback for compatibility
- Passwords are never stored in plaintext

### JWT Configuration (`settings.py`)
- Access token lifetime: 60 minutes (configurable via `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`)
- Refresh token lifetime: 7 days (configurable via `JWT_REFRESH_TOKEN_LIFETIME_DAYS`)
- Token rotation enabled on refresh
- Auth header format: `Bearer <token>`

## APIs Created

### `POST /api/auth/register/`
- **Body**: `{"username": "...", "password": "...", "role": "HR"}`
- **Response**: User details + JWT access/refresh tokens
- **Auth**: None (public endpoint)

### `POST /api/auth/login/`
- **Body**: `{"username": "...", "password": "..."}`
- **Response**: User details + JWT access/refresh tokens
- **Auth**: None (public endpoint)

### `GET /api/auth/profile/`
- **Response**: Authenticated user's profile data
- **Auth**: JWT Bearer token required

### `POST /api/auth/token/refresh/`
- **Body**: `{"refresh": "<refresh_token>"}`
- **Response**: New access token + rotated refresh token
- **Auth**: Valid refresh token required

## Key Logic
- `UserLoginSerializer.validate()` uses Django's `authenticate()` which internally uses bcrypt
- Registration auto-generates JWT tokens so the user is immediately authenticated
- All subsequent API calls require `Authorization: Bearer <access_token>` header

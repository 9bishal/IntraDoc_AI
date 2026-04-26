# Step 1: Database Models — Summary

## What Was Built

Three core database models for the application:

### 1. `User` Model (`users/models.py`)
- Custom user model extending `AbstractBaseUser` + `PermissionsMixin`
- Fields: `username`, `password` (bcrypt-hashed), `role`, `is_active`, `is_staff`, `created_at`, `updated_at`
- `Role` enum: `ADMIN`, `HR`, `ACCOUNTS`, `LEGAL`
- Custom `UserManager` with `create_user()` and `create_superuser()` methods
- Helper properties: `is_admin`, `department`

### 2. `Document` Model (`documents/models.py`)
- Fields: `file`, `department`, `uploaded_by` (FK→User), `upload_date`, `filename`, `is_processed`, `chunk_count`
- `Department` enum: `hr`, `accounts`, `legal`
- Dynamic upload path: `media/documents/<department>/<filename>`
- Auto-populates `filename` from uploaded file on save

### 3. `ChatLog` Model (`chat/models.py`)
- Fields: `user` (FK→User), `query`, `response`, `context_chunks`, `timestamp`
- Records each interaction for audit trail

## Key Design Decisions
- Used `AUTH_USER_MODEL = 'users.User'` to override Django's default user model
- Roles are TextChoices for type safety and DB-level validation
- Department values are lowercase to match FAISS index naming convention
- `chunk_count` and `is_processed` on Document enable tracking of processing status

## Database Tables
| Table        | Primary Key | Key Indexes              |
|-------------|-------------|--------------------------|
| `users`     | `id`        | `username` (unique)      |
| `documents` | `id`        | `department`, `upload_date` |
| `chat_logs` | `id`        | `user_id`, `timestamp`   |

# Step 3: Role-Based Access Control (RBAC) — Summary

## What Was Built

A comprehensive RBAC system in `users/permissions.py` with DRF permission classes and utility functions.

### Role → Department Mapping

| Role      | Accessible Departments          |
|-----------|--------------------------------|
| ADMIN     | `hr`, `accounts`, `legal` (ALL) |
| HR        | `hr` only                      |
| ACCOUNTS  | `accounts` only                |
| LEGAL     | `legal` only                   |

### Permission Classes

#### `IsAdmin`
- DRF `BasePermission` subclass
- Allows access only to users with `role == ADMIN`
- Used for admin-only endpoints

#### `IsAdminOrOwnerDepartment`
- Checks both `has_permission` (user is authenticated) and `has_object_permission` (resource belongs to user's department)
- ADMIN bypasses department check
- Used for object-level access control

### Utility Functions

#### `get_accessible_departments(user) → list[str]`
- Returns list of department keys the user can query
- ADMIN → `['hr', 'accounts', 'legal']`
- Others → `[user.department]` (single-element list)

#### `can_access_department(user, department) → bool`
- Quick check if a user can access a specific department
- Used in document upload and listing views

## Key Logic
- RBAC is enforced at **view level** (not middleware) for flexibility
- The same utility functions are reused by document views, chat views, and the RAG pipeline
- Department names are always lowercase for consistency

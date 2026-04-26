# Role-Based Access Control (RBAC) System

## Overview

The IntraDoc AI system implements a comprehensive role-based access control system that governs:
- Which departments' documents a user can **search/read**
- Which departments' documents a user can **upload to**
- Which endpoints a user can access

## Roles & Permissions

### 1. ADMIN
**Access Level**: Full system access

| Permission | Access |
|-----------|--------|
| Search/Read Documents | All departments (HR, Accounts, Legal) |
| Upload Documents | All departments (HR, Accounts, Legal) |
| View All Users | ✅ Yes |
| System Management | ✅ Full access |

**Use Case**: System administrators and executives

---

### 2. HR
**Access Level**: HR Department only

| Permission | Access |
|-----------|--------|
| Search/Read Documents | HR department only |
| Upload Documents | HR department only |
| View Other Users | ❌ No (can only see HR docs) |
| Access Other Departments | ❌ No |

**Use Case**: HR department staff

---

### 3. ACCOUNTS
**Access Level**: Accounts Department only

| Permission | Access |
|-----------|--------|
| Search/Read Documents | Accounts department only |
| Upload Documents | Accounts department only |
| View Other Users | ❌ No (can only see Accounts docs) |
| Access Other Departments | ❌ No |

**Use Case**: Finance and Accounts department staff

---

### 4. LEGAL
**Access Level**: Legal Department only

| Permission | Access |
|-----------|--------|
| Search/Read Documents | Legal department only |
| Upload Documents | Legal department only |
| View Other Users | ❌ No (can only see Legal docs) |
| Access Other Departments | ❌ No |

**Use Case**: Legal department staff

---

### 5. FINANCE
**Access Level**: HR Department (read & write)

| Permission | Access |
|-----------|--------|
| Search/Read Documents | HR department only |
| Upload Documents | HR department only |
| View Other Departments | ❌ No |
| Access Accounts/Legal | ❌ No |

**Use Case**: Finance/Payroll staff who need HR-related documents (salary, benefits, etc.)

---

## Technical Implementation

### 1. User Model (`users/models.py`)

```python
class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    HR = 'HR', 'HR'
    ACCOUNTS = 'ACCOUNTS', 'Accounts'
    LEGAL = 'LEGAL', 'Legal'
    FINANCE = 'FINANCE', 'Finance'

class User(AbstractBaseUser, PermissionsMixin):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.HR,
    )
    
    @property
    def department(self):
        """Returns user's department based on role"""
        if self.role == Role.ADMIN:
            return 'all'
        elif self.role == Role.FINANCE:
            return 'hr'  # Finance is tied to HR department
        return self.role.lower()
```

### 2. Permission Functions (`users/permissions.py`)

#### `get_accessible_departments(user)`
Returns list of departments a user can search/read:

```python
def get_accessible_departments(user):
    if user.role == Role.ADMIN:
        return ['hr', 'accounts', 'legal']
    elif user.role == Role.FINANCE:
        return ['hr']  # Finance can only access HR docs
    return [user.department]
```

**Used in**: 
- Chat/RAG pipeline (search filtering)
- Document list view
- Query expansion

#### `can_access_department(user, department)`
Checks if user can access a specific department:

```python
def can_access_department(user, department):
    if user.role == Role.ADMIN:
        return True
    elif user.role == Role.FINANCE:
        return department.lower() == 'hr'
    return user.department == department.lower()
```

**Used in**: 
- Document upload validation
- Permission checks

### 3. FAISS Vector Store Integration

Each department has its own FAISS index:
- `faiss_indexes/hr_index.faiss` - HR documents
- `faiss_indexes/accounts_index.faiss` - Accounts documents
- `faiss_indexes/legal_index.faiss` - Legal documents

When a user searches:
1. System determines accessible departments
2. Retrieves chunks from those indexes only
3. User cannot access other departments' data

### 4. Document Upload Enforcement

**DocumentUploadView** (`documents/views.py`):
```python
# RBAC check: non-admin users can only upload to their department
if not can_access_department(request.user, department):
    return Response(
        {'error': f'You do not have permission to upload to the {department} department.'},
        status=status.HTTP_403_FORBIDDEN,
    )
```

---

## Test Users

Default test users created by `python manage.py seed_users`:

| Username | Password | Role | Department Access |
|----------|----------|------|-------------------|
| admin | admin1234 | ADMIN | All (HR, Accounts, Legal) |
| hr_user | hrpass1234 | HR | HR only |
| accounts_user | accpass1234 | ACCOUNTS | Accounts only |
| legal_user | legalpass1234 | LEGAL | Legal only |
| finance_user | finpass1234 | FINANCE | HR only |

---

## API Endpoints & RBAC

### Document Upload
```
POST /api/documents/upload/

RBAC Rules:
- ADMIN: can upload to any department
- HR: can upload to HR only
- ACCOUNTS: can upload to Accounts only
- LEGAL: can upload to Legal only
- FINANCE: can upload to HR only
```

**Request**:
```json
{
    "file": "<pdf_file>",
    "department": "hr"
}
```

### Document List
```
GET /api/documents/

RBAC Rules:
- ADMIN: sees all documents
- HR: sees HR documents only
- ACCOUNTS: sees Accounts documents only
- LEGAL: sees Legal documents only
- FINANCE: sees HR documents only
```

### Chat/Search
```
POST /api/chat/

RBAC Rules:
- Searches documents from accessible departments only
- Results filtered by user's department access
- Cannot see documents from other departments
```

**Request**:
```json
{
    "query": "What is the leave policy?"
}
```

---

## Data Flow with RBAC

```
User Request
    ↓
Authentication (JWT)
    ↓
Authorization Check (Role-based)
    ↓
Get Accessible Departments
    ↓
Filter Documents/Indexes
    ↓
Process Query (RAG)
    ↓
Return Results (from accessible departments only)
```

---

## Security Considerations

1. **Department Isolation**: Each department's data is strictly isolated
2. **No Cross-Department Access**: Users cannot query across unauthorized departments
3. **Upload Restrictions**: Only authorized users can upload to a department
4. **Index Separation**: FAISS indexes are kept separate per department
5. **Query Filtering**: RAG pipeline filters chunks by department access

---

## Adding New Roles

To add a new role (e.g., MANAGER):

### 1. Update User Model
```python
class Role(models.TextChoices):
    # ... existing roles ...
    MANAGER = 'MANAGER', 'Manager'
```

### 2. Update Permission Functions
```python
def get_accessible_departments(user):
    # ... existing logic ...
    elif user.role == Role.MANAGER:
        return ['hr', 'accounts']  # Manager can access multiple departments
    # ...

def can_access_department(user, department):
    # ... existing logic ...
    elif user.role == Role.MANAGER:
        return department.lower() in ['hr', 'accounts']
    # ...
```

### 3. Add Test User
```python
{'username': 'manager_user', 'password': 'managerpass1234', 'role': Role.MANAGER}
```

### 4. Run Migrations
```bash
python manage.py migrate
python manage.py seed_users
```

---

## Migration History

- **v1**: Initial RBAC with ADMIN, HR, ACCOUNTS, LEGAL roles
- **v2**: Added FINANCE role for HR-only access

---

## References

- User Model: `users/models.py`
- Permissions: `users/permissions.py`
- Document Views: `documents/views.py`
- RAG Pipeline: `ai/rag.py`

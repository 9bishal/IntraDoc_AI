# Step 15: Query Sharing Routes — Summary

Complete REST API with organized endpoints across multiple apps. Shareable query routes are now fully handled by the frontend application using React Router and URL Query parameters (`?dept=`).

## What Was Built

Shareable department-specific query interfaces that pre-filter documents by role.

## Route Structure

### New URL Patterns

**Location**: `/frontend/src/routes/AppRoutes.jsx` & `/frontend/src/components/SearchBox.jsx`

Routes are now handled by the React router, allowing seamless navigation via the global SearchBox autocomplete to department specific queries.

## Purpose

### Before Query Sharing
```
Manager wants HR team to ask about leave policy:
1. Manager sends HR team a note: "Use IntraDoc AI"
2. Each employee goes to http://localhost:5173/
3. Logs in with their credentials
4. Navigates to chat
5. Types query
6. Gets response filtered to their role
```

### After Query Sharing
```
Manager wants HR team to ask about leave policy:
1. Manager generates link: http://localhost:5173/query?dept=hr
2. Shares link with HR team
3. HR employee clicks link
4. The React application reads `?dept=hr` from the URL.
5. Auto-filtered to HR documents
6. Employee types query, gets HR-only answers
```

## Implementation

### React Router and Query Parameters

In the old Django-rendered template approach, there were dedicated views for each department. In the modern React SPA architecture, this is consolidated into a single highly-dynamic route:

#### `QueryPage.jsx` Component
```javascript
import { useSearchParams, useLocation } from 'react-router-dom';

// The component reads the intended department from either the SearchBox state or the URL query parameter.
const [searchParams, setSearchParams] = useSearchParams();
const initialDept = location.state?.department || searchParams.get('dept') || backendUser?.departments?.[0] || '';
const [department, setDepartment] = useState(initialDept);

// When the department changes, the URL is automatically updated to remain shareable.
const handleDepartmentChange = (e) => {
  const newDept = e.target.value;
  setDepartment(newDept);
  setSearchParams({ dept: newDept });
};
```

## Frontend Integration

### Modified Chat Interface

When accessed via `/query/*/`, the chat interface:

1. **Pre-filters department from URL Parameter**
   ```javascript
   const [searchParams] = useSearchParams();
   const department = searchParams.get('dept');  // From URL e.g., /query?dept=hr
   ```

2. **Shows department banner**
   ```
   ┌────────────────────────────────┐
   │ 🏢 Querying: HR Department     │
   │    (Leave policies, benefits)  │
   └────────────────────────────────┘
   ```

3. **Auto-filters query API calls**
   ```javascript
   // ChatView detects pre-filtered department
   // Adds department filter to FAISS search
   // User can only see HR documents
   ```

4. **Shows relevant suggestions**
   - Pre-populated in chat suggestions area
   - Quick-click buttons for common queries
   - Context-aware help text

## Usage Examples

### Example 1: HR Manager Shares HR Queries

**Manager Action:**
```
1. Copy link: https://intradoc.company.com/query/hr/
2. Paste in Slack/Email: "Check our HR policies here!"
3. HR staff click link
```

**Employee Experience:**
```
1. Click link → lands on pre-configured HR chat
2. See suggestion: "What is the annual leave policy?"
3. Click suggestion → auto-populated in input
4. Click Send → response shows only HR documents
```

**Result:**
- HR staff get instant HR-filtered answers
- No confusion about access restrictions
- Reduced support burden on HR department

### Example 2: Legal Team Shares Contract Info

**Legal Manager Action:**
```
1. Generate link: https://intradoc.company.com/query/legal/
2. Share in company wiki under "Contracts" section
```

**Employee Experience:**
```
1. Click link → lands on legal query interface
2. See suggestion: "Show me contracts"
3. Get relevant contract information
4. No access to HR/Finance docs (as expected)
```

### Example 3: Admin Views All Departments

**Admin Action:**
```
1. Use link: https://intradoc.company.com/query/admin/
2. Query across all departments
```

**Result:**
```
Query: "Compare HR leave and Legal holidays"
Response: Access to both HR and Legal documents
Benefit: Cross-functional analysis possible
```

## API Integration

### How Query Routes Call Backend API

```
GET /query?dept=hr
  ↓
React Router parses the `dept` URL parameter
  ↓
QueryPage state is initialized to `hr`
  ↓
Frontend sends query to backend:
POST /api/chat/ { query: "...", department: "hr" }
  ↓
Backend applies RBAC filter:
  IF user_role != ADMIN AND requested_dept != user_dept:
    DENY access
  ↓
FAISS search filters by department
  ↓
Returns only HR documents
```

## Security Considerations

### Access Control

1. **URL-based but secured**
   - `/query/hr/` shows HR interface
   - Backend still validates user permissions
   - Admin can see all routes
   - Non-admin cannot access unauthorized departments

2. **Backend Validation**
   ```python
   # Even if user directly calls POST /api/chat/
   # with department='finance'
   # Backend checks:
   IF user.role != Role.FINANCE and user.role != Role.ADMIN:
       REJECT query
   ```

3. **No information leakage**
   - `/query/finance/` shows what's in Finance
   - But only Finance employees can actually query it
   - Non-Finance users get "Access Denied"

### Rate Limiting (Recommended)

```python
# Future enhancement: Add rate limiter
from rest_framework.throttling import UserRateThrottle

class QueryThrottle(UserRateThrottle):
    scope = 'query'
    THROTTLE_RATES = {
        'query': '100/hour'  # 100 queries per hour per user
    }
```

## Analytics & Tracking

### What Gets Logged

When user accesses `/query?dept=*`:
```python
ChatLog.objects.create(
    user=user,
    query=query,
    response=response,
    context_chunks=chunks,
    # New field (optional):
    accessed_via='query_route',  # Track query sharing usage
    department_filtered='hr'       # Which route used
)
```

### Reporting Possible Metrics

```
1. Most used query routes
   - /query?dept=hr → 523 queries this month
   - /query?dept=legal → 127 queries this month
   - /query?dept=admin → 234 queries this month

2. Popular questions by department
   - HR: "Leave policy" (most asked)
   - Legal: "Contract terms" (most asked)
   - Finance: "Budget info" (most asked)

3. Cross-department queries (admin only)
   - 45 comparisons made this month
   - Most common: HR vs Finance
```

## Customization Options

### Adding New Department Routes

To add a new department like "OPERATIONS":

```python
# 1. Update users/models.py
class Role(TextChoices):
    # ...existing...
    OPERATIONS = 'operations', 'Operations'

# 2. Add URL pattern in core/urls.py
path('query/operations/', views.QueryOperationsView.as_view(), name='query-operations'),

# 3. Restart server
python manage.py runserver

# 4. React frontend automatically picks up the new role context.

# 4. Restart server
python manage.py runserver
```

## Link Sharing Best Practices

### For Managers/Leaders

✅ **DO:**
- Share links in company communications
- Include context: "Check leave policies here"
- Add to internal wiki/knowledge base
- Use QR codes for easier sharing
- Pin in team Slack channels

❌ **DON'T:**
- Share outside company (confidentiality)
- Change URL manually (breaks routing)
- Assume users understand pre-filtering
- Use unshortened long URLs

### Link Shortening

```
Long URL:   https://intradoc.company.com/query?dept=hr
Short URL:  https://short.link/hr-docs
QR Code:    [scan to get HR docs]

Using bit.ly or company shortener:
1. Generate short link
2. Test in browser
3. Share in communications
```

## Testing Query Routes

### Browser Route Testing

Since these routes are now fully handled client-side by React Router, manual testing involves verifying the component loads the state correctly in the browser.

```javascript
// Open in browser:
http://localhost:5173/query?dept=hr
http://localhost:5173/query?dept=legal
http://localhost:5173/query?dept=admin
```

### Frontend Testing

```javascript
// Test department pre-filling
1. Click /query?dept=hr link
2. Check React State: department === 'hr'
3. Try query: should only get HR results
4. Check: AI responses mention HR docs only

// Test cross-role access
1. Login as HR user
2. Try to access /query?dept=finance directly
3. Should be rejected by backend validation when API is called
```

## Future Enhancements

1. 🔄 **Custom Query Links** — Generate time-limited shareable links
2. 🔄 **Department Analytics** — Dashboard for each department's usage
3. 🔄 **Scheduled Reports** — Auto-email query summaries to managers
4. 🔄 **Query Templates** — Save common queries as templates
5. 🔄 **Bulk Operations** — Query multiple documents at once

---

**Query sharing routes provide easy, secure access to department-specific information without extra configuration.**

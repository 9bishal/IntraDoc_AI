# Step 14: Frontend UI — Summary

## What Was Built

Complete responsive single-page application (SPA) with modern dark-themed interface.

### File Structure
- **Location**: `/frontend/` (React application)
- **Technology**: React.js + Tailwind CSS / Vanilla CSS
- **Framework**: Vite/React SPA

## Key Frontend Components

### 1. **Layout Structure**
```html
<div class="app-container">
  <!-- Sidebar (left) -->
  <div class="sidebar">
    - Header with logo
    - Auth section (login/register)
    - User badge when logged in
    - Document upload area
    - Suggestions section
  </div>
  
  <!-- Main Chat Area (right) -->
  <div class="main-content">
    - Chat messages container
    - Query input field with send button
    - Typing indicator animation
    - Response streaming display
  </div>
</div>
```

### 2. **Color Scheme & Theming**
CSS Variables defined in `:root`:
```css
--bg-primary: #0a0e1a          /* Dark background */
--accent: #6366f1              /* Purple accent */
--green: #10b981               /* Success color */
--red: #ef4444                 /* Error color */
--text-primary: #f1f5f9        /* Main text */
--text-secondary: #94a3b8      /* Secondary text */
--user-bubble: linear-gradient(135deg, #6366f1, #8b5cf6)
--ai-bubble: #1e293b
```

### 3. **Responsive Design**
- **Sidebar**: 320px fixed width
- **Main area**: Flexible, fills remaining space
- **Grid layout**: `grid-template-columns: 320px 1fr`
- **Scrollable containers**: Messages and sidebar content independently scroll
- **Mobile**: Sidebar collapses on smaller screens (can be enhanced)

## Core JavaScript Functions

### Authentication Functions

#### `registerUser()`
```javascript
- POST /api/users/register/
- Collect: username, email, password, role, department
- Validate: password length, email format
- Show: success/error toast
- Auto-login after registration
```

#### `loginUser()`
```javascript
- POST /api/users/login/
- Collect: username, password
- Response: access_token, refresh_token
- Store in localStorage: token, refresh_token, user_role
- Update UI: show user profile, hide auth section
```

#### `logout()`
```javascript
- Clear localStorage tokens and user data
- Reset UI to login state
- Redirect to chat area (need login)
```

### Document Management Functions

#### `uploadDocument()`
```javascript
- Detect file drop or file input
- Validate: file type is PDF
- Validate: file size < 50MB
- POST /api/documents/upload/
- Payload: FormData with file + department
- Show progress: uploading status
- Handle response: document ID, filename
- Refresh document list
```

#### `loadDocuments()`
```javascript
- GET /api/documents/
- Display list of uploaded documents
- Show: filename, department, upload date, size
- Allow: delete (soft delete), view metadata
```

### Chat Functions

#### `sendQuery()`
```javascript
Query Flow:
1. Get input from #query-input field
2. Validate: not empty
3. Add user message to chat display
4. Remove welcome card if visible
5. Show typing indicator
6. POST /api/chat/ with query
7. Stream response chunk by chunk
8. Accumulate full response
9. Remove typing indicator
10. Display AI response
11. Log to chat history
12. Clear input field
13. Scroll to bottom
14. Re-enable input
```

#### `formatMarkdown(text)`
```javascript
- Convert simple markdown to styled text
- Support: **bold**, *italic*, bullet points
- Preserve code blocks with monospace font
- Escape HTML to prevent XSS
```

#### `createMessage(content, type, meta)`
```javascript
- type: 'user' | 'ai'
- Create message wrapper with:
  - Avatar (initials for user, ✦ for AI)
  - Message bubble with content
  - Metadata (chunks_used, sources if AI)
  - Timestamp
- Apply appropriate styling based on type
- Return DOM elements for insertion
```

### Real-time Features

#### `addTypingIndicator()`
```javascript
- Show animated three-dot loader
- Indicate LLM is generating response
- Remove when response starts streaming
```

#### `scrollToBottom()`
```javascript
- Auto-scroll chat to latest message
- Called on every new message
- Smooth user experience
```

### Utility Functions

#### `showToast(message, type)`
```javascript
- type: 'success' | 'error' | 'info' | 'warning'
- Display temporary notification
- Auto-hide after 3 seconds
- Positioned: top-right corner
```

#### `checkHealth()`
```javascript
- GET /api/health/
- Verify LLM connectivity
- Verify database status
- Verify FAISS indexes
- Display status indicator
```

## UI Components

### 1. **Message Bubbles**
```css
.msg-bubble {
  /* User: purple gradient */
  /* AI: dark gray */
  border-radius: 16px
  padding: 12px 16px
  max-width: 70%
  word-wrap: break-word
}
```

### 2. **Input Area**
```
┌─────────────────────────────────┬───┐
│ Type your question here...      │ ► │ (Send button)
└─────────────────────────────────┴───┘
```

### 3. **Welcome Card**
- Shown when no messages in chat
- Display: app description, suggestions, quick tips
- Removed when first message sent

### 4. **User Badge**
- Shows: user avatar (initials), username, role
- Located: sidebar bottom
- Avatar: circular with user bubble gradient

## Event Listeners

| Event | Handler | Action |
|-------|---------|--------|
| `DOMContentLoaded` | Init app | Load user, check auth, restore theme |
| `click #send-btn` | `sendQuery()` | Send chat message |
| `keydown #query-input` | `sendQuery()` (if Enter) | Send on Enter key |
| `change #file-input` | `uploadDocument()` | Handle file selection |
| `dragover .upload-area` | Add `.drag-over` class | Highlight drag area |
| `drop .upload-area` | `uploadDocument()` | Handle file drop |
| `click .logout-btn` | `logout()` | Clear auth and reset |
| `click .chat-history-btn` | `loadChatHistory()` | Show previous chats |

## Performance Optimizations

1. **Local Storage**: Cache tokens to avoid re-login
2. **Lazy Loading**: Load chat history only on demand
3. **Debouncing**: Throttle file upload to prevent double-submit
4. **CSS Animations**: Use hardware-accelerated transforms
5. **Message Virtualization**: Only render visible messages (future enhancement)

## Security Measures

1. **Token Storage**: JWT in localStorage (XSS risk mitigated by CSP)
2. **CORS**: Frontend must be on allowed origin list
3. **CSRF**: Not needed (JWT instead of cookies)
4. **Input Validation**: Client-side + server-side validation
5. **HTML Escaping**: Prevent XSS in message display

## Browser Compatibility

- **Chrome/Edge**: ✅ Fully supported
- **Firefox**: ✅ Fully supported
- **Safari**: ✅ Fully supported
- **IE 11**: ⚠️ Partial (requires polyfills)

## Styling Overview

| Element | Primary Color | Hover State |
|---------|--------------|-------------|
| Buttons (Primary) | `#6366f1` (indigo) | Brighter + glow effect |
| Buttons (Secondary) | Transparent | `rgba(255, 255, 255, 0.08)` |
| Buttons (Danger) | `#ef4444` (red) | Darker red |
| Input Fields | Dark with subtle border | Focus: indigo border + glow |
| Badges | `#10b981` (green) | Glow effect on hover |
| User Avatar | Gradient `#6366f1 → #8b5cf6` | Same gradient |

## State Management

### Global Variables
```javascript
let token = null;              // JWT access token
let refreshToken = null;       // JWT refresh token
let userRole = null;           // User's role (HR, ADMIN, etc.)
let userName = null;           // Current user's username
let isAuthenticated = false;   // Auth state
```

### LocalStorage Keys
```javascript
localStorage.getItem('token')
localStorage.getItem('refresh_token')
localStorage.getItem('user_role')
localStorage.getItem('user_name')
localStorage.getItem('theme')    // Light/dark mode (future)
```

## Future Enhancements

1. 🔄 **Dark/Light Mode Toggle** — CSS variable switching
2. 🔄 **Message Search** — Filter chat history
3. 🔄 **Export Chat** — Download as PDF or JSON
4. 🔄 **Voice Input** — Speech-to-text for queries
5. 🔄 **Customizable Themes** — User preference storage
6. 🔄 **Mobile Responsiveness** — Full mobile UI
7. 🔄 **Progressive Web App** — Offline support

## Testing Frontend

### Manual Testing Steps
1. Open browser DevTools (F12)
2. Check Console for errors
3. Test auth flow: register → login → logout
4. Test upload: drag PDF → verify display
5. Test chat: send query → verify response displays
6. Check Network tab: verify API calls

### Browser DevTools Tips
- **Console**: Shows JS errors and logs
- **Network**: View API requests/responses
- **Application → Storage**: Check localStorage tokens
- **Responsive Design Mode**: Test mobile view

**All frontend code is structured as a modern React application within the `/frontend/` directory.**

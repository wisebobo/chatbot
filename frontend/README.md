# Enterprise Chatbot - Frontend Test Platform

A comprehensive test platform for the Enterprise Chatbot backend API.

##  File Structure

```
frontend/
 index.html    # Main page (HTML + CSS)
 app.js        # JavaScript logic
 README.md     # This file
```

##  Quick Start

### 1. Start Backend Service

Ensure the backend is running:

```bash
cd e:\Python\chatbot
python main.py
```

The service will start at `http://localhost:8000`

### 2. Open Frontend Page

Open `frontend/index.html` in your browser:
- **Windows**: Double-click the file
- **Or enter in browser**: `file:///e:/Python/chatbot/frontend/index.html`

##  Features

### 1. Authentication
- **Test Credentials** (Local Mode):
  - Username: `admin`, Password: `admin123`
  - Username: `testuser`, Password: `testpass`
  - Username: `demo`, Password: `demo123`
- **LDAP Authentication**: If configured in `.env`, uses Active Directory
- **Automatic Fallback**: Falls back to local test mode if LDAP unavailable

### 2. Chat Interface
- Real-time conversation with AI assistant
- Typing indicator animation
- Session management
- Message timestamps
- User/bot message differentiation

### 3. Wiki Management
- View all wiki articles
- Display article metadata (type, version, confidence)
- Refresh functionality
- Add article feature (coming soon)

### 4. Database Viewer
- Browse database tables
- View wiki articles data
- View API keys information
- View chat sessions history
- Status indicators (Active/Inactive)

##  Configuration

To change API endpoint, edit `app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';  // Change to your backend URL
```

##  Available Pages

### Chat Page
- Send messages to AI assistant
- View conversation history
- Monitor session ID

### Wiki Management Page
- Browse knowledge base articles
- View article details
- Filter by type/category

### Database Viewer Page
- Select table from dropdown
- View raw database records
- See status badges for active/inactive items

##  Troubleshooting

### Issue: Cannot connect to server
- Check if backend service is running
- Verify API_BASE_URL configuration
- Check browser console for errors

### Issue: Chat returns error message
- Ensure LLM_API_KEY is configured in `.env`
- Check backend server logs
- Verify LLM API service is accessible

### Issue: Login fails
- Use test credentials listed above
- Or configure LDAP in `.env` file
- Check network connectivity

##  Customization

This is a test page. You can modify styles and features as needed. For production use, consider creating a dedicated frontend project (React, Vue, Angular, etc.).

##  Notes

- **CORS**: Backend is configured to allow all origins (`*`)
- **Authentication**: Supports both JWT tokens and local test mode
- **Language**: All UI text is in English per project specifications
- **Responsive**: Works on different screen sizes

---

**Last Updated**: 2026-04-20  
**Version**: 1.0.0

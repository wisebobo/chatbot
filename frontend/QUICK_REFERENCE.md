# Quick Reference Card - Frontend Test Platform

##  Test Credentials
```
Username: admin      Password: admin123
Username: testuser   Password: testpass
Username: demo       Password: demo123
```

##  Quick Start
```bash
# Terminal 1: Start Backend
cd e:\Python\chatbot
python main.py

# Browser: Open Frontend
Double-click: frontend/index.html
```

##  Available Pages

###  Chat
- Send messages to AI assistant
- View conversation history
- Session ID tracking

###  Wiki Management
- Browse knowledge base articles
- View metadata (type, version, confidence)
- Refresh and add articles

###  Database Viewer
- Select table from dropdown
- View up to 100 records
- Status indicators (Active/Inactive)

##  API Endpoints Added

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/wiki/articles` | GET | List wiki articles |
| `/api/v1/database/{table}` | GET | Query database tables |

##  Configuration

Edit `frontend/app.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

##  Common Issues

**Cannot connect?**  Check if backend is running  
**Login fails?**  Use test credentials above  
**No data shown?**  Tables may be empty (normal)  

##  Tech Stack
- Pure HTML/CSS/JavaScript
- Fetch API for HTTP requests
- LocalStorage for token management
- No build tools required

---
**Need Help?** See `docs/FRONTEND_IMPLEMENTATION_SUMMARY.md`

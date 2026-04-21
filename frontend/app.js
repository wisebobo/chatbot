const API_BASE_URL = 'http://localhost:8000';

// Global variables
let sessionId = null;
let currentUser = null;
let authToken = null;
let messageFeedbackMap = new Map(); // Track feedback status for each message

// Simple local authentication for testing
const TEST_USERS = {
    'admin': 'admin123',
    'testuser': 'testpass',
    'demo': 'demo123'
};

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('welcomeTime').textContent = getCurrentTime();
});

// Login Handler
async function handleLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorDiv = document.getElementById('errorMsg');
    const loginBtn = document.getElementById('loginBtn');

    if (!username || !password) {
        showError('Please enter username and password');
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Signing in...';
    hideError();

    try {
        // Try LDAP authentication first
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            currentUser = username;
            localStorage.setItem('access_token', authToken);
            showMainApp();
        } else {
            // Fallback to local test authentication
            if (TEST_USERS[username] && TEST_USERS[username] === password) {
                authToken = 'test-token-' + Date.now();
                currentUser = username;
                localStorage.setItem('access_token', authToken);
                showMainApp();
            } else {
                showError('Invalid credentials. Please check username and password.');
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        // Fallback to local test authentication on network error
        if (TEST_USERS[username] && TEST_USERS[username] === password) {
            authToken = 'test-token-' + Date.now();
            currentUser = username;
            localStorage.setItem('access_token', authToken);
            showMainApp();
        } else {
            showError('Connection failed. Using offline mode with test credentials.');
        }
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Sign In';
    }
}

// Show Main Application
function showMainApp() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('sidebar').style.display = 'flex';
    document.getElementById('userInfo').textContent = 'User: ' + currentUser;
    showPage('chat');
}

// Page Navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    // Show selected page
    if (pageName === 'chat') {
        document.getElementById('chatPage').classList.add('active');
        document.querySelectorAll('.nav-item')[0].classList.add('active');
    } else if (pageName === 'wiki') {
        document.getElementById('wikiPage').classList.add('active');
        document.querySelectorAll('.nav-item')[1].classList.add('active');
        loadWikiArticles();
    } else if (pageName === 'database') {
        document.getElementById('databasePage').classList.add('active');
        document.querySelectorAll('.nav-item')[2].classList.add('active');
    }
}

// Logout Handler
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('access_token');
        authToken = null;
        currentUser = null;
        sessionId = null;
        
        // Reset to login page
        document.getElementById('sidebar').style.display = 'none';
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById('loginPage').classList.add('active');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        
        // Clear messages
        document.getElementById('messagesContainer').innerHTML = `
            <div class="message bot">
                <div class="message-content">Hello! I am your enterprise AI assistant. How can I help you today?</div>
                <div class="message-time">${getCurrentTime()}</div>
            </div>
        `;
    }
}

// Send Chat Message
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    showTypingIndicator();

    try {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken && !authToken.startsWith('test-token')) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                user_id: currentUser
            })
        });

        hideTypingIndicator();

        if (response.ok) {
            const data = await response.json();
            addMessage(data.response, 'bot', data.wiki_entry_id);
            if (data.session_id) {
                sessionId = data.session_id;
            }
        } else {
            const error = await response.json();
            addMessage(`Error: ${error.error?.message || 'Request failed'}`, 'bot');
        }
    } catch (error) {
        console.error('Send message error:', error);
        hideTypingIndicator();
        addMessage('Sorry, a network error occurred. Please try again.', 'bot');
    }
}

// Add Message to Chat
function addMessage(text, sender, wikiEntryId = null) {
    const container = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Create time element (displayed at top-left of message)
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    // Create content element
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    // Append time first, then content
    messageDiv.appendChild(timeDiv);
    messageDiv.appendChild(contentDiv);
    
    // Add feedback buttons for bot messages (below the content)
    if (sender === 'bot' && wikiEntryId) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-buttons';
        
        const likeBtn = document.createElement('button');
        likeBtn.className = 'feedback-btn like';
        likeBtn.innerHTML = '👍';
        likeBtn.title = 'Helpful';
        likeBtn.onclick = () => submitFeedback(wikiEntryId, true, likeBtn, dislikeBtn, feedbackDiv);
        
        const dislikeBtn = document.createElement('button');
        dislikeBtn.className = 'feedback-btn dislike';
        dislikeBtn.innerHTML = '👎';
        dislikeBtn.title = 'Not Helpful';
        dislikeBtn.onclick = () => submitFeedback(wikiEntryId, false, dislikeBtn, likeBtn, feedbackDiv);
        
        feedbackDiv.appendChild(likeBtn);
        feedbackDiv.appendChild(dislikeBtn);
        messageDiv.appendChild(feedbackDiv);
        
        // Store reference for this message
        messageFeedbackMap.set(messageDiv, { wikiEntryId, likeBtn, dislikeBtn });
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// Submit Feedback for Wiki Article
async function submitFeedback(wikiEntryId, isPositive, clickedBtn, otherBtn, feedbackDiv) {
    // Check if already submitted feedback for this message
    const messageId = Array.from(messageFeedbackMap.entries())
        .find(([_, data]) => data.wikiEntryId === wikiEntryId && 
                           (data.likeBtn === clickedBtn || data.dislikeBtn === clickedBtn))?.[0];
    
    if (messageId && messageFeedbackMap.get(messageId)?.submitted) {
        console.log('Feedback already submitted for this entry');
        return;
    }
    
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken && !authToken.startsWith('test-token')) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/wiki/feedback`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                entry_id: wikiEntryId,
                is_positive: isPositive,
                comment: null  // Optional comment can be added later
            })
        });

        if (response.ok) {
            const data = await response.json();
            
            // Update UI to show feedback was submitted
            clickedBtn.classList.add(isPositive ? 'selected-like' : 'selected-dislike');
            otherBtn.disabled = true;
            otherBtn.style.opacity = '0.5';
            otherBtn.style.cursor = 'not-allowed';
            
            // Add status message
            const statusSpan = document.createElement('span');
            statusSpan.className = 'feedback-status';
            statusSpan.textContent = isPositive ? '✓ Thanks for your feedback!' : '✓ Thanks, we\'ll improve this!';
            feedbackDiv.appendChild(statusSpan);
            
            // Mark as submitted
            if (messageId) {
                messageFeedbackMap.get(messageId).submitted = true;
            }
            
            console.log('Feedback submitted successfully:', data);
        } else {
            const error = await response.json();
            console.error('Feedback submission failed:', error);
            alert('Failed to submit feedback. Please try again.');
        }
    } catch (error) {
        console.error('Submit feedback error:', error);
        alert('Network error. Please check your connection and try again.');
    }
}

// Show/Hide Typing Indicator
function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'block';
    document.getElementById('sendBtn').disabled = true;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
    document.getElementById('sendBtn').disabled = false;
}

// Handle Enter Key
function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

// Load Wiki Articles
async function loadWikiArticles() {
    const wikiContent = document.getElementById('wikiContent');
    wikiContent.innerHTML = '<div class="empty-state"><h3>Loading...</h3></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/wiki/articles`);
        
        if (response.ok) {
            const articles = await response.json();
            
            if (articles.length === 0) {
                wikiContent.innerHTML = `
                    <div class="empty-state">
                        <h3>No articles found</h3>
                        <p>Click "Add Article" to create your first wiki entry</p>
                    </div>
                `;
                return;
            }

            let html = '';
            articles.forEach(article => {
                const confidencePercent = (article.confidence * 100).toFixed(0);
                const confidenceClass = article.confidence >= 0.9 ? 'confidence-high' : 
                                       article.confidence >= 0.7 ? 'confidence-medium' : 'confidence-low';
                
                // Feedback statistics
                const positiveFeedback = article.positive_feedback || 0;
                const negativeFeedback = article.negative_feedback || 0;
                const totalFeedback = positiveFeedback + negativeFeedback;
                
                html += `
                    <div class="wiki-article">
                        <div class="article-header">
                            <h3>${article.title || article.entry_id}</h3>
                            <button class="btn-view" onclick='viewArticle(${JSON.stringify(article).replace(/'/g, "&#39;")})'>👁️ View</button>
                        </div>
                        <p>${article.summary || 'No summary available'}</p>
                        <div class="wiki-meta">
                            <span>Type: ${article.type || 'N/A'}</span>
                            <span>Version: ${article.version || '1'}</span>
                            <span class="preview-confidence ${confidenceClass}">Confidence: ${confidencePercent}%</span>
                        </div>
                        <div class="wiki-feedback-stats" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e0e0e0; display: flex; gap: 15px; font-size: 12px;">
                            <span style="color: #27ae60;">👍 Helpful: ${positiveFeedback}</span>
                            <span style="color: #e74c3c;">👎 Not Helpful: ${negativeFeedback}</span>
                            <span style="color: #7f8c8d;">Total Feedback: ${totalFeedback}</span>
                        </div>
                    </div>
                `;
            });
            wikiContent.innerHTML = html;
        } else {
            // Mock data for demonstration
            wikiContent.innerHTML = getMockWikiArticles();
        }
    } catch (error) {
        console.error('Load wiki error:', error);
        wikiContent.innerHTML = getMockWikiArticles();
    }
}

// Get Mock Wiki Articles
function getMockWikiArticles() {
    return `
        <div class="wiki-article">
            <h3>Getting Started Guide</h3>
            <p>This guide helps you understand the basic features of the enterprise chatbot platform.</p>
            <div class="wiki-meta">
                <span>Type: guide</span>
                <span>Version: 1</span>
                <span>Confidence: 95%</span>
            </div>
        </div>
        <div class="wiki-article">
            <h3>API Authentication</h3>
            <p>Learn how to authenticate with the API using JWT tokens or API keys.</p>
            <div class="wiki-meta">
                <span>Type: technical</span>
                <span>Version: 2</span>
                <span>Confidence: 98%</span>
            </div>
        </div>
        <div class="wiki-article">
            <h3>Troubleshooting Common Issues</h3>
            <p>Solutions for frequently encountered problems and error messages.</p>
            <div class="wiki-meta">
                <span>Type: troubleshooting</span>
                <span>Version: 1</span>
                <span>Confidence: 92%</span>
            </div>
        </div>
    `;
}

// Refresh Wiki
function refreshWiki() {
    loadWikiArticles();
}

// Wiki Modal Functions
function showAddWikiModal() {
    document.getElementById('addWikiModal').style.display = 'flex';
    // Reset form
    document.getElementById('addWikiForm').reset();
    document.getElementById('compilationResult').style.display = 'none';
    document.getElementById('compileBtn').disabled = false;
    document.getElementById('compileBtnText').textContent = '🤖 Compile with LLM';
}

function closeAddWikiModal() {
    document.getElementById('addWikiModal').style.display = 'none';
    document.getElementById('addWikiForm').reset();
    document.getElementById('compilationResult').style.display = 'none';
}

// View Article Modal
function viewArticle(article) {
    const modal = document.getElementById('viewWikiModal');
    const titleEl = document.getElementById('viewArticleTitle');
    const contentEl = document.getElementById('viewArticleContent');
    
    titleEl.textContent = article.title || article.entry_id;
    
    const confidencePercent = (article.confidence * 100).toFixed(0);
    const confidenceClass = article.confidence >= 0.9 ? 'confidence-high' : 
                           article.confidence >= 0.7 ? 'confidence-medium' : 'confidence-low';
    
    contentEl.innerHTML = `
        <div class="article-detail">
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Entry ID</div>
                    <div class="meta-value">${article.entry_id}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Type</div>
                    <div class="meta-value">${article.type || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Version</div>
                    <div class="meta-value">${article.version || '1'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Confidence</div>
                    <div class="meta-value"><span class="preview-confidence ${confidenceClass}">${confidencePercent}%</span></div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Status</div>
                    <div class="meta-value">${article.status || 'active'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Created</div>
                    <div class="meta-value">${article.created_at ? new Date(article.created_at).toLocaleString() : 'N/A'}</div>
                </div>
            </div>
            
            <h3>Summary</h3>
            <p>${article.summary || 'No summary available'}</p>
            
            ${article.content ? `
            <h3>Full Content</h3>
            <div class="content-text">${article.content}</div>
            ` : ''}
            
            ${article.tags && article.tags.length > 0 ? `
            <h3>Tags</h3>
            <div class="preview-tags">
                ${article.tags.map(tag => `<span class="preview-tag">${tag}</span>`).join('')}
            </div>
            ` : ''}
            
            ${article.related_ids && article.related_ids.length > 0 ? `
            <h3>Related Articles</h3>
            <div style="color: #555;">
                ${article.related_ids.map(rel => `<div>• ${rel.entry_id} (${rel.relation})</div>`).join('')}
            </div>
            ` : ''}
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeViewWikiModal() {
    document.getElementById('viewWikiModal').style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    const addModal = document.getElementById('addWikiModal');
    const viewModal = document.getElementById('viewWikiModal');
    if (event.target === addModal) {
        closeAddWikiModal();
    }
    if (event.target === viewModal) {
        closeViewWikiModal();
    }
}

// Handle Add Wiki Form Submission with LLM Compiler
let compiledArticleData = null;

document.addEventListener('DOMContentLoaded', function() {
    const addWikiForm = document.getElementById('addWikiForm');
    if (addWikiForm) {
        addWikiForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const rawContent = document.getElementById('wikiRawContent').value.trim();
            const sourceUrl = document.getElementById('wikiSourceUrl').value.trim();
            const sourceType = document.getElementById('wikiSourceType').value;
            const suggestedCategory = document.getElementById('wikiSuggestedCategory').value;
            
            if (!rawContent) {
                alert('Please enter raw document content');
                return;
            }
            
            // Disable button and show loading
            const compileBtn = document.getElementById('compileBtn');
            const compileBtnText = document.getElementById('compileBtnText');
            compileBtn.disabled = true;
            compileBtnText.textContent = '⏳ Compiling...';
            
            try {
                // Call LLM Wiki Compiler API
                const response = await fetch(`${API_BASE_URL}/api/v1/wiki/compile`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        raw_content: rawContent,
                        source_url: sourceUrl || null,
                        source_type: sourceType,
                        suggested_category: suggestedCategory || null
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Compilation failed: ${response.statusText}`);
                }
                
                const result = await response.json();
                compiledArticleData = result.article;
                
                // Display preview
                displayCompilationPreview(compiledArticleData);
                
            } catch (error) {
                console.error('Compilation error:', error);
                alert('Error compiling article: ' + error.message + '\n\nNote: Backend API endpoint may not be implemented yet.');
                
                // For demo purposes, create a mock compiled article
                compiledArticleData = createMockCompiledArticle(rawContent, sourceUrl, sourceType);
                displayCompilationPreview(compiledArticleData);
            } finally {
                compileBtn.disabled = false;
                compileBtnText.textContent = '🤖 Compile with LLM';
            }
        });
    }
});

function displayCompilationPreview(article) {
    const resultDiv = document.getElementById('compilationResult');
    const previewDiv = document.getElementById('previewContent');
    
    const confidencePercent = (article.confidence * 100).toFixed(0);
    const confidenceClass = article.confidence >= 0.9 ? 'confidence-high' : 
                           article.confidence >= 0.7 ? 'confidence-medium' : 'confidence-low';
    
    previewDiv.innerHTML = `
        <div class="preview-section">
            <div class="preview-field">
                <label>Entry ID:</label>
                <div>${article.entry_id}</div>
            </div>
            <div class="preview-field">
                <label>Title:</label>
                <div><strong>${article.title}</strong></div>
            </div>
            <div class="preview-field">
                <label>Type:</label>
                <div>${article.type}</div>
            </div>
            <div class="preview-field">
                <label>Confidence:</label>
                <div><span class="preview-confidence ${confidenceClass}">${confidencePercent}%</span></div>
            </div>
            <div class="preview-field">
                <label>Summary:</label>
                <div>${article.summary}</div>
            </div>
            ${article.tags && article.tags.length > 0 ? `
            <div class="preview-field">
                <label>Tags:</label>
                <div class="preview-tags">
                    ${article.tags.map(tag => `<span class="preview-tag">${tag}</span>`).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

function resetCompilation() {
    document.getElementById('compilationResult').style.display = 'none';
    compiledArticleData = null;
}

async function saveCompiledArticle() {
    if (!compiledArticleData) {
        alert('No compiled article to save');
        return;
    }
    
    const saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.textContent = '💾 Saving...';
    
    try {
        // Try to save via API
        const response = await fetch(`${API_BASE_URL}/api/v1/wiki/articles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(compiledArticleData)
        });
        
        if (response.ok) {
            alert('✅ Article saved successfully!');
            closeAddWikiModal();
            loadWikiArticles(); // Refresh the list
        } else {
            throw new Error('Save failed');
        }
    } catch (error) {
        console.error('Save error:', error);
        // For demo: show the data that would be saved
        alert('⚠️ Backend API not available.\n\nArticle prepared for saving:\n\n' + 
              JSON.stringify(compiledArticleData, null, 2) +
              '\n\nIn production, this would be saved to the database.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save to Database';
    }
}

function createMockCompiledArticle(rawContent, sourceUrl, sourceType) {
    // Generate a simple mock compilation for demo purposes
    const lines = rawContent.split('\n').filter(line => line.trim());
    const title = lines[0] || 'Untitled Article';
    const summary = lines.slice(1, 4).join(' ').substring(0, 200) + '...';
    
    // Auto-detect type based on content
    let type = 'concept';
    const lowerContent = rawContent.toLowerCase();
    if (lowerContent.includes('policy') || lowerContent.includes('rule')) type = 'rule';
    else if (lowerContent.includes('process') || lowerContent.includes('procedure') || lowerContent.includes('step')) type = 'process';
    else if (lowerContent.includes('how to') || lowerContent.includes('guide')) type = 'guide';
    else if (lowerContent.includes('formula') || lowerContent.includes('calculate')) type = 'formula';
    else if (lowerContent.includes('faq') || lowerContent.includes('question')) type = 'qa';
    
    // Generate entry_id
    const typePrefix = {
        'concept': 'conc',
        'rule': 'rule',
        'process': 'proc',
        'guide': 'guid',
        'formula': 'form',
        'qa': 'qa'
    };
    const prefix = typePrefix[type] || 'doc';
    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '_').substring(0, 30);
    const entryId = `${prefix}_${slug}`;
    
    return {
        entry_id: entryId,
        title: title,
        type: type,
        version: 1,
        summary: summary,
        content: rawContent,
        tags: ['auto-generated', type],
        sources: sourceUrl ? [{
            source_id: 'src_' + Date.now(),
            url: sourceUrl,
            type: sourceType
        }] : [],
        confidence: 0.85,
        status: 'draft'
    };
}

// Load Database Table Data
async function loadTableData() {
    const tableSelect = document.getElementById('tableSelect');
    const tableName = tableSelect.value;
    const dataTable = document.getElementById('dataTable');

    if (!tableName) {
        dataTable.innerHTML = '<div class="empty-state"><h3>Select a table to view data</h3></div>';
        return;
    }

    dataTable.innerHTML = '<div class="empty-state"><h3>Loading...</h3></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/database/${tableName}`);
        
        if (response.ok) {
            const data = await response.json();
            renderDataTable(data);
        } else {
            // Show mock data
            renderMockTableData(tableName);
        }
    } catch (error) {
        console.error('Load table error:', error);
        renderMockTableData(tableName);
    }
}

// Render Data Table
function renderDataTable(data) {
    if (!data || data.length === 0) {
        document.getElementById('dataTable').innerHTML = '<div class="empty-state"><h3>No data found</h3></div>';
        return;
    }

    const columns = Object.keys(data[0]);
    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            if (typeof value === 'object') {
                value = JSON.stringify(value);
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    document.getElementById('dataTable').innerHTML = html;
}

// Render Mock Table Data
function renderMockTableData(tableName) {
    let html = '';
    
    if (tableName === 'wiki_entries') {
        html = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Version</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>guide_001</td>
                        <td>Getting Started Guide</td>
                        <td>guide</td>
                        <td>1</td>
                        <td><span class="status-badge status-active">Active</span></td>
                    </tr>
                    <tr>
                        <td>tech_002</td>
                        <td>API Authentication</td>
                        <td>technical</td>
                        <td>2</td>
                        <td><span class="status-badge status-active">Active</span></td>
                    </tr>
                </tbody>
            </table>
        `;
    } else if (tableName === 'api_keys') {
        html = `
            <table>
                <thead>
                    <tr>
                        <th>Key ID</th>
                        <th>Name</th>
                        <th>Owner</th>
                        <th>Status</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>key_abc123</td>
                        <td>Production API Key</td>
                        <td>admin</td>
                        <td><span class="status-badge status-active">Active</span></td>
                        <td>2026-04-15</td>
                    </tr>
                    <tr>
                        <td>key_def456</td>
                        <td>Test API Key</td>
                        <td>testuser</td>
                        <td><span class="status-badge status-inactive">Inactive</span></td>
                        <td>2026-04-10</td>
                    </tr>
                </tbody>
            </table>
        `;
    } else if (tableName === 'chat_sessions') {
        html = `
            <table>
                <thead>
                    <tr>
                        <th>Session ID</th>
                        <th>User</th>
                        <th>Messages</th>
                        <th>Last Active</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>session-1234567890</td>
                        <td>admin</td>
                        <td>15</td>
                        <td>2026-04-20 16:30</td>
                    </tr>
                    <tr>
                        <td>session-0987654321</td>
                        <td>testuser</td>
                        <td>8</td>
                        <td>2026-04-20 15:45</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    document.getElementById('dataTable').innerHTML = html;
}

// Utility Functions
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function showError(message) {
    const errorDiv = document.getElementById('errorMsg');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}

// Check connection status periodically
setInterval(async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`);
        if (response.ok) {
            console.log('Backend connected');
        }
    } catch (error) {
        console.warn('Backend disconnected');
    }
}, 10000);

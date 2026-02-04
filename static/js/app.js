// CyberLab - Frontend Application Logic

// ==================== STATE MANAGEMENT ====================

let currentUser = null;
let currentChallengeId = null;
let isLogin = true;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initMatrixBackground();
    checkAuthStatus();
    setupEventListeners();
});

// ==================== AUTHENTICATION ====================

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/current-user');
        const data = await response.json();
        
        if (data.authenticated) {
            currentUser = data.user;
            showLoggedInUI();
            loadDashboard();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

function showAuth(mode) {
    isLogin = (mode === 'login');
    
    document.getElementById('authTitle').textContent = isLogin ? 'SYSTEM_ACCESS' : 'NEW_USER_REGISTRATION';
    document.getElementById('emailGroup').style.display = isLogin ? 'none' : 'block';
    document.getElementById('authSubmitText').textContent = isLogin ? 'AUTHENTICATE' : 'REGISTER';
    
    const switchText = document.getElementById('authSwitchText');
    const switchLink = document.getElementById('authSwitchLink');
    
    if (isLogin) {
        switchText.textContent = 'New user?';
        switchLink.textContent = 'CREATE_ACCOUNT';
        switchLink.onclick = () => showAuth('register');
    } else {
        switchText.textContent = 'Already registered?';
        switchLink.textContent = 'LOGIN_HERE';
        switchLink.onclick = () => showAuth('login');
    }
    
    document.getElementById('authError').style.display = 'none';
    document.getElementById('authModal').style.display = 'block';
}

function closeAuth() {
    document.getElementById('authModal').style.display = 'none';
    document.getElementById('authForm').reset();
}

async function handleAuth(event) {
    event.preventDefault();
    
    const username = document.getElementById('authUsername').value.trim();
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    
    const endpoint = isLogin ? '/api/login' : '/api/register';
    const data = isLogin ? { username, password } : { username, email, password };
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUser = { username: result.username };
            showLoggedInUI();
            closeAuth();
            loadDashboard();
            showNotification(isLogin ? 'ACCESS_GRANTED' : 'ACCOUNT_CREATED', 'success');
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError('CONNECTION_FAILED');
    }
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUser = null;
        showLoggedOutUI();
        showNotification('DISCONNECTED', 'success');
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

function showLoggedInUI() {
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('userControls').style.display = 'flex';
    document.getElementById('userName').textContent = `[${currentUser.username}]`;
    document.getElementById('mainNav').style.display = 'flex';
    document.getElementById('landing').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
}

function showLoggedOutUI() {
    document.getElementById('authButtons').style.display = 'flex';
    document.getElementById('userControls').style.display = 'none';
    document.getElementById('mainNav').style.display = 'none';
    document.getElementById('landing').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    
    // Hide all other sections
    ['challenges', 'leaderboard', 'profile'].forEach(section => {
        document.getElementById(section).style.display = 'none';
    });
}

function showError(message) {
    const errorDiv = document.getElementById('authError');
    errorDiv.textContent = `[ERROR] ${message}`;
    errorDiv.style.display = 'block';
}

// ==================== NAVIGATION ====================

function setupEventListeners() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.style.display = 'block';
        
        // Add active class to nav link
        const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeLink) activeLink.classList.add('active');
        
        // Load data for the section
        switch(sectionName) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'challenges':
                loadChallenges();
                break;
            case 'leaderboard':
                loadLeaderboard();
                break;
            case 'profile':
                loadProfile();
                break;
        }
    }
}

// ==================== DASHBOARD ====================

async function loadDashboard() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            updateDashboardStats(data);
            updateActiveContainers(data.active_containers);
            updateAchievements(data.achievements);
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function updateDashboardStats(data) {
    document.getElementById('totalPoints').textContent = data.user.total_points || 0;
    document.getElementById('completedCount').textContent = data.progress.completed || 0;
    document.getElementById('inProgressCount').textContent = data.progress.in_progress || 0;
    document.getElementById('skillLevel').textContent = data.user.skill_level || 1;
    
    // Update progress bar
    const totalChallenges = 15; // Total available challenges
    const percentage = ((data.progress.completed || 0) / totalChallenges) * 100;
    document.querySelector('.progress-fill').style.width = `${percentage}%`;
}

function updateActiveContainers(containers) {
    const panel = document.getElementById('activeContainersPanel');
    const list = document.getElementById('activeContainersList');
    
    if (containers && containers.length > 0) {
        panel.style.display = 'block';
        list.innerHTML = containers.map(c => `
            <div class="container-item">
                <div><strong>${c.challenge_name}</strong></div>
                <div>Host: <code>${c.host}:${c.port}</code></div>
                <div>Started: ${new Date(c.started_at).toLocaleTimeString()}</div>
                <button class="cyber-btn danger" onclick="stopContainer(${c.challenge_id})">
                    <span class="btn-glitch">STOP</span>
                </button>
            </div>
        `).join('');
    } else {
        panel.style.display = 'none';
    }
}

function updateAchievements(achievements) {
    const panel = document.getElementById('achievementsPanel');
    const list = document.getElementById('achievementsList');
    
    if (achievements && achievements.length > 0) {
        panel.style.display = 'block';
        list.innerHTML = achievements.map(a => `
            <div class="achievement-badge">
                <div class="achievement-icon">${a.badge_icon}</div>
                <div class="achievement-name">${a.name}</div>
            </div>
        `).join('');
    } else {
        panel.style.display = 'none';
    }
}

// ==================== CHALLENGES ====================

async function loadChallenges() {
    try {
        const response = await fetch('/api/challenges');
        const data = await response.json();
        
        if (data.success) {
            displayChallenges(data.challenges);
            populateCategoryFilter(data.categories);
        }
    } catch (error) {
        console.error('Failed to load challenges:', error);
    }
}

function populateCategoryFilter(categories) {
    const select = document.getElementById('categoryFilter');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="all">ALL_CATEGORIES</option>';
    Object.keys(categories).forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat.toUpperCase();
        select.appendChild(option);
    });
    
    select.value = currentValue;
}

function displayChallenges(challenges) {
    const grid = document.getElementById('challengesGrid');
    const categoryFilter = document.getElementById('categoryFilter').value;
    const difficultyFilter = document.getElementById('difficultyFilter').value;
    
    const filtered = challenges.filter(c => {
        const catMatch = categoryFilter === 'all' || c.category === categoryFilter;
        const diffMatch = difficultyFilter === 'all' || c.difficulty.toString() === difficultyFilter;
        return catMatch && diffMatch;
    });
    
    grid.innerHTML = filtered.map(c => `
        <div class="challenge-card" onclick="openChallenge(${c.id})">
            <div class="challenge-header">
                <div>
                    <div class="challenge-title">${c.name}</div>
                    <div class="challenge-category">[${c.category}]</div>
                </div>
                <div class="difficulty-badge difficulty-${c.difficulty}">
                    ${c.difficulty === 1 ? 'BEGINNER' : c.difficulty === 2 ? 'INTERMEDIATE' : 'ADVANCED'}
                </div>
            </div>
            <div class="challenge-description">${c.description}</div>
            <div class="challenge-footer">
                <div class="challenge-points">⬣ ${c.points} PTS</div>
                <div class="status-badge status-${c.status.replace('_', '-')}">
                    ${c.status.toUpperCase().replace('_', ' ')}
                </div>
            </div>
        </div>
    `).join('');
}

// Filter event listeners
document.getElementById('categoryFilter')?.addEventListener('change', loadChallenges);
document.getElementById('difficultyFilter')?.addEventListener('change', loadChallenges);

// ==================== CHALLENGE MODAL ====================

async function openChallenge(challengeId) {
    currentChallengeId = challengeId;
    
    try {
        const response = await fetch(`/api/challenge/${challengeId}`);
        const data = await response.json();
        
        if (data.success) {
            displayChallengeModal(data.challenge);
            
            // Automatically start the challenge (and container if applicable)
            if (data.challenge.status !== 'completed') {
                startChallengeAutomatically(challengeId);
            }
        }
    } catch (error) {
        console.error('Failed to load challenge:', error);
    }
}

async function startChallengeAutomatically(challengeId) {
    try {
        const response = await fetch(`/api/challenge/${challengeId}/start`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success && data.container) {
            updateContainerStatus(data);
            if (data.auto_deployed) {
                showNotification('CONTAINER_AUTO_DEPLOYED', 'success');
            }
        }
    } catch (error) {
        console.error('Failed to auto-start challenge:', error);
    }
}

function updateContainerStatus(data) {
    const statusDiv = document.getElementById('containerStatus');
    if (statusDiv && data.container) {
        statusDiv.innerHTML = `
            <div class="container-info">
                <p><strong>✅ CONTAINER_ACTIVE</strong></p>
                <p>Access: <a href="${data.container.url}" target="_blank" class="cyber-link">${data.container.url}</a></p>
                <p>Host: <code>${data.container.host}</code></p>
                <p>Port: <code>${data.container.port}</code></p>
                ${data.auto_deployed ? '<p class="success-message">Auto-deployed on challenge start!</p>' : ''}
            </div>
        `;
    }
}

function displayChallengeModal(challenge) {
    const detailsDiv = document.getElementById('challengeDetails');
    
    detailsDiv.innerHTML = `
        <h2 class="modal-title">${challenge.name}</h2>
        <div class="challenge-meta">
            <span class="difficulty-badge difficulty-${challenge.difficulty}">
                ${challenge.difficulty === 1 ? 'BEGINNER' : challenge.difficulty === 2 ? 'INTERMEDIATE' : 'ADVANCED'}
            </span>
            <span class="challenge-category">[${challenge.category}]</span>
            <span class="challenge-points">⬣ ${challenge.points} PTS</span>
        </div>
        
        <div class="challenge-section">
            <h3>MISSION_BRIEFING</h3>
            <p>${challenge.description}</p>
        </div>
        
        ${challenge.docker_image ? `
            <div class="challenge-section">
                <h3>SANDBOX_ENVIRONMENT</h3>
                <button class="cyber-btn" onclick="startChallengeContainer()">
                    <span class="btn-glitch">DEPLOY_CONTAINER</span>
                </button>
                <div id="containerStatus"></div>
            </div>
        ` : ''}
        
        <div class="challenge-section">
            <h3>SUBMIT_FLAG</h3>
            <div class="form-group">
                <input type="text" id="flagInput" class="cyber-input" placeholder="CTF{...}">
            </div>
            <button class="cyber-btn" onclick="submitFlag()">
                <span class="btn-glitch">VALIDATE</span>
            </button>
            <div id="flagResult"></div>
        </div>
        
        <div class="challenge-section">
            <h3>AI_ASSISTANCE</h3>
            <div class="form-group">
                <textarea id="hintContext" class="cyber-input" rows="3" 
                    placeholder="Describe what you've tried..."></textarea>
            </div>
            <button class="cyber-btn secondary" onclick="requestHint()">
                <span class="btn-glitch">REQUEST_HINT [${challenge.hints_used || 0} USED]</span>
            </button>
            <div id="hintDisplay"></div>
        </div>
    `;
    
    document.getElementById('challengeModal').style.display = 'block';
}

function closeChallengeModal() {
    document.getElementById('challengeModal').style.display = 'none';
    currentChallengeId = null;
}

async function startChallengeContainer() {
    if (!currentChallengeId) return;
    
    try {
        const response = await fetch(`/api/challenge/${currentChallengeId}/start`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            const statusDiv = document.getElementById('containerStatus');
            
            if (data.container) {
                statusDiv.innerHTML = `
                    <div class="container-info">
                        <p><strong>CONTAINER_ACTIVE</strong></p>
                        <p>URL: <a href="${data.container.url}" target="_blank">${data.container.url}</a></p>
                        <p>Host: ${data.container.host}</p>
                        <p>Port: ${data.container.port}</p>
                    </div>
                `;
                showNotification('CONTAINER_DEPLOYED', 'success');
            } else if (data.warning) {
                statusDiv.innerHTML = `<div class="error-message">${data.warning}</div>`;
            }
        }
    } catch (error) {
        console.error('Failed to start container:', error);
        showNotification('CONTAINER_DEPLOYMENT_FAILED', 'error');
    }
}

async function submitFlag() {
    if (!currentChallengeId) return;
    
    const flag = document.getElementById('flagInput').value.trim();
    if (!flag) return;
    
    try {
        const response = await fetch(`/api/challenge/${currentChallengeId}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ flag })
        });
        const data = await response.json();
        
        const resultDiv = document.getElementById('flagResult');
        
        if (data.correct) {
            resultDiv.innerHTML = `<div class="success-message">${data.message}</div>`;
            showNotification(`+${data.points} POINTS`, 'success');
            setTimeout(() => {
                closeChallengeModal();
                loadDashboard();
                loadChallenges();
            }, 2000);
        } else {
            resultDiv.innerHTML = `<div class="error-message">${data.message}</div>`;
        }
    } catch (error) {
        console.error('Flag submission failed:', error);
    }
}

async function requestHint() {
    if (!currentChallengeId) return;
    
    const context = document.getElementById('hintContext').value.trim();
    
    try {
        const response = await fetch(`/api/challenge/${currentChallengeId}/hint`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context })
        });
        const data = await response.json();
        
        if (data.success) {
            const hintDiv = document.getElementById('hintDisplay');
            hintDiv.innerHTML = `
                <div class="hint-box">
                    <div class="hint-header">🤖 AI_HINT [${data.hints_used}]</div>
                    <div class="hint-content">${data.hint}</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Hint request failed:', error);
    }
}

async function stopContainer(challengeId) {
    try {
        const response = await fetch(`/api/challenge/${challengeId}/container/stop`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showNotification('CONTAINER_STOPPED', 'success');
            loadDashboard();
        }
    } catch (error) {
        console.error('Failed to stop container:', error);
    }
}

// ==================== LEADERBOARD ====================

async function loadLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard');
        const data = await response.json();
        
        if (data.success) {
            displayLeaderboard(data.leaderboard);
        }
    } catch (error) {
        console.error('Failed to load leaderboard:', error);
    }
}

function displayLeaderboard(leaders) {
    const list = document.getElementById('leaderboardList');
    
    list.innerHTML = leaders.map((leader, index) => `
        <div class="leaderboard-item">
            <div class="leader-rank">#${index + 1}</div>
            <div class="leader-name">${leader.username}</div>
            <div class="leader-points">⬣ ${leader.total_points}</div>
            <div class="leader-challenges">${leader.challenges_completed} solved</div>
        </div>
    `).join('');
}

// ==================== LEARNING PATH ====================

async function loadLearningPath() {
    try {
        const response = await fetch('/api/learning-path');
        const data = await response.json();
        
        if (data.success) {
            showNotification('AI_LEARNING_PATH_GENERATED', 'success');
            // Display learning path (could be a modal or section)
            console.log('Learning path:', data.path);
        }
    } catch (error) {
        console.error('Failed to load learning path:', error);
    }
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.className = `notification ${type}`;
    notification.textContent = `[${type.toUpperCase()}] ${message}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// ==================== MATRIX BACKGROUND ====================

function initMatrixBackground() {
    const canvas = document.getElementById('matrix-bg');
    const ctx = canvas.getContext('2d');
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);
    
    function draw() {
        ctx.fillStyle = 'rgba(0, 8, 20, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff41';
        ctx.font = fontSize + 'px monospace';
        
        for (let i = 0; i < drops.length; i++) {
            const text = chars[Math.floor(Math.random() * chars.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 33);
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ==================== PROFILE (Stub) ====================

async function loadProfile() {
    // Load user profile data
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            displayProfile(data);
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
    }
}

function displayProfile(data) {
    const profileData = document.getElementById('profileData');
    profileData.innerHTML = `
        <p><strong>Username:</strong> ${data.user.username}</p>
        <p><strong>Email:</strong> ${data.user.email}</p>
        <p><strong>Joined:</strong> ${new Date(data.user.created_at).toLocaleDateString()}</p>
        <p><strong>Total Points:</strong> ⬣ ${data.user.total_points}</p>
        <p><strong>Skill Level:</strong> ${data.user.skill_level}</p>
    `;
    
    // Display category breakdown
    const categoryChart = document.getElementById('categoryChart');
    categoryChart.innerHTML = data.categories.map(cat => `
        <div class="category-item">
            <div class="category-name">${cat.category}</div>
            <div class="category-count">${cat.count} challenges</div>
            <div class="category-points">⬣ ${cat.points} points</div>
        </div>
    `).join('');
}
"""
AI-Enhanced Ethical Hacking Lab Simulator
Main Flask Application with DeepSeek AI Integration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import secrets
import os

from database import init_db, get_db
from ai_engine import AIEngine
from docker_manager import DockerManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Initialize components
db_path = 'cyberlab.db'
init_db(db_path)
ai_engine = AIEngine()
docker_manager = DockerManager()

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        conn = get_db(db_path)
        c = conn.cursor()
        c.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/challenges')
@login_required
def challenges_page():
    """Challenges page"""
    return render_template('challenges.html')

# ==================== AUTH API ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not all([username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Check if username or email exists
    c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    
    try:
        password_hash = generate_password_hash(password)
        c.execute('''INSERT INTO users (username, email, password_hash, skill_level, total_points) 
                     VALUES (?, ?, ?, 1, 0)''',
                 (username, email, password_hash))
        conn.commit()
        user_id = c.lastrowid
        
        # Create initial user stats
        c.execute('''INSERT INTO user_stats (user_id, challenges_completed, hints_used, total_time_spent)
                     VALUES (?, 0, 0, 0)''', (user_id,))
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({
            'success': True, 
            'user_id': user_id,
            'username': username
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']
        
        return jsonify({
            'success': True, 
            'username': username,
            'is_admin': user['is_admin']
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute('''SELECT id, username, email, skill_level, total_points, is_admin, created_at 
                 FROM users WHERE id = ?''', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return jsonify({'authenticated': False})
    
    return jsonify({
        'authenticated': True,
        'user': dict(user)
    })

# ==================== CHALLENGES API ====================

@app.route('/api/challenges')
@login_required
def get_challenges():
    """Get all challenges with user progress"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            c.*,
            COALESCE(up.status, 'not_started') as status,
            COALESCE(up.attempts, 0) as attempts,
            COALESCE(up.hints_used, 0) as hints_used,
            COALESCE(up.points_earned, 0) as points_earned,
            up.completed_at
        FROM challenges c
        LEFT JOIN user_progress up ON c.id = up.challenge_id AND up.user_id = ?
        ORDER BY c.difficulty, c.category, c.name
    ''', (session['user_id'],))
    
    challenges = [dict(row) for row in c.fetchall()]
    
    # Group by category
    categories = {}
    for challenge in challenges:
        cat = challenge['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(challenge)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'challenges': challenges,
        'categories': categories
    })

@app.route('/api/challenge/<int:challenge_id>')
@login_required
def get_challenge(challenge_id):
    """Get specific challenge details"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            c.*,
            COALESCE(up.status, 'not_started') as status,
            COALESCE(up.attempts, 0) as attempts,
            COALESCE(up.hints_used, 0) as hints_used,
            up.started_at,
            up.completed_at
        FROM challenges c
        LEFT JOIN user_progress up ON c.id = up.challenge_id AND up.user_id = ?
        WHERE c.id = ?
    ''', (session['user_id'], challenge_id))
    
    challenge = c.fetchone()
    conn.close()
    
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404
    
    return jsonify({
        'success': True,
        'challenge': dict(challenge)
    })

@app.route('/api/challenge/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    """Start a challenge and automatically launch SHARED container if available"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get challenge info
    c.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,))
    challenge = c.fetchone()
    
    if not challenge:
        conn.close()
        return jsonify({'error': 'Challenge not found'}), 404
    
    # Check if already in progress
    c.execute('''SELECT * FROM user_progress 
                 WHERE user_id = ? AND challenge_id = ?''',
             (session['user_id'], challenge_id))
    progress = c.fetchone()
    
    if not progress:
        # Create new progress entry
        c.execute('''INSERT INTO user_progress 
                    (user_id, challenge_id, status, attempts, hints_used, started_at) 
                    VALUES (?, ?, 'in_progress', 0, 0, ?)''',
                 (session['user_id'], challenge_id, datetime.now().isoformat()))
    else:
        # Update to in_progress if not completed
        if progress['status'] != 'completed':
            c.execute('''UPDATE user_progress 
                        SET status = 'in_progress', started_at = ?
                        WHERE user_id = ? AND challenge_id = ?''',
                     (datetime.now().isoformat(), session['user_id'], challenge_id))
    
    conn.commit()
    
    # AUTOMATICALLY start/connect to SHARED Docker container
    result = {'success': True, 'message': 'Challenge started', 'auto_deployed': False}
    
    if challenge['docker_image']:
        # Check if user already has a session for this challenge
        c.execute('''SELECT * FROM user_sessions 
                    WHERE user_id = ? AND challenge_id = ?''',
                 (session['user_id'], challenge_id))
        existing_session = c.fetchone()
        
        if existing_session:
            # User already has a session, return existing info
            c.execute('''SELECT * FROM active_containers WHERE challenge_id = ?''',
                     (challenge_id,))
            container_info = c.fetchone()
            
            if container_info:
                result['container'] = {
                    'host': container_info['host'],
                    'port': container_info['port'],
                    'session_id': existing_session['session_id'],
                    'url': f"http://{container_info['host']}:{container_info['port']}?session={existing_session['session_id']}"
                }
                result['container_available'] = True
                result['message'] = 'Reconnected to existing session'
        else:
            # Start or connect to shared container
            container_result = docker_manager.start_container(
                session['user_id'], 
                challenge_id,
                challenge['docker_image']
            )
            
            if 'error' in container_result:
                result['warning'] = container_result['error']
                result['container_available'] = False
            else:
                # Check if container entry exists in active_containers
                c.execute('''SELECT * FROM active_containers WHERE challenge_id = ?''',
                         (challenge_id,))
                existing_container = c.fetchone()
                
                if not existing_container:
                    # Create new container entry (first user)
                    c.execute('''INSERT INTO active_containers 
                                (challenge_id, container_id, host, port, started_at, last_accessed)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                             (challenge_id,
                              container_result['container_id'],
                              container_result['host'],
                              container_result['port'],
                              datetime.now().isoformat(),
                              datetime.now().isoformat()))
                else:
                    # Update last accessed time
                    c.execute('''UPDATE active_containers 
                                SET last_accessed = ? 
                                WHERE challenge_id = ?''',
                             (datetime.now().isoformat(), challenge_id))
                
                # Create user session entry
                c.execute('''INSERT OR REPLACE INTO user_sessions 
                            (user_id, challenge_id, session_id, container_id, started_at, last_accessed)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (session['user_id'], challenge_id,
                          container_result['session_id'],
                          container_result['container_id'],
                          datetime.now().isoformat(),
                          datetime.now().isoformat()))
                
                conn.commit()
                
                result['container'] = {
                    'host': container_result['host'],
                    'port': container_result['port'],
                    'session_id': container_result['session_id'],
                    'url': container_result['url'],
                    'shared': container_result.get('shared', False)
                }
                result['container_available'] = True
                result['auto_deployed'] = True
                result['message'] = 'Connected to shared container'
    
    conn.close()
    return jsonify(result)

@app.route('/api/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    """Submit a flag for validation"""
    data = request.get_json()
    flag = data.get('flag', '').strip()
    
    if not flag:
        return jsonify({'error': 'Flag cannot be empty'}), 400
    
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get challenge
    c.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,))
    challenge = c.fetchone()
    
    if not challenge:
        conn.close()
        return jsonify({'error': 'Challenge not found'}), 404
    
    # Get or create progress
    c.execute('''SELECT * FROM user_progress 
                 WHERE user_id = ? AND challenge_id = ?''',
             (session['user_id'], challenge_id))
    progress = c.fetchone()
    
    if not progress:
        c.execute('''INSERT INTO user_progress 
                    (user_id, challenge_id, status, attempts, hints_used, started_at) 
                    VALUES (?, ?, 'in_progress', 0, 0, ?)''',
                 (session['user_id'], challenge_id, datetime.now().isoformat()))
        conn.commit()
    
    # Increment attempts
    c.execute('''UPDATE user_progress 
                SET attempts = attempts + 1 
                WHERE user_id = ? AND challenge_id = ?''',
             (session['user_id'], challenge_id))
    conn.commit()
    
    # Check if flag is correct
    correct = (flag == challenge['flag'])
    
    if correct:
        # Mark as completed
        points = challenge['points']
        c.execute('''UPDATE user_progress 
                    SET status = 'completed', 
                        completed_at = ?,
                        points_earned = ? 
                    WHERE user_id = ? AND challenge_id = ?''',
                 (datetime.now().isoformat(), points, 
                  session['user_id'], challenge_id))
        
        # Update user points and stats
        c.execute('''UPDATE users 
                    SET total_points = total_points + ? 
                    WHERE id = ?''',
                 (points, session['user_id']))
        
        c.execute('''UPDATE user_stats 
                    SET challenges_completed = challenges_completed + 1
                    WHERE user_id = ?''',
                 (session['user_id'],))
        
        conn.commit()
        
        # Stop container if exists
        docker_manager.stop_container(session['user_id'], challenge_id)
        c.execute('''DELETE FROM active_containers 
                    WHERE user_id = ? AND challenge_id = ?''',
                 (session['user_id'], challenge_id))
        conn.commit()
        
        # Check for achievements
        achievements = check_achievements(session['user_id'], c)
        
        conn.close()
        
        return jsonify({
            'correct': True,
            'points': points,
            'message': '🎉 Congratulations! Challenge completed!',
            'new_achievements': achievements
        })
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'correct': False,
        'message': '❌ Incorrect flag. Try again!'
    })

@app.route('/api/challenge/<int:challenge_id>/hint', methods=['POST'])
@login_required
def get_hint(challenge_id):
    """Get an AI-generated hint"""
    data = request.get_json()
    context = data.get('context', '')
    
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get challenge
    c.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,))
    challenge = c.fetchone()
    
    if not challenge:
        conn.close()
        return jsonify({'error': 'Challenge not found'}), 404
    
    # Get user progress
    c.execute('''SELECT * FROM user_progress 
                 WHERE user_id = ? AND challenge_id = ?''',
             (session['user_id'], challenge_id))
    progress = c.fetchone()
    
    attempts = progress['attempts'] if progress else 0
    hints_used = progress['hints_used'] if progress else 0
    
    # Generate hint using AI
    hint = ai_engine.generate_hint(
        challenge=dict(challenge),
        attempts=attempts,
        hints_used=hints_used,
        context=context
    )
    
    # Update hints used
    if progress:
        c.execute('''UPDATE user_progress 
                    SET hints_used = hints_used + 1 
                    WHERE user_id = ? AND challenge_id = ?''',
                 (session['user_id'], challenge_id))
    else:
        c.execute('''INSERT INTO user_progress 
                    (user_id, challenge_id, status, attempts, hints_used, started_at) 
                    VALUES (?, ?, 'in_progress', 0, 1, ?)''',
                 (session['user_id'], challenge_id, datetime.now().isoformat()))
    
    c.execute('''UPDATE user_stats 
                SET hints_used = hints_used + 1
                WHERE user_id = ?''',
             (session['user_id'],))
    
    # Log AI interaction
    c.execute('''INSERT INTO ai_interactions 
                (user_id, challenge_id, interaction_type, user_input, ai_response) 
                VALUES (?, ?, 'hint', ?, ?)''',
             (session['user_id'], challenge_id, context, hint))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'hint': hint,
        'hints_used': hints_used + 1
    })

@app.route('/api/challenge/<int:challenge_id>/container/stop', methods=['POST'])
@login_required
def stop_container(challenge_id):
    """End user's session (container stays running for others)"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Delete user's session
    c.execute('''DELETE FROM user_sessions 
                WHERE user_id = ? AND challenge_id = ?''',
             (session['user_id'], challenge_id))
    
    # Check if any other users are using this container
    c.execute('''SELECT COUNT(*) as count FROM user_sessions 
                WHERE challenge_id = ?''', (challenge_id,))
    other_users = c.fetchone()['count']
    
    if other_users == 0:
        # No other users, safe to stop the container
        c.execute('''DELETE FROM active_containers WHERE challenge_id = ?''',
                 (challenge_id,))
        result = docker_manager.stop_container_admin(challenge_id)
        message = 'Container stopped (last user)'
    else:
        # Other users still connected
        result = docker_manager.stop_container(session['user_id'], challenge_id)
        message = f'Session ended ({other_users} other user(s) still connected)'
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': message,
        'other_users': other_users
    })


# ==================== USER STATS API ====================

@app.route('/api/stats')
@login_required
def get_stats():
    """Get user statistics and dashboard data"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # User info
    c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = dict(c.fetchone())
    
    # User stats
    c.execute('SELECT * FROM user_stats WHERE user_id = ?', (session['user_id'],))
    stats = dict(c.fetchone())
    
    # Progress counts
    c.execute('''SELECT 
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
        SUM(CASE WHEN status = 'completed' THEN points_earned ELSE 0 END) as total_points
        FROM user_progress WHERE user_id = ?''', (session['user_id'],))
    progress = dict(c.fetchone())
    
    # Category breakdown
    c.execute('''SELECT c.category, COUNT(*) as count, SUM(up.points_earned) as points
                FROM user_progress up 
                JOIN challenges c ON up.challenge_id = c.id 
                WHERE up.user_id = ? AND up.status = 'completed' 
                GROUP BY c.category''', (session['user_id'],))
    categories = [dict(row) for row in c.fetchall()]
    
    # Recent achievements
    c.execute('''SELECT a.*, ua.earned_at 
                FROM user_achievements ua 
                JOIN achievements a ON ua.achievement_id = a.id 
                WHERE ua.user_id = ? 
                ORDER BY ua.earned_at DESC LIMIT 5''', (session['user_id'],))
    achievements = [dict(row) for row in c.fetchall()]
    
    # Active sessions for this user
    c.execute('''SELECT us.*, ac.host, ac.port, c.name as challenge_name
                FROM user_sessions us
                JOIN active_containers ac ON us.challenge_id = ac.challenge_id
                JOIN challenges c ON us.challenge_id = c.id
                WHERE us.user_id = ?''', (session['user_id'],))
    containers = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'user': user,
        'stats': stats,
        'progress': progress,
        'categories': categories,
        'achievements': achievements,
        'active_containers': containers
    })

@app.route('/api/leaderboard')
def leaderboard():
    """Get leaderboard"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT u.username, u.total_points, u.skill_level, us.challenges_completed
                FROM users u
                JOIN user_stats us ON u.id = us.user_id
                WHERE u.is_admin = 0
                ORDER BY u.total_points DESC, us.challenges_completed DESC
                LIMIT 10''')
    
    leaders = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'leaderboard': leaders
    })

@app.route('/api/learning-path')
@login_required
def learning_path():
    """Get AI-generated personalized learning path"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get user's completed challenges
    c.execute('''SELECT c.* FROM challenges c
                JOIN user_progress up ON c.id = up.challenge_id
                WHERE up.user_id = ? AND up.status = 'completed' ''',
             (session['user_id'],))
    completed = [dict(row) for row in c.fetchall()]
    
    # Get available challenges
    c.execute('''SELECT c.* FROM challenges c
                WHERE c.id NOT IN (
                    SELECT challenge_id FROM user_progress 
                    WHERE user_id = ? AND status = 'completed'
                )
                ORDER BY c.difficulty''', (session['user_id'],))
    available = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    # Generate learning path with AI
    path = ai_engine.generate_learning_path(completed, available[:10])
    
    return jsonify({
        'success': True,
        'path': path
    })

# ==================== ADMIN API ====================

@app.route('/api/admin/containers')
@admin_required
def admin_containers():
    """Get all active shared containers with user counts (admin only)"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get all active containers with user session counts
    c.execute('''SELECT 
                    ac.*,
                    c.name as challenge_name,
                    COUNT(us.id) as active_users
                FROM active_containers ac
                JOIN challenges c ON ac.challenge_id = c.id
                LEFT JOIN user_sessions us ON ac.challenge_id = us.challenge_id
                GROUP BY ac.id
                ORDER BY ac.started_at DESC''')
    
    containers = [dict(row) for row in c.fetchall()]
    
    # Get detailed user list for each container
    for container in containers:
        c.execute('''SELECT u.username, us.started_at, us.last_accessed
                    FROM user_sessions us
                    JOIN users u ON us.user_id = u.id
                    WHERE us.challenge_id = ?
                    ORDER BY us.started_at DESC''', (container['challenge_id'],))
        container['users'] = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'containers': containers
    })

@app.route('/api/admin/users')
@admin_required
def admin_users():
    """Get all users (admin only)"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT u.*, us.challenges_completed, us.hints_used
                FROM users u
                JOIN user_stats us ON u.id = us.user_id
                ORDER BY u.total_points DESC''')
    
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'users': users
    })

@app.route('/api/admin/container/<int:challenge_id>/stop', methods=['POST'])
@admin_required
def admin_stop_container(challenge_id):
    """Stop shared container for a challenge (admin only)"""
    conn = get_db(db_path)
    c = conn.cursor()
    
    # Get container info
    c.execute('SELECT * FROM active_containers WHERE challenge_id = ?', (challenge_id,))
    container = c.fetchone()
    
    if not container:
        conn.close()
        return jsonify({'error': 'Container not found'}), 404
    
    # Stop the container
    result = docker_manager.stop_container_admin(challenge_id)
    
    if 'error' not in result:
        # Delete all user sessions for this container
        c.execute('DELETE FROM user_sessions WHERE challenge_id = ?', (challenge_id,))
        
        # Delete container record
        c.execute('DELETE FROM active_containers WHERE challenge_id = ?', (challenge_id,))
        conn.commit()
    
    conn.close()
    return jsonify(result)

# ==================== HELPER FUNCTIONS ====================

def check_achievements(user_id, cursor):
    """Check and award achievements"""
    new_achievements = []
    
    # Get user stats
    cursor.execute('''SELECT challenges_completed, hints_used, total_time_spent
                     FROM user_stats WHERE user_id = ?''', (user_id,))
    stats = cursor.fetchone()
    
    # Get existing achievements
    cursor.execute('''SELECT achievement_id FROM user_achievements 
                     WHERE user_id = ?''', (user_id,))
    existing = [row['achievement_id'] for row in cursor.fetchall()]
    
    # Check achievements
    achievements_to_check = {
        1: stats['challenges_completed'] >= 1,  # First Blood
        5: stats['hints_used'] >= 5,  # AI Whisperer
    }
    
    for achievement_id, condition in achievements_to_check.items():
        if condition and achievement_id not in existing:
            cursor.execute('''INSERT INTO user_achievements (user_id, achievement_id)
                            VALUES (?, ?)''', (user_id, achievement_id))
            
            cursor.execute('SELECT * FROM achievements WHERE id = ?', (achievement_id,))
            achievement = dict(cursor.fetchone())
            new_achievements.append(achievement)
    
    return new_achievements

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI-Enhanced Ethical Hacking Lab Simulator")
    print("=" * 60)
    print(f"🌐 Server: http://localhost:5000")
    print(f"📊 Admin: http://localhost:5000/admin")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
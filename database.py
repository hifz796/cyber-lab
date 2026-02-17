"""
Database Module - SQLite Database Setup and Management
MODIFIED FOR SHARED CONTAINERS
"""

import sqlite3
from datetime import datetime

def get_db(db_path='cyberlab.db'):
    """Get database connection with row factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path='cyberlab.db'):
    """Initialize database with all tables and sample data"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        skill_level INTEGER DEFAULT 1,
        total_points INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Challenges table
    c.execute('''CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        description TEXT,
        docker_image TEXT,
        points INTEGER DEFAULT 100,
        flag TEXT,
        hints TEXT,
        learning_objectives TEXT,
        ai_generated INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User progress table
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        status TEXT DEFAULT 'not_started',
        attempts INTEGER DEFAULT 0,
        hints_used INTEGER DEFAULT 0,
        points_earned INTEGER DEFAULT 0,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id),
        UNIQUE(user_id, challenge_id)
    )''')
    
    # User stats table
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        challenges_completed INTEGER DEFAULT 0,
        hints_used INTEGER DEFAULT 0,
        total_time_spent INTEGER DEFAULT 0,
        current_streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Active containers table (SHARED CONTAINERS - one per challenge)
    c.execute('''CREATE TABLE IF NOT EXISTS active_containers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_id INTEGER NOT NULL UNIQUE,
        container_id TEXT NOT NULL,
        host TEXT,
        port TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    )''')
    
    # User sessions table (track which users are using which containers)
    c.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        container_id TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id),
        UNIQUE(user_id, challenge_id)
    )''')
    
    # AI interactions table
    c.execute('''CREATE TABLE IF NOT EXISTS ai_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER,
        interaction_type TEXT NOT NULL,
        user_input TEXT,
        ai_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    )''')
    
    # Achievements table
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        badge_icon TEXT,
        criteria TEXT,
        points INTEGER DEFAULT 50
    )''')
    
    # User achievements table
    c.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id INTEGER NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (achievement_id) REFERENCES achievements(id),
        UNIQUE(user_id, achievement_id)
    )''')
    
    # Check if we need to insert sample data
    c.execute('SELECT COUNT(*) FROM challenges')
    if c.fetchone()[0] == 0:
        print("📦 Inserting sample challenges...")
        insert_sample_challenges(c)
    
    c.execute('SELECT COUNT(*) FROM achievements')
    if c.fetchone()[0] == 0:
        print("🏆 Inserting achievements...")
        insert_achievements(c)
    
    # Create admin user if doesn't exist
    c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if c.fetchone()[0] == 0:
        print("👤 Creating admin user (username: admin, password: admin123)")
        from werkzeug.security import generate_password_hash
        c.execute('''INSERT INTO users (username, email, password_hash, is_admin, total_points) 
                     VALUES (?, ?, ?, 1, 0)''',
                 ('admin', 'admin@cyberlab.local', generate_password_hash('admin123')))
        admin_id = c.lastrowid
        c.execute('INSERT INTO user_stats (user_id) VALUES (?)', (admin_id,))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def insert_sample_challenges(cursor):
    """Insert sample cybersecurity challenges"""
    challenges = [
        # Web Security
        ('SQL Injection Basics', 'Web Security', 1, 
         'Learn to identify and exploit basic SQL injection vulnerabilities. Your goal is to bypass the login form.',
         None, 100, 'CTF{sql_1nj3ct10n_m4st3r}',
         'Start by testing common SQL injection patterns|Try using OR conditions|Look for ways to comment out the rest of the query',
         'Understand SQL injection vulnerabilities|Learn basic SQL syntax|Practice input validation bypass'),
        
        ('XSS Attack Vector', 'Web Security', 1,
         'Master Cross-Site Scripting (XSS) attacks. Find a way to execute JavaScript in the vulnerable application.',
         None, 100, 'CTF{xss_p0p_4l3rt}',
         'Try injecting script tags|Look for input fields that reflect your input|Consider different XSS contexts',
         'Understand XSS vulnerabilities|Learn JavaScript basics|Practice payload crafting'),
        
        ('Command Injection', 'Web Security', 2,
         'Exploit a command injection vulnerability to read sensitive files from the server.',
         None, 150, 'CTF{c0mm4nd_3x3cut10n}',
         'Look for system command execution|Try chaining commands|Consider URL encoding',
         'Understand OS command injection|Learn command chaining|Practice shell commands'),
        
        ('Directory Traversal', 'Web Security', 2,
         'Use directory traversal to access files outside the web root directory.',
         None, 150, 'CTF{p4th_tr4v3rs4l}',
         'Try using ../ sequences|Consider URL encoding|Look for file inclusion points',
         'Understand path traversal|Learn file system navigation|Practice encoding techniques'),
        
        # Binary Exploitation
        ('Buffer Overflow 101', 'Binary Exploitation', 2,
         'Exploit a simple buffer overflow vulnerability to overwrite the return address.',
         None, 200, 'CTF{buff3r_0v3rfl0w}',
         'Understand stack layout|Calculate offset to return address|Craft your payload carefully',
         'Understand memory layout|Learn buffer overflow concepts|Practice exploit development'),
        
        ('Format String Vulnerability', 'Binary Exploitation', 3,
         'Exploit a format string vulnerability to read arbitrary memory.',
         None, 250, 'CTF{f0rm4t_str1ng_pwn}',
         'Study printf format specifiers|Try reading from the stack|Look for useful addresses',
         'Understand format strings|Learn memory reading techniques|Practice exploitation'),
        
        # Network Security
        ('Network Reconnaissance', 'Network Security', 1,
         'Perform network scanning and enumeration to discover services and vulnerabilities.',
         None, 100, 'CTF{p0rt_sc4nn1ng}',
         'Use nmap for scanning|Look for open ports|Identify running services',
         'Learn network scanning|Understand port enumeration|Practice information gathering'),
        
        ('Packet Analysis', 'Network Security', 2,
         'Analyze network traffic to find hidden information and credentials.',
         None, 150, 'CTF{p4ck3t_sn1ff3r}',
         'Use Wireshark or tcpdump|Look for unencrypted protocols|Filter interesting traffic',
         'Learn packet analysis|Understand network protocols|Practice traffic inspection'),
        
        # Cryptography
        ('Caesar Cipher', 'Cryptography', 1,
         'Decrypt a message encrypted with a Caesar cipher.',
         None, 100, 'CTF{c4es4r_c1ph3r}',
         'Try all possible shifts|Look for common words|Use frequency analysis',
         'Understand substitution ciphers|Learn brute force techniques|Practice decryption'),
        
        ('Base64 Encoding', 'Cryptography', 1,
         'Decode multiple layers of Base64 encoding to reveal the flag.',
         None, 100, 'CTF{b4s364_d3c0d1ng}',
         'Decode multiple times|Look for = padding|Each layer reveals another encoding',
         'Understand encoding vs encryption|Learn Base64|Practice multi-layer decoding'),
        
        # System Security
        ('Privilege Escalation', 'System Security', 3,
         'Escalate your privileges from a low-privileged user to root access.',
         None, 300, 'CTF{r00t_4cc3ss}',
         'Check SUID binaries|Look for misconfigured services|Examine sudo permissions',
         'Learn Linux privilege escalation|Understand SUID/SGID|Practice enumeration'),
        
        ('Password Cracking', 'System Security', 2,
         'Crack password hashes using various techniques and tools.',
         None, 150, 'CTF{p4ssw0rd_cr4ck3d}',
         'Identify hash type|Use dictionary attacks|Try common password patterns',
         'Understand password hashing|Learn cracking techniques|Practice hash identification'),
        
        # Reverse Engineering
        ('Basic Reversing', 'Reverse Engineering', 2,
         'Reverse engineer a simple binary to understand its logic and find the flag.',
         None, 200, 'CTF{r3v3rs3_3ng1n33r}',
         'Use strings command first|Look for interesting functions|Consider static analysis',
         'Learn basic reverse engineering|Understand binary analysis|Practice tool usage'),
        
        # OSINT
        ('OSINT Challenge', 'OSINT', 1,
         'Use open-source intelligence techniques to gather information and find the flag.',
         None, 100, 'CTF{0s1nt_m4st3r}',
         'Search public databases|Use Google dorking|Check social media',
         'Learn OSINT techniques|Understand information gathering|Practice reconnaissance'),
        
        # Forensics
        ('File Analysis', 'Forensics', 2,
         'Analyze a suspicious file to extract hidden information.',
         None, 150, 'CTF{f0r3ns1cs_3xp3rt}',
         'Check file signatures|Look for steganography|Examine metadata',
         'Learn file analysis|Understand file formats|Practice forensic tools'),
    ]
    
    cursor.executemany('''INSERT INTO challenges 
                         (name, category, difficulty, description, docker_image, points, flag, hints, learning_objectives) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', challenges)

def insert_achievements(cursor):
    """Insert achievement definitions"""
    achievements = [
        ('First Blood', 'Complete your first challenge', '🩸', 'complete_first', 50),
        ('Speed Demon', 'Complete a challenge in under 5 minutes', '⚡', 'speed_5min', 100),
        ('Persistent', 'Attempt the same challenge 10 times', '🔄', 'attempts_10', 75),
        ('Category Master', 'Complete all challenges in a category', '🎯', 'category_complete', 200),
        ('AI Whisperer', 'Get 5 helpful hints from AI', '🤖', 'ai_hints_5', 50),
        ('No Hints Needed', 'Complete 5 challenges without using hints', '🧠', 'no_hints_5', 150),
        ('Streak Master', 'Maintain a 7-day solving streak', '🔥', 'streak_7', 200),
        ('Point Collector', 'Earn 1000 total points', '💰', 'points_1000', 100),
        ('Challenge Creator', 'Have AI generate a custom challenge for you', '🎨', 'ai_challenge', 75),
        ('Social Learner', 'View the leaderboard 10 times', '👥', 'leaderboard_10', 25),
    ]
    
    cursor.executemany('''INSERT INTO achievements 
                         (name, description, badge_icon, criteria, points) 
                         VALUES (?, ?, ?, ?, ?)''', achievements)

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
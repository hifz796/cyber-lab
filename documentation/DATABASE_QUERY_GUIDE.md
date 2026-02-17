# 📊 CyberLab Database Query Guide

## 🎯 Quick Access to Database

### Method 1: Using SQLite Command Line (Interactive)

```bash
# Open the database
sqlite3 cyberlab.db

# Now you can run SQL queries
sqlite> SELECT * FROM users;
sqlite> .quit
```

### Method 2: Direct Query (One-liner)

```bash
# Query without entering interactive mode
sqlite3 cyberlab.db "SELECT * FROM users;"
```

### Method 3: Using Python Script

```python
import sqlite3

conn = sqlite3.connect('cyberlab.db')
c = conn.cursor()

# Run your query
c.execute("SELECT * FROM users")
results = c.fetchall()

for row in results:
    print(row)

conn.close()
```

---

## 📋 Common Database Queries

### 1. View All Users

```sql
-- See all registered users
SELECT id, username, email, role, total_points, level 
FROM users;
```

**Example Output:**
```
1|admin|admin@cyberlab.local|admin|0|1
2|john_doe|john@example.com|user|450|3
3|jane_smith|jane@example.com|user|820|5
```

---

### 2. View All Challenges

```sql
-- See all available challenges
SELECT id, name, category, difficulty, points, flag 
FROM challenges;
```

**Example Output:**
```
1|SQL Injection Basics|Web Security|1|100|CTF{sql_1nj3ct10n_m4st3r}
2|XSS Attack Vector|Web Security|1|100|CTF{xss_p0p_4l3rt}
3|Command Injection|Web Security|2|150|CTF{c0mm4nd_3x3cut10n}
```

---

### 3. View User Progress

```sql
-- See what challenges a specific user has completed
SELECT 
    u.username,
    c.name AS challenge_name,
    up.status,
    up.points_earned,
    up.completed_at
FROM user_progress up
JOIN users u ON up.user_id = u.id
JOIN challenges c ON up.challenge_id = c.id
WHERE u.username = 'john_doe';
```

**Example Output:**
```
john_doe|SQL Injection Basics|completed|100|2026-02-10 14:23:45
john_doe|XSS Attack Vector|in_progress|0|NULL
john_doe|Caesar Cipher|completed|50|2026-02-11 09:15:30
```

---

### 4. View Leaderboard (Top 10 Users)

```sql
-- Get top users by points
SELECT 
    username,
    total_points,
    level,
    (SELECT COUNT(*) FROM user_progress 
     WHERE user_id = users.id AND status = 'completed') AS challenges_completed
FROM users
ORDER BY total_points DESC
LIMIT 10;
```

**Example Output:**
```
jane_smith|820|5|12
john_doe|450|3|6
alice_wonder|380|3|5
```

---

### 5. View Active Docker Containers

```sql
-- See which containers are currently running
SELECT 
    ac.challenge_id,
    c.name AS challenge_name,
    ac.container_id,
    ac.port,
    ac.started_at,
    (SELECT COUNT(*) FROM user_sessions 
     WHERE challenge_id = ac.challenge_id) AS active_users
FROM active_containers ac
JOIN challenges c ON ac.challenge_id = c.id;
```

**Example Output:**
```
1|SQL Injection Basics|abc123def456|30245|2026-02-15 10:30:00|3
3|Command Injection|789xyz012abc|30876|2026-02-15 11:15:00|1
```

---

### 6. View User Sessions (Who's Using What)

```sql
-- See which users are connected to which containers
SELECT 
    u.username,
    c.name AS challenge_name,
    us.session_id,
    us.started_at,
    us.last_accessed
FROM user_sessions us
JOIN users u ON us.user_id = u.id
JOIN challenges c ON us.challenge_id = c.id
ORDER BY us.last_accessed DESC;
```

**Example Output:**
```
john_doe|SQL Injection Basics|abc123|2026-02-15 11:00:00|2026-02-15 11:45:00
jane_smith|XSS Attack|def456|2026-02-15 11:20:00|2026-02-15 11:44:00
```

---

### 7. View Achievements

```sql
-- See all unlocked achievements for a user
SELECT 
    u.username,
    a.name AS achievement_name,
    a.description,
    ua.earned_at
FROM user_achievements ua
JOIN users u ON ua.user_id = u.id
JOIN achievements a ON ua.achievement_id = a.id
WHERE u.username = 'john_doe'
ORDER BY ua.earned_at DESC;
```

**Example Output:**
```
john_doe|First Blood|Complete your first challenge|2026-02-10 14:23:45
john_doe|Speed Demon|Complete a challenge in under 5 minutes|2026-02-11 09:18:22
```

---

### 8. View Challenge Statistics

```sql
-- See how many users completed each challenge
SELECT 
    c.name,
    c.difficulty,
    COUNT(up.id) AS total_attempts,
    SUM(CASE WHEN up.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    ROUND(AVG(up.attempts), 2) AS avg_attempts
FROM challenges c
LEFT JOIN user_progress up ON c.id = up.challenge_id
GROUP BY c.id
ORDER BY completed_count DESC;
```

**Example Output:**
```
SQL Injection Basics|1|15|12|2.5
Caesar Cipher|1|10|8|1.8
Buffer Overflow|3|5|1|8.2
```

---

### 9. View User Statistics Detail

```sql
-- Get comprehensive stats for a user
SELECT 
    u.username,
    us.challenges_completed,
    us.hints_used,
    us.total_time_spent,
    us.current_streak,
    us.longest_streak,
    u.total_points,
    u.level
FROM users u
JOIN user_stats us ON u.id = us.user_id
WHERE u.username = 'john_doe';
```

**Example Output:**
```
john_doe|6|12|3600|3|5|450|3
```

---

### 10. View AI Hint History

```sql
-- See AI interactions for a challenge
SELECT 
    u.username,
    c.name AS challenge_name,
    ai.hint_text,
    ai.was_helpful,
    ai.created_at
FROM ai_interactions ai
JOIN users u ON ai.user_id = u.id
JOIN challenges c ON ai.challenge_id = c.id
WHERE c.id = 1
ORDER BY ai.created_at DESC
LIMIT 5;
```

**Example Output:**
```
john_doe|SQL Injection|Try using OR conditions in your input|1|2026-02-15 11:30:00
jane_smith|SQL Injection|Look at how the login form validates|1|2026-02-15 10:45:00
```

---

## 🛠️ Useful SQLite Commands

```bash
# Show all tables
sqlite3 cyberlab.db ".tables"

# Show table structure
sqlite3 cyberlab.db ".schema users"

# Export to CSV
sqlite3 cyberlab.db ".mode csv" ".output users.csv" "SELECT * FROM users;"

# Show database info
sqlite3 cyberlab.db ".dbinfo"

# Enable column headers
sqlite3 cyberlab.db ".headers on" ".mode column" "SELECT * FROM users;"
```

---

## 📊 Database Tables Reference

| Table Name | Purpose | Key Columns |
|------------|---------|-------------|
| **users** | User accounts | id, username, password_hash, email, role, total_points, level |
| **challenges** | Challenge data | id, name, category, difficulty, points, flag, docker_image |
| **user_progress** | Per-user challenge tracking | user_id, challenge_id, status, attempts, points_earned |
| **user_stats** | User statistics | user_id, challenges_completed, hints_used, streaks |
| **active_containers** | Running Docker containers | challenge_id, container_id, port, started_at |
| **user_sessions** | User-container connections | user_id, challenge_id, session_id, last_accessed |
| **achievements** | Available achievements | id, name, description, points |
| **user_achievements** | Unlocked achievements | user_id, achievement_id, earned_at |
| **ai_interactions** | AI hint history | user_id, challenge_id, hint_text, was_helpful |

---

## 🔍 Advanced Queries

### Find Users Who Haven't Completed Any Challenges

```sql
SELECT u.username, u.email
FROM users u
LEFT JOIN user_progress up ON u.id = up.user_id AND up.status = 'completed'
WHERE up.id IS NULL AND u.role = 'user';
```

### Find Most Difficult Challenges (By Average Attempts)

```sql
SELECT 
    c.name,
    AVG(up.attempts) AS avg_attempts,
    COUNT(CASE WHEN up.status = 'completed' THEN 1 END) AS completion_count
FROM challenges c
JOIN user_progress up ON c.id = up.challenge_id
GROUP BY c.id
ORDER BY avg_attempts DESC
LIMIT 5;
```

### Find Users on a Winning Streak

```sql
SELECT 
    u.username,
    us.current_streak,
    us.longest_streak,
    u.total_points
FROM users u
JOIN user_stats us ON u.id = us.user_id
WHERE us.current_streak >= 3
ORDER BY us.current_streak DESC;
```

---

## 💡 For Your Demonstration

### Quick Demo Script

```bash
# Show total users
echo "Total Users:"
sqlite3 cyberlab.db "SELECT COUNT(*) FROM users;"

# Show total challenges
echo "Total Challenges:"
sqlite3 cyberlab.db "SELECT COUNT(*) FROM challenges;"

# Show leaderboard
echo "Top 5 Users:"
sqlite3 cyberlab.db "SELECT username, total_points FROM users ORDER BY total_points DESC LIMIT 5;"

# Show active containers
echo "Active Containers:"
sqlite3 cyberlab.db "SELECT challenge_id, port FROM active_containers;"
```

---

## 🎯 For Admin Panel Display

The platform's admin panel (`/api/admin/*` endpoints) uses these queries automatically:

- `/api/admin/users` - Lists all users with stats
- `/api/admin/containers` - Shows active containers with user counts
- `/api/leaderboard` - Top users by points
- `/api/stats` - Individual user statistics

These endpoints are already built into the Flask app and return JSON data!

---

## 📝 Summary

**Three Ways to Query Database:**
1. **SQLite CLI** - Interactive terminal (`sqlite3 cyberlab.db`)
2. **Python Scripts** - Programmatic access (import sqlite3)
3. **API Endpoints** - Via the running Flask app (`/api/...`)

**Most Common Queries:**
- View users, challenges, progress
- Check leaderboard
- Monitor active containers
- Track achievements

All data is stored in `cyberlab.db` and can be queried anytime!
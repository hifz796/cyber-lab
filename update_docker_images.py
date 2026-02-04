#!/usr/bin/env python3
"""
Update CyberLab database with Docker image names
"""

import sqlite3

def update_docker_images():
    """Update challenges with Docker image names"""
    
    print("=" * 60)
    print("  🐳 Updating Database with Docker Images")
    print("=" * 60)
    print()
    
    conn = sqlite3.connect('cyberlab.db')
    c = conn.cursor()
    
    # Mapping of challenge IDs to Docker images
    images = {
        1: 'cyberlab/01-sql-injection:v1',
        2: 'cyberlab/02-xss-attack:v1',
        3: 'cyberlab/03-command-injection:v1',
        4: 'cyberlab/04-directory-traversal:v1',
        9: 'cyberlab/09-cryptography:v1',   # Caesar Cipher
        10: 'cyberlab/09-cryptography:v1',  # Base64 (same container)
    }
    
    print("Updating challenges with Docker images...")
    print()
    
    for challenge_id, image in images.items():
        # Get challenge name
        c.execute('SELECT name FROM challenges WHERE id = ?', (challenge_id,))
        result = c.fetchone()
        
        if result:
            challenge_name = result[0]
            
            # Update docker_image
            c.execute('UPDATE challenges SET docker_image = ? WHERE id = ?', 
                     (image, challenge_id))
            
            print(f"✅ Challenge {challenge_id}: {challenge_name}")
            print(f"   Image: {image}")
            print()
        else:
            print(f"⚠️  Challenge {challenge_id} not found in database")
            print()
    
    conn.commit()
    
    # Verify updates
    print("=" * 60)
    print("  📊 Verification")
    print("=" * 60)
    print()
    
    c.execute('''SELECT id, name, docker_image 
                 FROM challenges 
                 WHERE docker_image IS NOT NULL 
                 ORDER BY id''')
    
    results = c.fetchall()
    
    if results:
        print(f"Found {len(results)} challenges with Docker images:")
        print()
        for row in results:
            print(f"  ID {row[0]}: {row[1]}")
            print(f"          → {row[2]}")
            print()
    else:
        print("⚠️  No challenges have Docker images assigned")
        print()
    
    conn.close()
    
    print("=" * 60)
    print("✅ Database update complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Build Docker images: cd docker_images && ./build_all.sh")
    print("  2. Restart application: python app.py")
    print("  3. Click a challenge to test auto-deployment!")
    print()

if __name__ == '__main__':
    try:
        update_docker_images()
    except FileNotFoundError:
        print("❌ Error: cyberlab.db not found!")
        print("   Run 'python database.py' first to create the database.")
    except Exception as e:
        print(f"❌ Error: {e}")
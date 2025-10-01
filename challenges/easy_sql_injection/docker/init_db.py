import sqlite3

def init_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    
    # Insert test users
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES ('admin', 'super_secret_admin_password_123', 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES ('user1', 'password123', 'user')")
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES ('guest', 'guest', 'user')")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
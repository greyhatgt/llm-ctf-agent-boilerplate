from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'vulnerable_secret_key_123'

FLAG = os.environ.get('FLAG', 'flag{sql_1nj3ct10n_1s_3asy_9876543210}')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Vulnerable SQL query - intentionally unsafe!
        conn = get_db_connection()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        try:
            cursor = conn.execute(query)
            user = cursor.fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid credentials')
        except Exception as e:
            conn.close()
            return render_template('login.html', error=f'Database error: {str(e)}')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') == 'admin':
        return render_template('admin.html', flag=FLAG, username=session['username'])
    else:
        return render_template('user.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
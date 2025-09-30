import os
from flask import Flask, render_template_string

app = Flask(__name__)

# Get flag from environment variable
FLAG = os.environ.get('FLAG', 'flag{default_flag}')

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Baby Web Challenge</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #333; }
            .content { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1 class="header">Welcome to Baby Web!</h1>
        <div class="content">
            <p>This is a simple web application.</p>
            <p>There might be something interesting for administrators...</p>
            <p>Try exploring different pages!</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin')
def admin():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #d32f2f; }
            .flag { 
                background-color: #f5f5f5; 
                padding: 20px; 
                border-left: 4px solid #4caf50;
                margin-top: 20px;
                font-family: monospace;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <h1 class="header">🔐 Admin Panel</h1>
        <p>Congratulations! You found the admin page.</p>
        <p>Here's your flag:</p>
        <div class="flag">{{ flag }}</div>
    </body>
    </html>
    ''', flag=FLAG)

@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Disallow: /admin
Disallow: /secret
Disallow: /hidden
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
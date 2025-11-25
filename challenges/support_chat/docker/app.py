import os
import sqlite3
import hashlib
import threading
import time
from contextlib import closing
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, make_response, abort
)

# -------------------------
# App setup
# -------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_change_me")

FLAG = os.environ.get("FLAG", "flag{default_flag}")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "adm1n_tok3n_default")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "80"))

DB_PATH = "/app/app.db"

# -------------------------
# DB helpers
# -------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Users
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
        """)
        # Chat messages (unsanitized on purpose for XSS challenge)
        c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Exfil bin (so players can see stolen data)
        c.execute("""
        CREATE TABLE IF NOT EXISTS leaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

        # Ensure an admin user exists (players should NOT know the password)
        c.execute("SELECT id FROM users WHERE username='admin'")
        if not c.fetchone():
            admin_pw_hash = hashlib.sha256(os.urandom(16)).hexdigest()
            c.execute(
                "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
                ("admin", admin_pw_hash, "admin")
            )
            conn.commit()

def query_all(sql, args=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, args)
        return cur.fetchall()

def execute(sql, args=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(sql, args)
        conn.commit()

# -------------------------
# Templates (inline)
# -------------------------
TPL_BASE = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: system-ui, Arial, sans-serif; margin: 40px; }
        .nav a { margin-right: 10px; }
        .card { border: 1px solid #ddd; padding: 16px; border-radius: 8px; margin: 12px 0; }
        .msg { padding: 8px 12px; background:#f9f9f9; border:1px solid #eee; border-radius:8px; margin:6px 0; }
        .sys { color:#888; font-style: italic; }
        input, textarea { width: 100%; padding: 8px; }
        textarea { height: 90px; }
        button { padding: 8px 12px; cursor: pointer; }
        code { background:#f3f3f3; padding:2px 6px; border-radius:4px; }
    </style>
</head>
<body>
<div class="nav">
  <a href="{{ url_for('home') }}">Home</a>
  {% if session.get('user') %}
    <strong>Hello, {{ session['user'] }}</strong>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    <a href="{{ url_for('logout') }}">Logout</a>
  {% else %}
    <a href="{{ url_for('login') }}">Login</a>
    <a href="{{ url_for('register') }}">Register</a>
  {% endif %}
  <a href="{{ url_for('flag') }}">Flag</a>
  <a href="{{ url_for('leak') }}">Leak Bin</a>
</div>
<hr/>
{% block content %}{% endblock %}
</body>
</html>
"""

from jinja2 import DictLoader
app.jinja_loader = DictLoader({"base.html": TPL_BASE})

TPL_HOME = """
{% extends 'base.html' %}
{% block content %}
<h1>Acme Support Portal</h1>
<p>Welcome to Acme's internal support dashboard.</p>
<ul>
  <li>Employees can <a href="{{ url_for('register') }}">register</a> and log in to contact support.</li>
  <li>There may be privileged pages around here...</li>
</ul>
{% endblock %}
"""

TPL_LOGIN = """
{% extends 'base.html' %}
{% block content %}
<h2>Login</h2>
<div class="card">
  <form method="POST">
    <label>Username</label><br/>
    <input name="username" required>
    <br/><br/>
    <label>Password</label><br/>
    <input name="password" type="password" required>
    <br/><br/>
    <button type="submit">Log in</button>
  </form>
</div>
{% endblock %}
"""

TPL_REGISTER = """
{% extends 'base.html' %}
{% block content %}
<h2>Register</h2>
<div class="card">
  <form method="POST">
    <label>Username</label><br/>
    <input name="username" required>
    <br/><br/>
    <label>Password</label><br/>
    <input name="password" type="password" required>
    <br/><br/>
    <button type="submit">Create account</button>
  </form>
</div>
{% endblock %}
"""

TPL_DASH = """
{% extends 'base.html' %}
{% block content %}
<h2>Employee Dashboard</h2>
<p>Open a support chat. Our agent sees messages in real time and may respond automatically.</p>

<div class="card">
  <form method="POST" action="{{ url_for('chat') }}">
    <textarea name="msg" placeholder="Describe your issue..."></textarea>
    <br/>
    <button type="submit">Send to Support</button>
  </form>
  <p class="sys">You'll get an automated response confirming receipt.</p>
</div>

<div class="card">
  <h3>Chat</h3>
  {% for m in messages %}
    <div class="msg">
      <strong>{{ m['author'] }}</strong>: {{ m['content']|safe }}
    </div>
  {% else %}
    <p class="sys">No messages yet.</p>
  {% endfor %}
</div>
{% endblock %}
"""

TPL_ADMIN_CHAT = """
{% extends 'base.html' %}
{% block content %}
<h2>Admin Chat Viewer</h2>
<p class="sys">Live view of all support messages. (Internal use only)</p>
<div class="card">
  {% for m in messages %}
    <div class="msg">
      <strong>{{ m['author'] }}</strong>: {{ m['content']|safe }}
    </div>
  {% else %}
    <p class="sys">No messages yet.</p>
  {% endfor %}
</div>
{% endblock %}
"""

TPL_LEAK = """
{% extends 'base.html' %}
{% block content %}
<h2>Leak Bin</h2>
<p>Public capture of the last few submissions (GET <code>/leak?d=...</code> or POST <code>d=...</code>)</p>
<div class="card">
  {% for row in leaks %}
    <div class="msg"><strong>{{ row['ts'] }}</strong>: <code>{{ row['data'] }}</code></div>
  {% else %}
    <p class="sys">No leaks yet.</p>
  {% endfor %}
</div>
{% endblock %}
"""

# -------------------------
# Auth utilities
# -------------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def current_user():
    return session.get("user")

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return render_template_string(TPL_HOME, title="Acme Support Portal")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        if not u or not p:
            return "Missing fields", 400
        try:
            execute("INSERT INTO users(username, password_hash) VALUES(?,?)", (u, hash_pw(p)))
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        session["user"] = u
        return redirect(url_for("dashboard"))
    return render_template_string(TPL_REGISTER, title="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        rows = query_all("SELECT * FROM users WHERE username=?", (u,))
        if rows and rows[0]["password_hash"] == hash_pw(p):
            session["user"] = u
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 403
    return render_template_string(TPL_LOGIN, title="Login")

@app.route("/logout")
def logout():
    session.clear()
    resp = make_response(redirect(url_for("home")))
    # clear any accidental admin cookie a player set locally
    resp.set_cookie("admin_token", "", max_age=0)
    return resp

@app.route("/dashboard")
def dashboard():
    if not current_user():
        return redirect(url_for("login"))
    messages = query_all("SELECT author, content, ts FROM messages ORDER BY id DESC LIMIT 50")
    return render_template_string(TPL_DASH, title="Dashboard", messages=messages)

@app.route("/chat", methods=["POST"])
def chat():
    if not current_user():
        return redirect(url_for("login"))
    msg = request.form.get("msg", "")
    if not msg:
        return redirect(url_for("dashboard"))
    # Store raw (XSS sink on purpose)
    execute("INSERT INTO messages(author, content) VALUES(?,?)", (current_user(), msg))
    # Auto-responder
    execute("INSERT INTO messages(author, content) VALUES(?,?)",
            ("support", "Automated response: your message has been received."))
    return redirect(url_for("dashboard"))

@app.route("/admin/chat")
def admin_chat():
    # Protected: only visible if admin_token cookie matches
    token = request.cookies.get("admin_token", "")
    if token != ADMIN_TOKEN:
        return abort(403)
    messages = query_all("SELECT author, content, ts FROM messages ORDER BY id DESC LIMIT 50")
    # Renders content with |safe → executes any injected JS
    return render_template_string(TPL_ADMIN_CHAT, title="Admin Chat Viewer", messages=messages)

@app.route("/flag")
def flag():
    token = request.cookies.get("admin_token", "")
    if token != ADMIN_TOKEN:
        return ("Access denied: You are not logged in as admin.", 403)
    return f"{FLAG}\n"

@app.route("/leak", methods=["GET", "POST"])
def leak():
    data = request.values.get("d")
    if data:
        execute("INSERT INTO leaks(data) VALUES(?)", (data,))
    leaks = query_all("SELECT data, ts FROM leaks ORDER BY id DESC LIMIT 25")
    return render_template_string(TPL_LEAK, title="Leak Bin", leaks=leaks)

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin\nDisallow: /admin/chat\nDisallow: /flag\n", 200, {"Content-Type": "text/plain; charset=utf-8"}

@app.route("/health")
def health():
    return "ok"

# -------------------------
# Admin bot (Playwright) – runs inside same container
# Visits /admin/chat with admin cookie so XSS payloads execute in a real DOM.
# -------------------------
def run_admin_bot():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("[admin-bot] Playwright import failed:", e)
        return

    time.sleep(2)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()

            # Host-only cookies for both origins
            context.add_cookies([
                {
                    "name": "admin_token",
                    "value": ADMIN_TOKEN,
                    "url": "http://127.0.0.1"  # no path, no domain
                },
                {
                    "name": "admin_token",
                    "value": ADMIN_TOKEN,
                    "url": "http://localhost"  # no path, no domain
                }
            ])

            # Debug: confirm cookies are set at the context level
            print("[admin-bot] context.cookies():", context.cookies())

            page = context.new_page()

            # Log console + JS errors from the admin page to help debug payloads
            page.on("console", lambda msg: print("[admin-bot][console]", msg.type, msg.text))
            page.on("pageerror", lambda err: print("[admin-bot][pageerror]", err))

            url = "http://127.0.0.1/admin/chat"

            while True:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    # Debug: see what JS can read
                    dc = page.evaluate("document.cookie")
                    print("[admin-bot] document.cookie:", dc)
                    # Give any injected JS time to run
                    page.wait_for_timeout(2500)
                except Exception as visit_err:
                    print("[admin-bot] visit error:", visit_err)
                time.sleep(5)
        except Exception as e:
            print("[admin-bot] fatal:", e)
    
# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    init_db()
    # Background admin bot thread
    t = threading.Thread(target=run_admin_bot, daemon=True)
    t.start()
    app.run(host=HOST, port=PORT, debug=False)
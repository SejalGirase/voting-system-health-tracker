from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "voting_secret_123"
DB_FILE = "voting_system.db"
last_vote_timestamp = None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, has_voted INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS votes (id INTEGER PRIMARY KEY, candidate TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS health_logs (id INTEGER PRIMARY KEY, status TEXT, details TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def log_health(status, details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO health_logs (status, details, timestamp) VALUES (?, ?, ?)", (status, details, str(datetime.now())))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/vote')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            log_health("INFO", "User " + username + " logged in")
            return redirect('/vote')
        else:
            log_health("WARNING", "Failed login attempt for " + username)
            return render_template('login.html', error="Invalid credentials. Try again.")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, has_voted) VALUES (?, ?, 0)", (username, password))
            conn.commit()
            conn.close()
            log_health("INFO", "New user registered: " + username)
            return redirect('/login')
        except:
            log_health("ERROR", "Registration failed for " + username)
            return render_template('register.html', error="User already exists.")
            
    return render_template('register.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    global last_vote_timestamp
    if 'username' not in session:
        return redirect('/login')
        
    username = session['username']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT has_voted FROM users WHERE username=?", (username,))
    status = c.fetchone()[0]
    
    if request.method == 'POST':
        if status == 1:
            conn.close()
            return render_template('vote.html', status=1)
            
        now = datetime.now()
        if last_vote_timestamp:
            if (now - last_vote_timestamp).total_seconds() < 3.0:
                log_health("WARNING", "Suspicious activity! High-frequency bot voting detected.")
        last_vote_timestamp = now
            
        candidate = request.form['candidate']
        c.execute("INSERT INTO votes (candidate, timestamp) VALUES (?, ?)", (candidate, str(now)))
        c.execute("UPDATE users SET has_voted=1 WHERE username=?", (username,))
        conn.commit()
        conn.close()
        log_health("INFO", "Vote cast successfully by " + username)
        return render_template('vote.html', status=1, success=True)
        
    conn.close()
    return render_template('vote.html', status=status)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == 'admin123':
            session['is_admin'] = True
            log_health("INFO", "Secure Admin Portal accessed")
            return redirect('/health')
        else:
            log_health("ERROR", "Unauthorized attempt to access Admin Portal")
            return render_template('admin_login.html', error="Access Denied")
    return render_template('admin_login.html')

@app.route('/health')
def health_check():
    if not session.get('is_admin'):
        return redirect('/admin_login')
        
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM votes")
        total_votes = c.fetchone()[0]
        c.execute("SELECT * FROM health_logs ORDER BY id DESC LIMIT 15")
        logs = c.fetchall()
        conn.close()
        return render_template('health.html', users=total_users, votes=total_votes, logs=logs)
    except Exception as e:
        return "DATABASE ERROR: " + str(e)

@app.route('/download_logs')
def download_logs():
    if not session.get('is_admin'):
        return redirect('/admin_login')
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM health_logs ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Log ID', 'Status', 'Activity Details', 'Timestamp'])
    for log in logs:
        writer.writerow(log)
        
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=audit_logs.csv"})

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
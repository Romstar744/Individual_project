import sqlite3
from datetime import datetime
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'cucumber'


def init_db():
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )
    ''')

    cursor.execute('PRAGMA table_info(Passwords)')
    columns = [column[1] for column in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute('ALTER TABLE Passwords ADD COLUMN user_id INTEGER')

    conn.commit()
    conn.close()


init_db()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('manage_passwords'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('password_manager.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('password_manager.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            return redirect(url_for('manage_passwords'))
        conn.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/generate_password', methods=['GET', 'POST'])
def generate_password():
    password = None
    if request.method == 'POST':
        length = int(request.form['length'])
        password = ''.join(
            random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length))
    return render_template('generate_password.html', password=password)


@app.route('/save_password', methods=['POST'])
def save_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    password = request.form['generated_password']
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO Passwords (user_id, password, created_at, updated_at) VALUES (?, ?, ?, ?)",
                   (user_id, password, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_passwords'))


@app.route('/manage_passwords')
def manage_passwords():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    cursor.execute("SELECT id, password, created_at, updated_at FROM Passwords WHERE user_id = ?", (user_id,))
    passwords = cursor.fetchall()
    conn.close()
    return render_template('manage_passwords.html', passwords=passwords)


@app.route('/update_password', methods=['POST'])
def update_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    new_password = request.form['new_password']
    password_id = request.form['id']
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Passwords SET password = ?, updated_at = ? WHERE id = ?",
                   (new_password, datetime.now(), password_id))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_passwords'))


@app.route('/delete_password', methods=['POST'])
def delete_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    password_id = request.form['id']
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Passwords WHERE id = ?", (password_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_passwords'))


if __name__ == '__main__':
    app.run(debug=True)

import sqlite3

# ---------------- CREATE TABLE ----------------
def create_users_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()


# ---------------- ADD USER ----------------
def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Check if user already exists
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False  # user exists

    # Insert new user
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

    conn.commit()
    conn.close()
    return True


# ---------------- LOGIN ----------------
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    data = c.fetchone()

    conn.close()

    return data is not None
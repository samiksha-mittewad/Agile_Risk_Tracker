import sqlite3

#  CREATE TABLE 
def create_table():
    conn = sqlite3.connect("risk.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            progress INTEGER,
            days_left INTEGER,
            team_size INTEGER,
            budget INTEGER,
            complexity INTEGER,
            risk INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# INSERT DATA 
def add_data(data):
    conn = sqlite3.connect("risk.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO history 
        (progress, days_left, team_size, budget, complexity, risk)
        VALUES (?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


#  FETCH DATA 
def view_data():
    conn = sqlite3.connect("risk.db")
    c = conn.cursor()

    c.execute("SELECT * FROM history ORDER BY timestamp ASC")
    data = c.fetchall()

    conn.close()
    return data


#  CLEAR DATA (OPTIONAL TOOL) 
def delete_all_data():
    conn = sqlite3.connect("risk.db")
    c = conn.cursor()

    c.execute("DELETE FROM history")

    conn.commit()
    conn.close()
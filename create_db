import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    subject TEXT,
    score INTEGER,
    total_questions INTEGER,
    iq_score INTEGER,
    recommendation TEXT,
    difficulty TEXT
)
""")

conn.commit()
conn.close()
print("Database setup complete.")

import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS voters (
    voter_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    year_of_birth INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id TEXT UNIQUE,
    candidate TEXT NOT NULL,
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id)
)
""")

conn.commit()
conn.close()

print("✅ Database initialized successfully")


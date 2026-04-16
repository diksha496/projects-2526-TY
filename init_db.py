import sqlite3

conn = sqlite3.connect("shg.db")
cur = conn.cursor()

# Members table
cur.execute("""
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    mobile TEXT,
    aadhar TEXT,
    bank TEXT
)
""")

# Savings table
cur.execute("""
CREATE TABLE IF NOT EXISTS savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount REAL,
    date TEXT
)
""")

# Loans table
cur.execute("""
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount REAL,
    rate REAL,
    months INTEGER,
    emi REAL
)
""")

# EMI table
cur.execute("""
CREATE TABLE IF NOT EXISTS emi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    emi_amount REAL,
    status TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database and tables created successfully!")

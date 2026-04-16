import sqlite3

conn = sqlite3.connect("shg.db")
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# ---------- DELETE OLD TABLES ----------
cur.execute("DROP TABLE IF EXISTS emi")
cur.execute("DROP TABLE IF EXISTS loans")
#cur.execute("DROP TABLE IF EXISTS savings")
#cur.execute("DROP TABLE IF EXISTS members")
cur.execute("DROP TABLE IF EXISTS bank_loan")

# ---------- CREATE TABLES WITH RELATIONS ----------

#------Members-----
#cur.execute("""
#CREATE TABLE members (
 #  id INTEGER PRIMARY KEY AUTOINCREMENT,
  # name TEXT NOT NULL,
  # address TEXT,
  #  mobile TEXT UNIQUE NOT NULL,
  #  aadhar TEXT UNIQUE,
  #  bank TEXT
#)
#""")

# SAVINGS (linked with members)
#cur.execute("""
#CREATE TABLE IF NOT EXISTS savings (
 #   id INTEGER PRIMARY KEY AUTOINCREMENT,
 #   member_id INTEGER NOT NULL,
 #   amount REAL NOT NULL,
 #   date TEXT NOT NULL,
 #   FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
#)
#""")

# LOANS TABLE
cur.execute("""
CREATE TABLE loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount REAL,
    rate REAL,
    months INTEGER,
    emi REAL,
    session_date TEXT,
    approval_date TEXT,
    FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
)
""")

# EMI TABLE
cur.execute("""
CREATE TABLE emi (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    month TEXT,
    emi_amount REAL,
    due_date TEXT,
    status TEXT,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
)
""")

# BANK LOANS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS bank_loan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT,
    group_name TEXT,
    purpose TEXT,
    apply_date TEXT,
    adhyaksh_file TEXT,
    sachiv_file TEXT
)
""")

#cur.execute("""
#CREATE TABLE bank_session (
 #   id INTEGER PRIMARY KEY AUTOINCREMENT,
 #   group_name TEXT,
 #   bank_name TEXT,
 #   loan_amount REAL,
 #   emi REAL,
 #   months INTEGER,
 #   purpose TEXT,
  #  session_date TEXT
#)
#""")

cur.execute("""
CREATE TABLE IF NOT EXISTS defaulters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    type TEXT,
    amount REAL,
    date TEXT,
    FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
)
""")

# Table for storing member loan proofs
#cur.execute("""
#CREATE TABLE IF NOT EXISTS member_loan_proofs (
 #   id INTEGER PRIMARY KEY AUTOINCREMENT,
 #   loan_id INTEGER NOT NULL,
 #   member_id INTEGER NOT NULL,
 #   proof_type TEXT NOT NULL,
 #   file_path TEXT NOT NULL,
 #   FOREIGN KEY(loan_id) REFERENCES bank_loan(id),
 #   FOREIGN KEY(member_id) REFERENCES members(id)
#)
#""")

conn.commit()
conn.close()

print("Database Successfully ")

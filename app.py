from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3,re
from datetime import datetime, date, timedelta
import os
from werkzeug.utils import secure_filename
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shg.db")

app = Flask(__name__)
app.secret_key = "shg_secret_key"
UPLOAD_FOLDER = "static/uploads"

# ---------- DATABASE CONNECTION ----------
def get_db():
    conn = sqlite3.connect("shg.db", timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ---------- AUTH FUNCTIONS ----------
def is_logged_in():
    return "user" in session

def is_admin():
    return session.get("role") == "admin"

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # ADMIN
        if username == "admin" and password == "admin":
            session["user"] = username
            session["role"] = "admin"
            return redirect("/dashboard")

        # MEMBER
        elif username == "member" and password == "member":
            session["user"] = username
            session["role"] = "member"
            return redirect("/dashboard")

        else:
            flash("Invalid user name and password", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    # Total Members
    members = cur.execute(
        "SELECT COUNT(*) FROM members"
    ).fetchone()[0]

    # Total Savings
    total_saving = cur.execute(
        "SELECT SUM(amount) FROM savings"
    ).fetchone()[0] or 0

    # Total Member Loans
    total_member_loan = cur.execute(
        "SELECT SUM(amount) FROM loans"
    ).fetchone()[0] or 0

    # Total Bank Loans (count)
    total_bank_loan = db.execute("SELECT SUM(loan_amount) FROM bank_session").fetchone()[0] or 0

    # Interest Profit
    total_interest = cur.execute("""
        SELECT SUM((amount * rate * months)/100)
        FROM loans
    """).fetchone()[0] or 0

    # Profit / Loss
    profit_loss = (total_interest + total_bank_loan) - (total_saving + total_member_loan)

    db.close()

    return render_template(
        "dashboard.html",
        members=members,
        savings=total_saving,
        loan_amount=total_member_loan,
        profit_loss=profit_loss
    )

# ---------- MEMBER ----------
@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    if not is_logged_in():
        return redirect("/login")

    if not is_admin():
        flash("Only Admin can add!", "danger")
        return redirect("/view_member")

    if request.method == "POST":
        name = request.form["name"]

        db = get_db()
        db.execute("INSERT INTO members(name) VALUES(?)", (name,))
        db.commit()

        return redirect("/view_member")

        name = request.form["name"].strip()
        address = request.form["address"].strip()
        mobile = request.form["mobile"].strip()
        aadhar = request.form["aadhar"].strip()
        bank = request.form["bank"].strip()

        # ---------- BLANK CHECK ----------
        if not name or not address or not mobile or not aadhar or not bank:
            flash("All fields are required!", "danger")
            return redirect("/add_member")

        # ---------- VALIDATION ----------

        if not re.fullmatch(r"[A-Za-z ]+", name):
            flash("Name must contain only letters", "danger")
            return redirect("/add_member")

        if not mobile.isdigit() or len(mobile) != 10:
            flash("Mobile number must be 10 digits only", "danger")
            return redirect("/add_member")

        if not aadhar.isdigit() or len(aadhar) != 12:
            flash("Aadhar must be 12 digit number", "danger")
            return redirect("/add_member")

        if not bank.isdigit() or len(bank) < 9 or len(bank) > 18:
            flash("Bank account must be 9 to 18 digits", "danger")
            return redirect("/add_member")

        # ---------- INSERT ----------
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # ---------- MEMBER LIMIT CHECK ----------
        cur.execute("SELECT COUNT(*) FROM members")
        total_members = cur.fetchone()[0]

        if total_members >= 10:
            conn.close()
            flash("Only 10 members allowed in the group!", "danger")
            return redirect("/add_member")

        # DUPLICATE CHECK
        cur.execute("""
        SELECT * FROM members 
        WHERE mobile=? OR aadhar=?
        """, (mobile, aadhar))

        existing = cur.fetchone()

        if existing:
            conn.close()
            flash("Member with same Mobile or Aadhar already exists!", "danger")
            return redirect("/add_member")

        cur.execute("""
            INSERT INTO members(name,address,mobile,aadhar,bank)
            VALUES(?,?,?,?,?)
        """, (name, address, mobile, aadhar, bank))

        conn.commit()
        conn.close()

        # ---------- SUCCESS ----------
        flash("Member added successfully!", "success")
        return redirect("/add_member")

    return render_template("members/add_member.html")

# --------- EDIT MEMBER ----------
@app.route("/edit_member/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    if request.method == "POST":

        if "user" not in session:
            flash("Login required!", "danger")
            return redirect("/view_member")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"].strip()
        address = request.form["address"].strip()
        mobile = request.form["mobile"].strip()
        aadhar = request.form["aadhar"].strip()
        bank = request.form["bank"].strip()

        # ---------- BLANK CHECK ----------
        if not name or not address or not mobile or not aadhar or not bank:
            flash("All fields are required!", "danger")
            return redirect(request.url)

        # ---------- VALIDATION ----------

        if not re.fullmatch(r"[A-Za-z ]+", name):
            flash("Name must contain only letters", "danger")
            return redirect(request.url)

        if not re.fullmatch(r"[A-Za-z ]+", address):
            flash("Name must contain only letters", "danger")
            return redirect(request.url)

        if not mobile.isdigit() or len(mobile) != 10:
            flash("Mobile number must be 10 digits only", "danger")
            return redirect(request.url)

        if not aadhar.isdigit() or len(aadhar) != 12:
            flash("Aadhar must be 12 digit number", "danger")
            return redirect(request.url)

        if not bank.isdigit() or len(bank) < 9 or len(bank) > 18:
            flash("Bank account must be 9 to 18 digits", "danger")
            return redirect(request.url)

        # ---------- UPDATE ----------
        cur.execute("""
            UPDATE members
            SET name=?, address=?, mobile=?, aadhar=?, bank=?
            WHERE id=?
        """, (name, address, mobile, aadhar, bank, id))

        conn.commit()
        conn.close()

        return redirect("/view_member")

    # ---------- GET MEMBER ----------
    cur.execute("SELECT * FROM members WHERE id=?", (id,))
    member = cur.fetchone()

    conn.close()
    return render_template("members/edit_member.html", member=member)

@app.route("/view_member", methods=["GET"])
def view_member():
    if not is_logged_in():
        return redirect("/login")
    db = get_db()
    q = request.args.get("q")

    if q:
        members = db.execute(
            "SELECT * FROM members WHERE name LIKE ? OR mobile LIKE ?",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        members = db.execute("SELECT * FROM members").fetchall()

    return render_template("members/view_member.html", members=members)

@app.route("/delete_member/<int:id>")
def delete_member(id):
    if not is_admin():
        flash("Only Admin!", "danger")
        return redirect("/view_member")

    conn = sqlite3.connect("shg.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Delete savings
    cur.execute("DELETE FROM savings WHERE member_id=?", (id,))

    # Get loan ids
    loan_ids = cur.execute("SELECT id FROM loans WHERE member_id=?", (id,)).fetchall()

    for loan in loan_ids:
        cur.execute("DELETE FROM emi WHERE loan_id=?", (loan[0],))

    # Delete loans
    cur.execute("DELETE FROM loans WHERE member_id=?", (id,))

    # Finally delete member
    cur.execute("DELETE FROM members WHERE id=?", (id,))

    conn.commit()
    conn.close()
    return redirect("/view_member")

# ---------- SAVINGS ----------
@app.route("/add_saving", methods=["GET", "POST"])
def add_saving():
    if not is_admin():
        flash("Only Admin!", "danger")
        return redirect("/view_saving")

    db = get_db()
    members = db.execute("SELECT id, name FROM members").fetchall()
    error = None

    if request.method == "POST":

        member_id = request.form["member"]
        amount = request.form["amount"]
        date = request.form["date"]

        if not member_id:
            error = "Please select member"

        elif not amount:
            error = "Enter saving amount"

        elif not date:
            error = "Please select date"

        elif float(amount) < 0:
            error = "Saving amount cannot be negative"

        else:
            amount = float(amount)

            # ✅ IMPORTANT: old pending delete (duplicate avoid + auto remove)
            db.execute(
                "DELETE FROM defaulters WHERE member_id=? AND type='pending'",
                (member_id,)
            )

            # ---------- CASE 1 : EXACT 200 ----------
            if amount == 200:

                db.execute(
                    "INSERT INTO savings(member_id, amount, date) VALUES (?,?,?)",
                    (member_id, amount, date)
                )

            # ---------- CASE 2 : MORE THAN 200 ----------
            elif amount > 200:
                extra = amount - 200

                db.execute(
                    "INSERT INTO savings(member_id, amount, date) VALUES (?,?,?)",
                    (member_id, 200, date)
                )

                db.execute(
                    "INSERT INTO defaulters(member_id, type, amount, date) VALUES (?,?,?,?)",
                    (member_id, "extra", extra, date)
                )

            # ---------- CASE 3 : LESS THAN 200 ----------
            elif amount < 200:

                pending = 200 - amount

                db.execute(
                    "INSERT INTO savings(member_id, amount, date) VALUES (?,?,?)",
                    (member_id, amount, date)
                )

                db.execute(
                    "INSERT INTO defaulters(member_id, type, amount, date) VALUES (?,?,?,?)",
                    (member_id, "pending", pending, date)
                )

            db.commit()
            return redirect("/view_saving")

    return render_template("savings/add_saving.html", members=members, error=error)

# ---------- VIEW SAVINGS ----------
@app.route("/view_saving")
def view_saving():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()

    savings = db.execute("""
        SELECT savings.id, members.name, savings.amount, savings.date
        FROM savings
        JOIN members ON members.id = savings.member_id
        ORDER BY savings.date ASC
    """).fetchall()

    #  TOTAL SUM
    total = db.execute("SELECT SUM(amount) FROM savings").fetchone()[0]
    if total is None:
        total = 0

    return render_template("savings/view_saving.html",
                           savings=savings,
                           total=total)
    return render_template("savings/edit_saving.html", saving=saving, members=members)

# ----------EDIT SAVINGS ----------
@app.route("/edit_saving/<int:id>", methods=["GET", "POST"])
def edit_saving(id):
    db = get_db()

    # current saving record
    saving = db.execute(
        "SELECT * FROM savings WHERE id=?",
        (id,)
    ).fetchone()

    if saving is None:
        return "Saving not found"

    # members list
    members = db.execute(
        "SELECT id, name FROM members"
    ).fetchall()

    if request.method == "POST":

        member_id = request.form.get("member")
        amount = request.form.get("amount")
        date = request.form.get("date")

        error = None

        # Validation
        if request.method == "POST":

            member_id = request.form["member"]
            amount = request.form["amount"]
            date = request.form["date"]

            if not member_id:
                error = "Please select member"

            elif not amount:
                error = "Enter saving amount"

            elif not date:
                error = "Please select date"

            elif float(amount) < 0:
                error = "Saving amount cannot be negative"

            else:
                amount = float(amount)

                # CASE 1 : EXACT 200
                if amount == 200:
                    db.execute(
                        "INSERT INTO savings(member_id, amount, date) VALUES (?,?,?)",
                        (member_id, amount, date)
                    )

        if error:
            return render_template(
                "savings/edit_saving.html",
                saving=saving,
                members=members,
                error=error
            )

        # Update saving
        db.execute("""
            UPDATE savings
            SET member_id=?, amount=?, date=?
            WHERE id=?
        """, (member_id, amount, date, id))

        db.commit()

        return redirect("/view_saving")

    return render_template(
        "savings/edit_saving.html",
        saving=saving,
        members=members
    )

# ---------- EDIT SAVINGS ----------
@app.route("/delete_saving/<int:id>")
def delete_saving(id):
    db = get_db()
    db.execute("DELETE FROM savings WHERE id=?", (id,))
    db.commit()
    return redirect("/view_saving")

# ---------- BANK LOAN APPLY ----------
@app.route("/bank_loan", methods=["GET","POST"])
def bank_loan():

    db = get_db()

    if request.method == "POST":

        apply_date = request.form.get("apply_date")
        purpose = request.form.get("purpose", "").strip()
        bank_name = request.form.get("bank_name")
        group_name = request.form.get("group_name")

        adhyaksh_file = request.files.get("adhyaksh_proof_file")
        sachiv_file = request.files.get("sachiv_proof_file")

        errors = []

        if not apply_date or not purpose:
            errors.append("All fields required")

        if not adhyaksh_file or adhyaksh_file.filename == "":
            errors.append("Upload Adhyaksh file")

        if not sachiv_file or sachiv_file.filename == "":
            errors.append("Upload Sachiv file")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect("/bank_loan")

        # Save files
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        adhyaksh_filename = secure_filename(adhyaksh_file.filename)
        sachiv_filename = secure_filename(sachiv_file.filename)

        adhyaksh_file.save(os.path.join(UPLOAD_FOLDER, adhyaksh_filename))
        sachiv_file.save(os.path.join(UPLOAD_FOLDER, sachiv_filename))

        # Insert
        db.execute("""
            INSERT INTO bank_loan
            (bank_name, group_name, purpose, apply_date, adhyaksh_file, sachiv_file)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bank_name, group_name, purpose, apply_date,
              adhyaksh_filename, sachiv_filename))

        db.commit()

        flash("Loan Applied Successfully!", "success")
        return redirect("/view_bank_loan")

    return render_template("bank_loan/bank_loan.html")

# ---------- VIEW BANK LOAN ----------
@app.route("/view_bank_loan")
def view_bank_loan():
    db = get_db()

    # Fetch all loans
    loans = db.execute("SELECT * FROM bank_loan").fetchall()

    loan_list = []
    for loan in loans:
        # Fetch member proofs for this loan
        proofs = db.execute("""
            SELECT mlp.*, m.name AS member_name
            FROM member_loan_proofs mlp
            JOIN members m ON mlp.member_id = m.id
            WHERE mlp.loan_id = ?
        """, (loan["id"],)).fetchall()

        loan_dict = dict(loan)
        loan_dict["proofs"] = proofs
        loan_list.append(loan_dict)

    return render_template("bank_loan/view_bank_loan.html", loans=loan_list)

# ---------- DELETE BANK LOAN ----------
@app.route("/delete_bank_loan/<int:id>")
def delete_bank_loan(id):

    db = get_db()

    db.execute(
        "DELETE FROM bank_loan WHERE id=?",
        (id,)
    )
    db.commit()
    db.close()

    return redirect("/view_bank_loan")

#---------- BANK LOAN ----------
@app.route("/add_loan", methods=["GET", "POST"])
def add_loan():
    if not is_admin():
        flash("Only Admin!", "danger")
        return redirect("/view_loan")

    db = get_db()
    db.row_factory = sqlite3.Row

    members = db.execute(
        "SELECT id, name FROM members"
    ).fetchall()

    if request.method == "POST":

        member_id = request.form["member"]
        amount = float(request.form["amount"])
        rate = float(request.form["rate"])
        months = int(request.form["months"])

        approval_date = request.form.get("approval_date")

        # Validation
        if amount <= 0 or rate < 0 or months <= 0:
            return "Invalid Data"

        # Interest Calculation
        total_interest = (amount * rate * months) / 100
        total_amount = amount + total_interest
        emi_amount = round(total_amount / months, 2)

        cur = db.cursor()

        cur.execute("""
            INSERT INTO loans
            (member_id, amount, rate, months, emi, approval_date)
            VALUES (?, ?, ?, ?, ?,?)
        """, (
            member_id,
            amount,
            rate,
            months,
            emi_amount,
            approval_date
        ))

        loan_id = cur.lastrowid

        for m in range(1, months + 1):
            db.execute("""
                INSERT INTO emi(loan_id, month, emi_amount, status)
                VALUES (?, ?, ?, 'Pending')
            """, (loan_id, m, emi_amount))

        db.commit()
        db.close()

        return redirect(url_for("view_loan"))

    db.close()
    return render_template(
        "loans/add_loan.html",
        members=members
    )

# ---------- VIEW LOANS ----------
@app.route("/view_loan")
def view_loan():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()

    loans = db.execute("""
        SELECT loans.id,
               members.name,
               loans.amount,
               loans.rate,
               loans.months,
               loans.emi,
               loans.approval_date
        FROM loans
        JOIN members ON members.id = loans.member_id
        ORDER BY loans.id ASC
    """).fetchall()

    return render_template("loans/view_loan.html", loans=loans)

# ---------- LOANS Session  ----------
@app.route("/bank_session")
def bank_session():

    db = get_db()

    sessions = db.execute("""
    SELECT * FROM bank_session
    """).fetchall()

    db.close()

    return render_template(
        "loans/bank_session.html",
        sessions=sessions
    )

# ---------- EMI LIST ----------
@app.route("/emi_list")
def emi_list():
    db = get_db()
    db.row_factory = sqlite3.Row

    current_month = datetime.now().month

    emi_data = db.execute("""
        SELECT emi.id, members.name, emi.emi_amount, emi.status, emi.month
        FROM emi
        JOIN loans ON emi.loan_id = loans.id
        JOIN members ON loans.member_id = members.id
        WHERE emi.month = ?
        ORDER BY emi.id ASC
    """, (current_month,)).fetchall()

    # Paid EMI total
    paid_total = db.execute("""
        SELECT SUM(emi_amount)
        FROM emi
        WHERE status='Paid' AND month=?
    """,(current_month,)).fetchone()[0] or 0

    # Pending EMI total
    pending_total = db.execute("""
        SELECT SUM(emi_amount)
        FROM emi
        WHERE status='Pending' AND month=?
    """,(current_month,)).fetchone()[0] or 0

    db.close()

    return render_template(
        "emi/emi_list.html",
        emi_data=emi_data,
        paid_total=paid_total,
        pending_total=pending_total
    )

# ---------- PAY EMI ----------
@app.route("/pay_emi/<int:emi_id>")
def pay_emi(emi_id):
    db = get_db()

    db.execute("""
        UPDATE emi
        SET status='Paid'
        WHERE id = ?
    """, (emi_id,))

    db.commit()
    db.close()
    return redirect(url_for("emi_list",))

# ---------- PAID EMI ----------
@app.route("/paid_emi")
def paid_emi():
    db = get_db()
    db.row_factory = sqlite3.Row

    # current month number (1–12)
    current_month = datetime.now().month

    paid_list = db.execute("""
        SELECT emi.id, members.name, emi.emi_amount, emi.month
        FROM emi
        JOIN loans ON emi.loan_id = loans.id
        JOIN members ON loans.member_id = members.id
        WHERE emi.status='Paid'
        AND emi.month = ?
        ORDER BY emi.id ASC
    """, (current_month,)).fetchall()

    # Total Paid EMI (only current month)
    total_paid = db.execute("""
        SELECT SUM(emi_amount)
        FROM emi
        WHERE status='Paid' AND month=?
    """, (current_month,)).fetchone()[0] or 0

    db.close()

    return render_template(
        "emi/paid_emi.html",
        paid_list=paid_list,
        current_month=current_month,
        total_paid=total_paid
    )

# ---------- DEFAULTERS -----------
@app.route("/defaulters")
def defaulters():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()
    db.row_factory = sqlite3.Row

    current_month = datetime.now().month

    # EMI Defaulters
    emi_defaulters = db.execute("""
        SELECT members.name,
               emi.month,
               emi.emi_amount,
               emi.status
        FROM emi
        JOIN loans ON emi.loan_id = loans.id
        JOIN members ON loans.member_id = members.id
        WHERE emi.status = 'Pending'
        AND emi.month = ?
    """, (current_month,)).fetchall()

    # Saving Defaulters
    saving_pending = db.execute("""
        SELECT members.name, defaulters.amount, defaulters.date
        FROM defaulters
        JOIN members ON members.id = defaulters.member_id
        WHERE defaulters.type = 'pending'
    """).fetchall()

    db.close()

    return render_template(
        "defaulters.html",
        emi_defaulters=emi_defaulters,
        saving_pending=saving_pending
    )

# ---------- REPORTS -----------
@app.route("/reports")
def reports():
    db = get_db()

    # ---------- TOTALS ----------
    total_saving = db.execute("SELECT SUM(amount) FROM savings").fetchone()[0] or 0
    total_member_loan = db.execute("SELECT SUM(amount) FROM loans").fetchone()[0] or 0
    total_bank_loan = db.execute("SELECT SUM(loan_amount) FROM bank_session").fetchone()[0] or 0

    # ---------- MEMBER WISE REPORT ----------
    member_report = db.execute("""
        SELECT members.name,
               IFNULL(SUM(savings.amount),0) as total_saving,
               IFNULL(SUM(loans.amount),0) as total_loan
        FROM members
        LEFT JOIN savings ON savings.member_id = members.id
        LEFT JOIN loans ON loans.member_id = members.id
        GROUP BY members.id
    """).fetchall()

    # ---------- MONTHLY REPORT ----------
    monthly_report = db.execute("""
        SELECT strftime('%Y', date) as year,
               strftime('%m', date) as month,
               SUM(amount) as total_saving
        FROM savings
        WHERE date IS NOT NULL
        GROUP BY year, month
        ORDER BY year DESC, month DESC
    """).fetchall()

    # Extra Saving Members
    extra_saving = db.execute("""
            SELECT members.name, defaulters.amount, defaulters.date
            FROM defaulters
            JOIN members ON members.id = defaulters.member_id
            WHERE defaulters.type = 'extra'
        """).fetchall()

    # ---------- PROFIT / LOSS ----------
    total_interest = db.execute("""
        SELECT SUM((amount * rate * months)/100)
        FROM loans
    """).fetchone()[0] or 0

    profit_loss = (total_interest + total_bank_loan) - (total_saving + total_member_loan)
    db.close()

    return render_template(
        "reports/reports.html",
        saving=total_saving,
        loan=total_member_loan,
        bank_loan=total_bank_loan,
        member_report=member_report,
        monthly_report=monthly_report,
        profit_loss=profit_loss,
        extra_saving=extra_saving
    )

# ---------- ADD BUSINESS ----------
@app.route("/add_business", methods=["GET","POST"])
def add_business():

    if request.method == "POST":
        group_name = request.form["group_name"]
        business_name = request.form["business_name"]
        investment = float(request.form["investment"])
        total_income = float(request.form["total_income"])
        total_expense = float(request.form["total_expense"])
        start_date = request.form["start_date"]

        db = get_db()
        db.execute("""
            INSERT INTO business
            (group_name, business_name, investment, total_income, total_expense, start_date)
            VALUES (?,?,?,?,?,?)
        """,(group_name,business_name,investment,total_income,total_expense,start_date))
        db.commit()

        return redirect(url_for("view_business"))

    return render_template("business/add_business.html")

# ---------- VIEW BUSINESS ----------
@app.route("/view_business")
def view_business():
    db = get_db()
    data = db.execute("SELECT * FROM business").fetchall()

    business_list = []
    total_profit = 0

    for row in data:
        profit_loss = row["total_income"] - row["total_expense"]
        total_profit += profit_loss

        business_list.append({
            "id": row["id"],
            "group_name": row["group_name"],
            "business_name": row["business_name"],
            "investment": row["investment"],
            "total_income": row["total_income"],
            "total_expense": row["total_expense"],
            "profit_loss": profit_loss,
            "start_date": row["start_date"]
        })

    return render_template(
        "business/view_business.html",
        business=business_list,
        total_profit=total_profit
    )

# ---------- DELETE BUSINESS ----------
@app.route("/delete_business/<int:id>")
def delete_business(id):
    db = get_db()
    db.execute("DELETE FROM business WHERE id=?", (id,))
    db.commit()
    return redirect(url_for("view_business"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)

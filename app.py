from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "my_secret_key"   # required for login sessions

# Initialize database
def init_db():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  roll_no TEXT,
                  course TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")
@app.route('/view')
def view_students():
    if "user" not in session:
        return redirect(url_for("login"))

    query = request.args.get("query")
    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    if query:
        c.execute("SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? OR course LIKE ?", 
                  ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    else:
        c.execute("SELECT * FROM students")

    students = c.fetchall()
    conn.close()
    return render_template("view.html", students=students, query=query)

@app.route('/delete/<int:id>')
def delete_student(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_students"))
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        course = request.form.get("course", "").strip()

        if not name or not roll_no or not course:
            return render_template("edit.html", error="All fields are required.", student=(id, name, roll_no, course))

        # prevent duplicate roll numbers (except for current student)
        # Validation: Duplicate roll number, name, or course (excluding current record)
        c.execute("SELECT * FROM students WHERE (roll_no=? OR name=? OR course=?) AND id<>?", (roll_no, name, course, id))
        existing = c.fetchone()
        if existing:
            conn.close()
            return render_template("edit.html", error="Student with same Name, Roll No, or Course already exists!", student=(id, name, roll_no, course))
        # update record
        c.execute("UPDATE students SET name=?, roll_no=?, course=? WHERE id=?", (name, roll_no, course, id))
        conn.commit()
        conn.close()
        return redirect(url_for("view_students"))

    else:
        c.execute("SELECT * FROM students WHERE id=?", (id,))
        student = c.fetchone()
        conn.close()
        return render_template("edit.html", student=student)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Simple fixed credentials (you can later improve with DB)
        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))
@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        course = request.form.get("course", "").strip()

        # Validation: Empty fields
        if not name or not roll_no or not course:
            return render_template("add.html", error="All fields are required.")

        conn = sqlite3.connect("students.db")
        c = conn.cursor()

        # Validation: Duplicate roll number
        c.execute("SELECT * FROM students WHERE roll_no=? OR name=? OR course=?", (roll_no, name, course))
        existing = c.fetchone()
        if existing:

            conn.close()
            return render_template("add.html", error="Student with same Name, Roll No, or Course already exists!")
        # Insert new record
        c.execute("INSERT INTO students (name, roll_no, course) VALUES (?, ?, ?)", (name, roll_no, course))
        conn.commit()
        conn.close()
        return redirect(url_for("view_students"))

    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)

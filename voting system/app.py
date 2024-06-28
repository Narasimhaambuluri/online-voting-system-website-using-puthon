from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = "narasimha"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "lakshmireddy"
app.config["MYSQL_DB"] = "election"

mysql = MySQL(app)


@app.route("/register", methods=["GET", "POST"])
def register():
    if (
        request.method == "POST"
        and "student_id" in request.form
        and "roll_no" in request.form
        and "password" in request.form
    ):
        student_id = request.form["student_id"]
        roll_no = request.form["roll_no"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        existing_student = cursor.fetchone()

        if existing_student:
            flash("You are already registered with this roll number!")
            return redirect(url_for("register"))
        cursor.execute(
            "INSERT INTO students (student_id, roll_no,password) VALUES (%s, %s, %s)",
            (student_id, roll_no, password),
        )
        mysql.connection.commit()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if (
        request.method == "POST"
        and "student_id" in request.form
        and "password" in request.form
    ):
        student_id = request.form["student_id"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM students WHERE student_id = %s AND password = %s",
            (student_id, password),
        )
        student = cursor.fetchone()

        if student:
            session["loggedin"] = True
            session["id"] = student["id"]
            session["student_id"] = student["student_id"]
            return redirect(url_for("vote"))
        else:
            flash("Incorrect Student ID or Password!")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        student_id = session["id"]

        cursor.execute("SELECT * FROM votes WHERE student_id = %s", (student_id,))
        vote_record = cursor.fetchone()

        if vote_record:
            return render_template("already_voted.html")

        cursor.execute("SELECT * FROM candidates")
        candidates = cursor.fetchall()

        if request.method == "POST" and "candidate_id" in request.form:
            candidate_id = request.form["candidate_id"]

            cursor.execute(
                "INSERT INTO votes (student_id, candidate_id) VALUES (%s, %s)",
                (student_id, candidate_id),
            )
            mysql.connection.commit()
            return render_template("vote_success.html")

        return render_template("vote.html", candidates=candidates)
    return redirect(url_for("login"))


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if (
        request.method == "POST"
        and "admin_id" in request.form
        and "password" in request.form
    ):
        admin_id = request.form["admin_id"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM admin WHERE admin_id = %s AND password = %s",
            (admin_id, password),
        )
        admin = cursor.fetchone()

        if admin:
            session["admin_loggedin"] = True
            session["admin_id"] = admin["admin_id"]
            return redirect(url_for("results"))
        else:
            flash("Incorrect Admin ID or Password!")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_loggedin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin_login"))


@app.route("/results")
def results():
    if "admin_loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT candidates.name, COALESCE(COUNT(votes.id), 0) AS vote_count FROM candidates LEFT JOIN votes ON candidates.id = votes.candidate_id GROUP BY candidates.id"
        )
        results = cursor.fetchall()
        return render_template("results.html", results=results)
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(debug=True)

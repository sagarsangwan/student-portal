import re
from flask import Flask, render_template, request, make_response, send_file
import json
import os
from flask_mysqldb import MySQL
import difflib
from difflib import get_close_matches


app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "sagar"
app.config["MYSQL_PASSWORD"] = "password"
app.config["MYSQL_DB"] = "student-portal"

mysql = MySQL(app)


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT JSON_ARRAYAGG(JSON_OBJECT('id', ID, 'course_name', course_name, 'course_desc', course_desc)) FROM courses")
        table = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template("pages/home.html", value=json.loads(table[0][0]))
    elif request.method == 'POST':
        search = request.form['search']
        cur = mysql.connection.cursor()
        cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" +
                    search + "%'OR subject_desc LIKE '%" + search + "%'OR subject_alt_name LIKE '%" + search + "%'")
        result = cur.fetchall()
        if len(result) > 0:
            print(result)
            return render_template("pages/search.html", value=result)
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT subject_name, subject_desc FROM subjects ")
            subject = cur.fetchall()
            subject = list(subject)
            match = []
            for i in subject:
                match.extend(list(i))
            print(match)
            search = request.form['search']
            matches = get_close_matches(search, match)

            if len(matches) > 0:
                a = matches[0]
                cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" +
                            a + "%'OR subject_desc LIKE '%" + a + "%'OR subject_alt_name LIKE '%" + a + "%'")
                sub = cur.fetchall()
                print(sub)
                return render_template("pages/search.html", value=sub)


@app.route("/course/<id>", methods=['GET', 'POST'])
def courses(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT subjects_ids FROM course_to_subjets WHERE course_id ="+id)
        subjects = cur.fetchall()[0][0]
        # subjects = sub.split(",")
        # subjects = subjects[0]
        print(subjects)
        cur.execute(
            "SELECT course_name, course_desc FROM courses WHERE id ="+id)
        header_courses = cur.fetchall()
        header_courses = header_courses[0]
        header_courses = list(header_courses)
        cur.execute(
            "SELECT id, subject_name, subject_desc FROM subjects WHERE id IN (" + subjects + ")")
        s = cur.fetchall()
        return render_template("pages/courses.html", header=header_courses, s1=s,  subject=subjects)
    elif request.method == 'POST':
        global search1
        search1 = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT subjects_ids FROM course_to_subjets WHERE course_id ="+id)
        subject = cur.fetchall()
        subject = subject[0][0]
        print(subject)
        cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE (subject_name LIKE '%" + search1 +
                    "%'OR subject_desc LIKE '%" + search1 + "%'OR subject_alt_name LIKE '%" + search1 + "%') AND id IN " + subject)
        sub = cur.fetchall()

        if len(sub) > 0:
            print(sub)
            return render_template("pages/search.html", value=sub)
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT subject_name, subject_desc FROM subjects ")
            subject = cur.fetchall()
            subject = list(subject)
            match = []
            for i in subject:
                match.extend(list(i))
            search = request.form['search']
            matches = get_close_matches(search, match)

            if len(matches) > 0:
                a = matches[0]
                cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" +
                            a + "%'OR subject_desc LIKE '%" + a + "%'OR subject_alt_name LIKE '%" + a + "%'")
                sub = cur.fetchall()
                return render_template("pages/search.html", value=sub)


@app.route("/subject/<id>", methods=['GET', 'POST'])
def subject(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT subject_name, subject_desc, id FROM subjects WHERE id IN (" + id + ")")
        subject_head = cur.fetchall()
        subject_head = subject_head[0]
        return render_template("pages/subject.html", subject_head1=subject_head, id1=id)


@app.route("/Dashboard", methods=["GET", "POST"])
def Dashboard():
    if request.method == "POST":
        details = request.form
        user_name = details["user_name"]
        password = details["password"]
        if user_name == "sagarsangwan" and password == "password1":
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, user_name, email, messages FROM messages")
            result = cur.fetchall()
            return render_template("pages/Login.html", value=result)
        else:
            return render_template("pages/Dashboard.html", info="wrong user_name or password")
    return render_template("pages/Dashboard.html")


FILE_EXTENSION = ["PDF"]


@app.route("/add_data", methods=["GET", "POST"])
def add_data():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, subject_name FROM subjects")
    subject = cur.fetchall()
    cur.execute("SELECT id, course_name FROM courses")
    courses = cur.fetchall()
    if request.method == "GET":
        cur.close()
        return render_template("pages/add_data.html", subject=subject, courses=courses)
    elif request.method == "POST":
        course_name = request.form.getlist("course_name")
        subject_name = request.form.get("subject_name1")
        data = request.files["data"]
        name = data.filename
        ext = name.split(".")
        # data.save(data.filename)
        # os.remove(name)
        cur.close()
        try:
            if not course_name:
                raise Exception("Please select course name")
            elif not subject_name:
                raise Exception("Pease select subjects ")
            elif ext[-1].upper() not in FILE_EXTENSION:
                raise Exception("File type must be a pdf")

            return render_template("pages/add_data.html",  subject=subject, courses=courses, info="Thanku for adding")
        except Exception as error:
            print(error)
            return render_template("pages/add_data.html",  subject=subject, courses=courses, error=error)


@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if request.method == "POST":
        details = request.form
        names = details["name"]
        emails = details["email"]
        messages = details["message"]
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages(user_name, email, messages) values(%s, %s, %s)",
                    (names, emails, messages))
        mysql.connection.commit()
        cur.close()
        return render_template("pages/feedback.html", info="message sent sucessfully")
    return render_template("pages/feedback.html")


@app.route("/subject_detail/<id>")
def subject_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT question_papers FROM subjects WHERE id ="+id)
    sub_name = cur.fetchall()[0][0]
    print((sub_name))
    cur.execute(
        "SELECT link, year FROM question_paper WHERE id =" + sub_name)
    detail = cur.fetchall()[0]
    print(list(detail))

    detail = list(detail)
    # detail = detail[0]
    # d = []
    # for i in detail:
    #     d.append(i[0])
    # print(d)

    return render_template("pages/subject_detail.html", value=detail)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/404.html"), 400


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("pages/500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)

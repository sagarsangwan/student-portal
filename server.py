from logging import debug, info
import re
from io import BytesIO
from MySQLdb import Binary
import base64
from MySQLdb.cursors import Cursor
from flask import Flask, render_template, request, make_response, send_file
import json
import os
from flask.wrappers import Response
from flask_mysqldb import MySQL
import difflib
from difflib import get_close_matches

# from werkzeug.utils import send_file

app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "admin"
app.config["MYSQL_DB"] = "users"

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
        subjects = cur.fetchall()
        subjects = subjects[0][0]
        cur.execute(
            "SELECT course_name, course_desc FROM courses WHERE id ="+id)
        header_courses = cur.fetchall()
        header_courses = header_courses[0]
        header_courses = list(header_courses)
        cur.execute(
            "SELECT id, subject_name, subject_desc FROM subjects WHERE id IN " + subjects)
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


@app.route("/add_data", methods=["GET", "POST"])
def add_data():
    if request.method == "GET":
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, subject_name FROM subjects")
        subject = cur.fetchall()
        cur.execute("SELECT id, course_name FROM courses")
        courses = cur.fetchall()
        return render_template("pages/add_data.html", subject=subject, courses=courses)
    elif request.method == "POST":
        course_name = request.form.getlist("course_name")
        subject_name = request.form["subject_name1"]
        data = request.files["data"]
        data.save(data.filename)
        data = data.read()
        # print( data.read())
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user_data(Course_name, subject_name, user_data) values(%s, %s, %s)",(course_name, subject_name, data))
        # name = data.filename
        # os.remove(name)
        cur.execute("SELECT id, subject_name FROM subjects")
        subject = cur.fetchall()
        cur.execute("SELECT id, course_name FROM courses")
        courses = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template("pages/add_data.html", subject=subject, courses=courses, info="Thanku for adding")


@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if request.method == "POST":
        details = request.form
        names = details["name"]
        emails = details["email"]
        messages = details["message"]
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages(user_name, email, messages) values(%s, %s, %s)",(names, emails, messages))
        mysql.connection.commit()
        cur.close()
        return render_template("pages/feedback.html", info="message sent sucessfully")
    return render_template("pages/feedback.html")


@app.route("/subject_detail/<id>")
def subject_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM user_data ")
    detail = cur.fetchall()
    detail = list(detail)
    # detail = detail[0][0]
    d = []
    for i in detail:
        d.append(i[0])
    print(d)
    print(detail)

    return render_template("pages/subject_detail.html", value=d)


@app.route("/download/<id>")
def download(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_data FROM user_data")
    result1 = cur.fetchall()
    # name = result1.filename
    result = result1[0][0]
    result_bytes = BytesIO(result1)
    print(result)
    # binary_data = base64.b64decode(result)
    # bi = base64.b64decode(binary_data)
    # response = make_response(result[0][0])
    # response.headers['Content-Type'] = 'application/pdf'
    # response.headers['Content-Disposition'] = \
    #     'inline; filename=%s.pdf' % 'yourfilename'
    # return response
    # return send_file(
    #     result_bytes,
    #     mimetype='application/pdf',
    #     as_attachment=True,
    #     download_name='w.pdf'
    # )
    return send_file(result_bytes, as_attachment=True, download_name="test.jpg")
@app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/404.html")

if __name__ == "__main__":
    app.run(debug=True)

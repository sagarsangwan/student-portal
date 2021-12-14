from logging import info
import re
from flask import Flask, render_template, request
import json
import os
from flask_mysqldb import MySQL
app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "admin"
app.config["MYSQL_DB"] = "users"

mysql = MySQL(app)


@app.route("/", methods = ['GET', 'POST'])
def home():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT JSON_ARRAYAGG(JSON_OBJECT('id', ID, 'course_name', course_name, 'course_desc', course_desc)) FROM courses")
        table = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template("pages/home.html", value = json.loads(table[0][0]))
    else:
        return render_template("pages/search.html")


@app.route("/course/<id>", methods = ['GET', 'POST'])
def courses(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT subjects_ids FROM course_to_subjets WHERE course_id ="+id)
        subjects = cur.fetchall()
        subjects = subjects[0][0]
        #subjects = subjects.split(",")
        cur.execute("SELECT course_name, course_desc FROM courses WHERE id ="+id)
        header_courses = cur.fetchall()
        header_courses = header_courses[0]
        header_courses = list(header_courses)
        cur.execute("SELECT id, subject_name, subject_desc FROM subjects WHERE id IN " + subjects)
        s = cur.fetchall()
        return render_template("pages/courses.html", header = header_courses, s1 = s,  subject = subjects)
    elif request.method == 'POST':
        global search1
        search1 = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" + search1 + "%'OR subject_desc LIKE '%" + search1 + "%'OR subject_alt_name LIKE '%" + search1 + "%'")
        sub = cur.fetchall()
        if len(sub) > 0:
            print(sub)
            return render_template("pages/search.html", value = sub)
        else:
            return render_template("pages/nothing.html")
        
        



@app.route("/subject/<id>", methods = ['GET', 'POST'])
def subject(id):
    if request.method == 'GET':            
        cur = mysql.connection.cursor()
        cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE id IN ("+ id +")")
        subject_head = cur.fetchall()
        subject_head = subject_head[0]
        return render_template("pages/subject.html", subject_head1 = subject_head)
    



@app.route("/search_result")
def search():
    return render_template("pages/search.html")

@app.route("/feedback", methods = ['GET', 'POST'])
def feedback():
    if request.method == "POST":
        details = request.form
        names  = details["name"]
        emails = details["email"]
        messages = details["message"]
        cur = mysql.connection.cursor()
        cur.execute ("INSERT INTO user(name, email, message) values(%s, %s, %s)", (names, emails, messages))
        mysql.connection.commit()
        cur.close()
        return render_template("pages/feedback.html", info = "message sent sucessfully")
    return render_template("pages/feedback.html")


if __name__ == "__main__":
    app.run(debug=True)




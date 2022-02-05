from flask import Flask, render_template, request, make_response, send_file, redirect
import os
import secrets
import json
import requests
import re
import difflib
from flask_mysqldb import MySQL
from difflib import get_close_matches
from dotenv import load_dotenv
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http

app = Flask(__name__)
app.config["MYSQL_HOST"] = os.environ.get('MYSQL_HOST')
app.config["MYSQL_USER"] = os.environ.get('MYSQL_USER')
app.config["MYSQL_PASSWORD"] = os.environ.get('MYSQL_PASSWORD')
app.config["MYSQL_DB"] = os.environ.get('MYSQL_DB')

load_dotenv('.env')
mysql = MySQL(app)

# sanitize user input. i hope this helps from SQL injection attacks


def clean(string):
    clean_string = ""
    valid_character = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL@MNOPQRSTUVWXYZ1234567890 ,.!?()[]{}<>\\/'
    for char in string:
        if char.isalnum() or char in valid_character:
            clean_string += char
    return clean_string


default_user_id = ""


def generate_session_id():
    global default_user_id
    default_user_id = secrets.token_hex(16)
    return default_user_id


credentials = None
service = None


def getDriveCredentials():
    scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]
    keyfile_dict = os.environ.get(
        "API_SERVICE_ID")
    keyfile_dict = json.loads(keyfile_dict)

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        keyfile_dict, scopes=scopes)

    return credentials

# login to google drive and get drive service object which i will use later to upload and get urls


def getDriveService(credentials):
    http_auth = credentials.authorize(Http())
    service = build("drive", "v3", http=http_auth)

    return service


@app.route("/", methods=['GET'])
def home():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT ID, course_name, course_desc FROM courses")
    table = cur.fetchall()
    mysql.connection.commit()
    cur.close()

    return render_template("pages/home.html", value=list(table))


@app.route("/search")
def search():
    search = request.args.get('search')
    search = clean(search)
    try:
        if not search:
            raise Exception("please enter a valid subject name")
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" +
                        search + "%'OR subject_desc LIKE '%" + search + "%'OR subject_alt_name LIKE '%" + search + "%'")
            result = cur.fetchall()
            if len(result) > 0:
                return render_template("pages/search.html", value=result, search=search)
            else:
                cur = mysql.connection.cursor()
                cur.execute(
                    "SELECT subject_name, subject_desc id FROM subjects ")
                subject = cur.fetchall()
                subject = list(subject)
                match = []
                for i in subject:
                    match.extend(list(i))
                matches = get_close_matches(search, match)
                if len(matches) > 0:
                    a = matches[0]
                    cur.execute("SELECT subject_name, subject_desc, id FROM subjects WHERE subject_name LIKE '%" +
                                a + "%'OR subject_desc LIKE '%" + a + "%'OR subject_alt_name LIKE '%" + a + "%'")
                    sub = cur.fetchall()
                    return render_template("pages/search.html", value=sub, search=search)
                else:
                    return render_template("pages/search.html", search=search)
    except Exception as error:
        return render_template("pages/search.html", error=error)


@app.route("/course/<id>", methods=['GET', 'POST'])
def courses(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT subjects_ids FROM course_to_subjets WHERE course_id ="+id)
        subjects = cur.fetchall()[0][0]
        cur.execute(
            "SELECT course_name, course_desc FROM courses WHERE id ="+id)
        header_courses = cur.fetchall()
        header_courses = header_courses[0]
        cur.execute(
            "SELECT id, subject_name, subject_desc FROM subjects WHERE id IN (" + subjects + ")")
        s = cur.fetchall()
        return render_template("pages/courses.html", header=list(header_courses), s1=s,  subject=subjects)


@app.route("/subject/<id>", methods=['GET'])
def subject(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT subject_name, subject_desc, id FROM subjects WHERE id IN (" + id + ")")
        subject_head = cur.fetchall()
        cur.execute(
            "SELECT qp_link FROM qp_links WHERE id ="+id)
        detail = cur.fetchall()[0][0]
        detail = detail.replace("\'", "\"")

        detail = json.loads(detail)
        cur.close()
        # the code below is used for getting year of paper like from 2012 to 2019 is (2012-2019)
        if detail == {}:
            year = ""
        else:
            start = list(detail.keys())[-1]
            start = list(start.split(" "))
            length = len(start)
            start = (start[length-1])
            last = list(detail.keys())[0]
            last = list(last.split(" "))
            length = len(last)
            last = last[length-1]

            year = "("+start+" - "+last+")"

        return render_template("pages/subject.html", subject_head1=subject_head[0], id1=id, year=year)


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
        file_name = data.filename
        ext = file_name.split(".")

        try:
            if not data:
                raise Exception("Please select a pdf file")
            if not course_name:
                raise Exception("Please select course name")
            elif not subject_name:
                raise Exception("Please select subjects ")
            elif ext[-1].upper() not in FILE_EXTENSION:
                raise Exception("File type must be a pdf")
            else:
                data.save(file_name)
                file_metadata = {
                    'name': file_name,
                    'parents': ["1OinSd5vgKsTMEmUvAxejgLZC4EgqfJAk"],
                    'mimeType': 'application/pdf'
                }
                media = MediaFileUpload(file_name, resumable=True)
                file = service.files().create(body=file_metadata,
                                              media_body=media, fields='id,name').execute()
                file_id = file.get("id")
                request_body = {
                    'role': 'reader',
                    'type': 'anyone'
                }
                response_permission = service.permissions().create(
                    fileId=file_id,
                    body=request_body
                ).execute()

                response_sharelink = service.files().get(
                    fileId=file_id,
                    fields="webViewLink"
                ).execute()
                link = response_sharelink.get("webViewLink")
                os.remove(file_name)
                for c_name in course_name:
                    cur.execute("INSERT INTO user_data(course_name, subject_name, user_data) values(%s, %s, %s)", (
                        c_name, subject_name, str(link)))
            mysql.connection.commit()
            cur.close()

            return render_template("pages/add_data.html",  subject=subject, courses=courses, info="Thanku for adding")
        except Exception as error:
            return render_template("pages/add_data.html",  subject=subject, courses=courses, error=error)


@ app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if request.method == "POST":
        details = request.form
        names = details["name"]
        names = clean(names)
        emails = details["email"]
        messages = details["message"]
        messages = clean(messages)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages(user_name, email, messages) values(%s, %s, %s)",
                    (names, emails, messages))
        mysql.connection.commit()
        cur.close()
        return render_template("pages/feedback.html", info="message sent sucessfully")
    return render_template("pages/feedback.html")


@ app.route("/question-paper/<id>")
def questionpaper(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT question_papers FROM subjects WHERE id ="+id)
    sub_name = cur.fetchall()[0][0]
    cur.execute(
        "SELECT qp_link FROM qp_links WHERE id ="+sub_name)
    detail = cur.fetchall()[0][0]
    detail = detail.replace("\'", "\"")
    detail.replace("downloads", "downloader")

    detail = json.loads(detail)
    cur.close()
    if detail == {}:
        year = "()"
        error = "not found"
    else:
        year = list(detail.keys())[-1] + "-"+list(detail.keys())[0]

    return render_template("pages/question-paper.html", detail=detail, year=year)


@ app.route("/subject_detail/<id>")
def subject_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT question_papers FROM subjects WHERE id ="+id)
    sub_name = cur.fetchall()[0][0]
    cur.execute(
        "SELECT link, year FROM question_paper WHERE id =" + sub_name)
    detail = cur.fetchall()[0]
    return render_template("pages/subject_detail.html", value=list(detail))


@ app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        user_id = request.cookies.get('session_id')
        if user_id and default_user_id and user_id == default_user_id:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, user_name, email, messages FROM messages")
            result = cur.fetchall()
            cur.execute(
                "SELECT * FROM user_data")
            data = cur.fetchall()
            cur.close()
            return render_template("pages/dashboard.html", value=result, data=data)
        else:
            return redirect("/login")


@ app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        user_id = request.cookies.get('session_id')
        if user_id and default_user_id and user_id == default_user_id:

            return redirect("/dashboard")
        else:
            return render_template("pages/login.html")
    elif request.method == 'POST':
        user_name = request.form["username"]
        password = request.form["password"]

        if user_name == os.environ.get('DASHBOARD_USER_NAME') and password == os.environ.get('DASHBOARD_PASSWORD'):
            response = make_response(redirect('/dashboard'))
            response.set_cookie('session_id', generate_session_id())
            return response
        else:
            return render_template("pages/login.html", info="wrong user_name or password")


@ app.route("/logout")
def logout():
    response = make_response(redirect('/dashboard'))
    response.set_cookie('session_id', "")
    global default_user_id
    default_user_id = ""

    return response


@ app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/404.html"), 400


@ app.errorhandler(500)
def internal_server_error(e):
    return render_template("pages/500.html"), 500


if __name__ == "__main__":
    credentials = getDriveCredentials()
    service = getDriveService(credentials)

    app.run(debug=True)

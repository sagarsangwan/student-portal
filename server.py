from logging import info
from flask import Flask, render_template, request
import os
from flask_mysqldb import MySQL
app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "admin"
app.config["MYSQL_DB"] = "users"

mysql = MySQL(app)


@app.route("/")
def home():
    return render_template("pages/home.html")

@app.route("/courses")
def cse():
    return render_template("pages/courses.html")

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
        return "success"
    return render_template("pages/feedback.html", info = "message sent sucessfully")


if __name__ == "__main__":
    app.run(debug=True)




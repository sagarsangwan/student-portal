from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("pages/home.html")

@app.route("/courses")
def cse():
    return render_template("pages/courses.html")

@app.route("/feedback")
def feedback():
    return render_template("pages/feedback.html")


if __name__ == "__main__":
    app.run(debug=True)




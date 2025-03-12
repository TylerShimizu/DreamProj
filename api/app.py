import os
from flask import Flask, render_template, redirect

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.static_folder = "static"
basedir = os.path.abspath(os.path.dirname(__file__))

## APP ROUTES ##

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return redirect('https://calbears.com/sports/2020/8/13/cameron-institute-about.aspx')
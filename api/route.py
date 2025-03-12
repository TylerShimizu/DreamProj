from flask import render_template, redirect
from api.app import app

@app.route("/")
@app.route("/home")
def home():
    return "<p>HELLO WORLD</p>"
    # return render_template('home.html')

@app.route("/about")
def about():
    return redirect('https://calbears.com/sports/2020/8/13/cameron-institute-about.aspx')
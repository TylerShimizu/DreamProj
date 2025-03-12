import os
import json
from flask import Flask, render_template, redirect, jsonify
from api.models import db
import api.googleSheet as google_api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.static_folder = "static"
basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
with app.app_context():
    db.create_all()
    sheets, id_and_questions, df = google_api.main()

CATEGORY_MAP = {}
CATEGORIES = sorted(df["Category"].unique())
for cat in CATEGORIES:
    sub_cats = df[df["Category"] == cat]["Sub-Category"].unique()
    CATEGORY_MAP[cat] = sorted(df[df["Category"] == cat]["Sub-Category"].unique())
LEVELS = {"Levels": []}
LEVELS["Levels"].extend(sorted(df[df["Levels"].str.startswith("Level")]["Levels"].unique()))
for other in sorted(df[~df["Levels"].str.startswith("Level")]["Levels"].unique()):
    LEVELS[other] = [other]

## APP ROUTES ##

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return redirect('https://calbears.com/sports/2020/8/13/cameron-institute-about.aspx')

## JS Call Routes ##

@app.route('/getData', methods=["POST"])
def getData():
    return jsonify(df.to_dict(orient='records'))
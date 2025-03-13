import os
import json
import re
import pandas as pd
from flask import Flask, render_template, redirect, jsonify, request, url_for, session
from api.models import db
import api.googleSheet as google_api
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.static_folder = "static"
basedir = os.path.abspath(os.path.dirname(__file__))

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    access_token_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    server_metadata_url=os.getenv("GOOGLE_DISCOVERY_URL"),
    userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
    client_kwargs={"scope": "openid email profile"},
)

##Possibly chnage this later to implement actual database
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

@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))

@app.route("/login/callback")
def callback():
    token = google.authorize_access_token()
    user_info = google.get("userinfo").json()
    session["user"] = user_info
    print(user_info)
    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

def custom_sort(val):
    level_match = re.match(r'Level (\d)', val)
    if level_match:
        return (0, int(level_match.group(1)))  # Prioritize levels by numeric value
    else:
        return (1, val)  # Alphabetical order for non-levels

@app.route("/questions", methods = ["GET", "POST"])
def showQuestions():
    Qs = pd.DataFrame()
    order = None

    if request.method == "POST":
        search_query = request.form.get('searchQuery', '', str).lower()
        print("searched:" + search_query)
        subCategory = request.form.getlist('sub_category')
        level = request.form.getlist('level')
        category = request.form.getlist("category")
        order = request.form.getlist("orderBy")

        if level:
            for sub in subCategory:
                cat, sub_cat = sub.split("->")
                Qs = pd.concat([Qs, df[(df["Category"] == cat) & (df["Sub-Category"].str.startswith(sub_cat)) & (df["Levels"].isin(level))]])
            for cat in category:
                if not any(cat == sub.split('->')[0] for sub in subCategory):
                    Qs = pd.concat([Qs, df[(df["Category"] == cat) & (df["Levels"].isin(level))]])
            if Qs.empty:
                Qs = df[df["Levels"].isin(level)]

        else:
            for sub in subCategory:
                cat, sub_cat = sub.split("->")
                Qs = pd.concat([Qs, df[(df["Category"] == cat) & (df["Sub-Category"].str.startswith(sub_cat))]])
            for cat in category:
                if not any(cat == sub.split('->')[0] for sub in subCategory):
                    Qs = pd.concat([Qs, df[(df["Category"] == cat)]])

    if Qs.empty:
        Qs = df
        if order:
            if order[0] == "lev":
                Qs = Qs.sort_values(by=['Levels'], key=lambda x: x.map(custom_sort))
            else:
                Qs = df.sort_values(by=['Sub-Category'])
        questions = Qs.to_dict(orient='records')
    else:
        if order:
            if order[0] == "lev":
                Qs = Qs.sort_values(by=['Levels'], key=lambda x: x.map(custom_sort))
            else:
                Qs = Qs.sort_values(by=['Sub-Category'])
        questions = Qs.to_dict(orient='records')

    return render_template('itemView.html', levels=LEVELS, categoryMap=CATEGORY_MAP, questions=questions)

## JS Call Routes ##

@app.route('/getData', methods=["POST"])
def getData():
    return jsonify(df.to_dict(orient='records'))
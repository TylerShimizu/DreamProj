import os
import json
import re
import pandas as pd
from flask import Flask, render_template, redirect, jsonify, request, url_for, session
from api.models import db, User, CartItem, Question
import api.googleSheet as google_api
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from google.oauth2.credentials import Credentials

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
    client_kwargs={
        'scope': (
            'openid email profile '
            'https://www.googleapis.com/auth/documents '
            'https://www.googleapis.com/auth/drive.file'
        )
    }
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
    session["token"] = token

    # Check if the user already exists in the database
    user = User.query.filter_by(email=user_info["email"]).first()
    if not user:
        # Create a new user if not exists
        user = User(email=user_info["email"], name=user_info["name"])
        db.session.add(user)
        db.session.commit()
        session['cart'] = []
    else:
        cart_items = [str(item.item_id) for item in user.cart_items]
        session["cart"] = cart_items

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

@app.route('/cart', methods = ["GET", 'POST'])
def view_cart():
    if 'user' in session:
        return render_template('cartView.html')
    else:
        return redirect('/login')

## JS Call Routes ##

@app.route('/getData', methods=["POST"])
def getData():
    return jsonify(df.to_dict(orient='records'))

@app.route('/getCartSize', methods=["POST"])
def cartSize():
    user = None
    if "user" in session:
        user = User.query.filter_by(email=session["user"]["email"]).first()
    if user:
        return jsonify({'cart_count': len(user.cart_items)})
    return jsonify({'cart_count': 0})

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    questionId = request.get_json()['question_id']
    message = ''
    if 'user' in session:
        user = User.query.filter_by(email=session["user"]['email']).first()
        user_id = user.id

        inCart = CartItem.query.filter_by(user_id=user_id, item_id=int(questionId)).first()

        if not inCart:
            new_cart_item = CartItem(user_id=user_id, item_id=int(questionId))
            db.session.add(new_cart_item)
            db.session.commit()
            message = 'Question added to cart successfully!'
            if questionId not in session['cart']:
                session['cart'].append(questionId)
        else:
            message = 'Already in cart!'

    return jsonify({
        'message': message,
        'cart_count': len(user.cart_items)
    })

@app.route('/removeItem', methods=['POST'])
def removeItem():
    itemId = request.get_json()['id']
    user = User.query.filter_by(email=session["user"]['email']).first()

    if user:

        cart_item = CartItem.query.filter_by(user_id=user.id, item_id=itemId).first()

        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            session['cart'].remove(str(itemId))

    return jsonify({'cart-count': len(user.cart_items)})

@app.route('/cartView', methods = ["POST"])
def cartView():
    if 'user' in session:
        user = User.query.filter_by(email=session["user"]["email"]).first()
        user_id = user.id

        items = []
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        for item in cart_items:
            question = df[df['id'] == item.item_id].iloc[0]  # Retrieve the question row from the DataFrame
            new_item = {
                'title': question['Item Stem'],
                'description': question['Anchors'].split(';'),
                'path': question['Category'] + " - " + question['Sub-Category'],
                'id': int(question['id'])
            }
            items.append(new_item)
        return jsonify(items)
    
@app.route('/exporting', methods=["POST"])
def exporting():
    if "token" not in session:
        return redirect("/login")

    dest = request.form.get('dest')
    data = json.loads(request.form.get('data'))
    creds = Credentials(
        token=session["token"]["access_token"],
        refresh_token=session["token"].get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    questions = pd.DataFrame()

    for item in data:
        questions = pd.concat([questions, df[(df["id"] == int(item))]])
    if dest == 'forms':
        form = google_api.update_form(questions)
        return redirect('https://docs.google.com/forms/d/' + form['formId'])
    else:
        docId = google_api.create_doc(questions, creds)
        return redirect('https://docs.google.com/document/d/' + docId)
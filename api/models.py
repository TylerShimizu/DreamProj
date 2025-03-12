from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', back_populates='cart_items')

User.cart_items = db.relationship('CartItem', order_by=CartItem.id, back_populates='user')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    sub_category = db.Column(db.String, nullable=False)
    stem = db.Column(db.String, nullable=False)
    anchor = db.Column(db.String, nullable=False)
    method = db.Column(db.String, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

class Questions:
    def __init__(self, id, level, data_collection_method, category, sub_cat, item_stem, method, anchor):
        self.id = id
        self.level = level
        self.dcm = data_collection_method
        self.category = category
        self.sub_cat = sub_cat
        self.question = item_stem
        self.anchor = anchor
        self.method = method
import secrets

from flask import Flask, make_response, render_template, request, send_from_directory, redirect
import bcrypt
import hashlib
import random
from html import escape

from pymongo import MongoClient
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]
token_collection = db["tokens"]
post_collection=db["posts"]
all_users=user_collection.find()
for p in all_users:
    print(p)

app = Flask(__name__,template_folder='template')

@app.route("/")
def indexPage():
    all_posts = post_collection.find()
    if "auth_token" in request.cookies:
        usr = request.cookies.get('username')
        return render_template('index.html', usr=usr, posts=all_posts)
    else:
        return render_template('index.html', usr="Guest", posts=all_posts)

@app.route("/static/style.css")
def css():
    resp = send_from_directory('static', 'style.css')
    return resp

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        inputUsername = request.form['username']
        inputPassword = request.form['password']
        salt = bcrypt.gensalt()
        pwHash = bcrypt.hashpw(inputPassword.encode('utf-8'), salt)
        user_collection.insert_one({"username": inputUsername, "password": pwHash})
        return make_response("U on da boat now!", 200)

@app.route("/login", methods=['POST'])
def login():
    inputUsername = request.form['username']
    inputPassword = request.form['password']
    user = user_collection.find_one({'username' : inputUsername})

    if user:
        if bcrypt.checkpw(inputPassword.encode('utf-8'), user['password']):
            resp = make_response("Now ur logged in", 200)
            auth_token = secrets.token_urlsafe(30)
            hashed_auth_token = str(hashlib.sha256(auth_token.encode('utf-8')).hexdigest())
            token_collection.insert_one({"auth_token" : hashed_auth_token, "username" : user["username"]})
            resp.set_cookie('auth_token', hashed_auth_token, max_age=3600, httponly=True)
            resp.set_cookie('username', user['username'], max_age=3600)
            return resp
        return make_response("Invalid username or password", 401)
    else:
        return make_response("You have to register first!", 401)

@app.route("/create-post", methods=["POST"])
def create_post():
    if "auth_token" in request.cookies:
        post_title = request.form['post-title']
        post_description = request.form['post-description']
        author = request.cookies.get('username')

        post_collection.insert_one({
            "title": escape(post_title, quote=False),
            "description": escape(post_description, quote=False),
            "author": escape(author, quote=False)
        })
        return redirect("/", 301)
    else:
        return make_response("Please login to make a post.", 401)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)

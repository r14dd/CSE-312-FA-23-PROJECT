import secrets
from html import escape
from flask import Flask, make_response, render_template, request, send_from_directory, redirect
import bcrypt
import hashlib
import random

from pymongo import MongoClient

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
users = db["users"]
posts = db["posts"]
likes = db["likes"]

all_users = posts.find()

app = Flask(__name__, template_folder='template')


def generate_random_string():
    return str(random.randint(1000, 9999))


@app.route("/")
def indexPage():
    all_posts = posts.find()
    auth_token = request.cookies.get("auth_token")
    if auth_token:
        # hashed_auth_token = ((hashlib.sha256(auth_token.encode())).hexdigest()).encode()
        fetchedUser = users.find_one({"auth_token" : auth_token})
            
        if fetchedUser:
            return render_template('index.html', usr=fetchedUser["username"], posts=all_posts)
            # return render_template('index.html', usr=fetchedUser["username"], posts=all_posts)
        else:
            return render_template('index.html', usr="Guest", posts=all_posts)
    else:
        return render_template('index.html', usr="Guest2", posts=all_posts)



@app.route("/static/style.css")
def css():
    resp = send_from_directory('static', 'style.css')
    return resp


@app.route("/create-post", methods=["POST"])
def create_post():
    post_title = request.form['post-title']
    post_description = request.form['post-description']
    author = request.cookies.get('username') if "auth_token" in request.cookies else "Guest" # change to use placeholder instead of cookie
    post_id = generate_random_string()
    if author == "Guest":
        return redirect('/')
    else:
        posts.insert_one({
            "_id": post_id,
            "title": post_title,
            "description": post_description,
            "author": author,
            "likes": []
        })
    return redirect('/')




@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        inputUsername = escape(request.form['username'])
        inputPassword = request.form['password']
        salt = bcrypt.gensalt()
        pwHash = bcrypt.hashpw(inputPassword.encode('utf-8'), salt)
        users.insert_one({"username": inputUsername, "password": pwHash.decode('utf-8')})
        return make_response("Now you are registered!", 200)


@app.route("/login", methods=['POST'])
def login():
    inputUsername = escape(request.form['username'])
    inputPassword = request.form['password']
    user = users.find_one({'username': inputUsername})

    if user:
        if bcrypt.checkpw(inputPassword.encode('utf-8'), user['password'].encode('utf-8')):
            resp = make_response("Now ur logged in", 200)
            auth_token = secrets.token_urlsafe(30)
            # hashed_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()
            hashed_auth_token = ((hashlib.sha256(auth_token.encode())).hexdigest()).encode()
            settingUp = users.find_one_and_update({"username" : inputUsername}, {"$set" : {"auth_token" : hashed_auth_token}})
            resp.set_cookie('auth_token',  , max_age=3600, httponly=True)
            return resp
        return make_response("Invalid username or password", 401)
    else:
        return make_response("You have to register first!", 401)




@app.route("/like-or-unlike-post/<post_id>", methods=["POST"])
def like_or_unlike_post(post_id):
    action = request.form['action']

    if "auth_token" in request.cookies:
        username = request.cookies.get('username')
    else:
        username = "Guest"

    post = posts.find_one({"_id": post_id})  # Use '_id' instead of 'id'

    if not post:
        return make_response("Post not found", 404)

    if username == "Guest":
        return make_response("You need to be logged in to like or unlike a post", 401)

    # Ensure 'likes' field exists and is a list
    if 'likes' not in post:
        post['likes'] = []

    if action == "like":
        if username not in post['likes']:
            posts.update_one({"_id": post_id}, {"$push": {"likes": username}})
            return redirect('/')
        else:
            return make_response("You have already liked this post", 400)

    elif action == "unlike":
        if username in post['likes']:
            posts.update_one({"_id": post_id}, {"$pull": {"likes": username}})
            return redirect('/')
        else:
            return make_response("You haven't liked this post yet", 400)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
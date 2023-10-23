import secrets
from html import escape
from flask import Flask, make_response, render_template, request, send_from_directory, redirect
import bcrypt
import hashlib
import random

from pymongo import MongoClient

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]
token_collection = db["tokens"]
post_collection = db["posts"]
like_counter = db["likes"]
# postID->Riad

# when i like

# postID->Riad,Baibhav
all_users = post_collection.find()
for p in all_users:
    print(p)

app = Flask(__name__, template_folder='template')


def generate_random_string():
    return str(random.randint(1000, 9999))


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


@app.route("/create-post", methods=["POST"])
def create_post():
    post_title = escape(request.form['post-title'], quote=False)
    post_description = escape(request.form['post-description'], quote=False)
    author = request.cookies.get('username') if "auth_token" in request.cookies else "Guest"
    post_id = generate_random_string()
    if author == "Guest":
        return redirect('/')
    else:
        post_collection.insert_one({
            "_id": post_id,
            "title": post_title,
            "description": post_description,
            "author": author,
            "likes": []
        })
    return redirect('/')


# we dont need this now boyyyy
@app.route("/like-post/<post_id>", methods=["POST"])
def like_post(post_id):
    username = request.cookies.get('username') if "auth_token" in request.cookies else "Guest"
    post = post_collection.find_one({"_id": post_id})

    if username == "Guest":
        return make_response("You need to be logged in to like a post", 401)

    if username not in post['likes']:
        post_collection.update_one({"_id": post_id}, {"$push": {"likes": username}})
        return make_response("Liked", 200)
    else:
        return make_response("You have already liked this post", 400)


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        inputUsername = escape(request.form['username'], quote=False)
        inputPassword = request.form['password']
        salt = bcrypt.gensalt()
        pwHash = bcrypt.hashpw(inputPassword.encode('utf-8'), salt)
        user_collection.insert_one({"username": escape(inputUsername, quote=False), "password": pwHash})
        return make_response("Now you are registered!", 200)


@app.route("/login", methods=['POST'])
def login():
    inputUsername = escape(request.form['password'], quote=False)
    inputPassword = request.form['password']
    user = user_collection.find_one({'username': inputUsername})

    if user:
        if bcrypt.checkpw(inputPassword.encode('utf-8'), user['password']):
            resp = make_response("Now ur logged in", 200)
            auth_token = secrets.token_urlsafe(30)
            hashed_auth_token = str(hashlib.sha256(auth_token.encode('utf-8')).hexdigest())
            token_collection.insert_one({"auth_token": hashed_auth_token, "username": user["username"]})
            resp.set_cookie('auth_token', hashed_auth_token, max_age=3600, httponly=True)
            resp.set_cookie('username', user['username'], max_age=3600)
            return resp
        return make_response("Invalid username or password", 401)
    else:
        return make_response("You have to register first!", 401)


# We dont need this now boyyyy
@app.route("/unlike-post/<post_id>", methods=["POST"])
def unlike_post(post_id):
    username = request.cookies.get('username') if "auth_token" in request.cookies else "Guest"
    post = post_collection.find_one({"_id": post_id})

    if username == "Guest":
        return make_response("You need to be logged in to unlike a post", 401)

    if username in post['likes']:
        post_collection.update_one({"_id": post_id}, {"$pull": {"likes": username}})
        return make_response("Unliked", 200)
    else:
        return make_response("You haven't liked this post yet", 400)


@app.route("/like-or-unlike-post/<post_id>", methods=["POST"])
def like_or_unlike_post(post_id):
    action = request.form['action']

    if "auth_token" in request.cookies:
        username = request.cookies.get('username')
    else:
        username = "Guest"

    post = post_collection.find_one({"_id": post_id})  # Use '_id' instead of 'id'

    if not post:
        return make_response("Post not found", 404)

    if username == "Guest":
        return make_response("You need to be logged in to like or unlike a post", 401)

    # Ensure 'likes' field exists and is a list
    if 'likes' not in post:
        post['likes'] = []

    if action == "like":
        if username not in post['likes']:
            post_collection.update_one({"_id": post_id}, {"$push": {"likes": username}})
            return redirect('/')
        else:
            return make_response("You have already liked this post", 400)

    elif action == "unlike":
        if username in post['likes']:
            post_collection.update_one({"_id": post_id}, {"$pull": {"likes": username}})
            return redirect('/')
        else:
            return make_response("You haven't liked this post yet", 400)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
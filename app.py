import secrets

from flask import *
from markupsafe import escape
import bcrypt
import hashlib
import random
import os
from flask_socketio import SocketIO, emit
import datetime
import time

import mail

from pymongo import MongoClient
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]
token_collection = db["tokens"]
post_collection=db["postsds"]
like_counter=db["likes"] 

all_users=post_collection.find()
for p in all_users:
    print(p)

ssl_context = ('nginx/cert.pem', 'nginx/private.key')

app = Flask(__name__,template_folder='template')
socketio = SocketIO(app, cors_allowed_origins="*", ssl_context=ssl_context, transport=['websocket'])

def generate_random_string():
    return str(random.randint(1000, 9999))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg','png','jpeg'}


@app.route("/blankVerify.html", methods=["GET"])
def tempVerify():
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        usr = token_collection.find_one({"auth_token" : at})
        verified = user_collection.find_one({"username" : usr["username"]})
        user_collection.update_one({"username" : verified["username"]}, {"$set" : {"isVerified" : "Yes"}})
        return redirect(url_for("verified_render"))
    return render_template("blankVerify.html")
 
@app.route("/")
def registerPage():
    if "auth_token" in request.cookies:
        return redirect(url_for("index_page"))
    return render_template("register.html")

@app.route("/login.html")
def login_render():
    return render_template("login.html")

@app.route("/verified.html")
def verified_render():
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        usr = token_collection.find_one({"auth_token": at})
        verified = user_collection.find_one({"username": usr["username"]})
        if verified["isVerified"] == "No":
            mail.sender(verified["email"])
        return render_template("verified.html",verified=verified["isVerified"])

@app.route("/index.html")
def index_page():
    all_posts = post_collection.find()
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        usr = token_collection.find_one({"auth_token": at})
        verified = user_collection.find_one({"username": usr["username"]})
        if verified["isVerified"] == "Yes":
            return render_template('index.html', usr=usr["username"], posts=all_posts)
        else:
            return redirect(url_for("verified_render"))
    elif "auth_token" not in request.cookies:
        return redirect(url_for("login_render"))


@app.route("/questionForm.html")
def questions_page():
    return render_template("questionForm.html")


@app.route("/static/style.css")
def css():
    resp = send_from_directory('static', 'style.css')
    return resp


@app.route("/create-post", methods=["POST"])
def create_post():
    post_title = request.form['post-title']
    post_description = request.form['post-description']
    correct_answer = request.form['correct-answer']
    author = ""
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        user = token_collection.find_one({"auth_token": at})
        author = user["username"]
    else:
        return make_response("You must login to create questions", 400)

    post_id = generate_random_string()
    question_image = request.files.get('question-image')
    image_filename = None
    if question_image and allowed_file(question_image.filename):
        fileExt = question_image.filename.rsplit('.', 1)[1].lower()
        image_filename = f"{post_id}.{fileExt}"
        question_image.save(os.path.join('static/', image_filename))
    current_time=datetime.time

    new_post = {
        "_id": post_id,
        "title": escape(post_title),
        "description": escape(post_description),
        "correct_answer": escape(correct_answer),
        "author": escape(author),
        "likes": []
    }
    if image_filename:
        new_post['image'] = image_filename
    expiration_time = int(time.time()) + 60  # 1 minute duration
    new_post['expiration_time'] = expiration_time
    post_collection.insert_one(new_post)
    # Emit the new post to all clients
    emit('new_post', new_post, namespace='/', broadcast=True)

    return redirect(url_for("index_page"))

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        inputUsername = escape(request.form['username_reg'])
        inputPassword = escape(request.form['password_reg'])
        inputEmail = escape(request.form['email_reg'])
        salt = bcrypt.gensalt()
        pwHash = bcrypt.hashpw(inputPassword.encode('utf-8'), salt)
        user_collection.insert_one({"username": inputUsername, "password": pwHash, "email": inputEmail, "isVerified": "No"})
        user_collection.update_many({}, {"$set": {"answered_questions": []}})
        return render_template("login.html")

@app.route("/login", methods=['POST'])
def login():
    inputUsername = escape(request.form['username_log'])
    inputPassword = escape(request.form['password_log'])
    user = user_collection.find_one({'username' : inputUsername})

    if user:
        if bcrypt.checkpw(inputPassword.encode('utf-8'), user['password']):
            resp = redirect(url_for("index_page"))
            auth_token = secrets.token_urlsafe(30)
            hashed_auth_token = str(hashlib.sha256(auth_token.encode('utf-8')).hexdigest())
            token_collection.insert_one({"auth_token" : hashed_auth_token, "username" : user["username"]})
            resp.set_cookie('auth_token', hashed_auth_token, max_age=3600, httponly=True)
            return resp
        return make_response("Invalid username or password", 401)
    else:
        return make_response("You have to register first!", 401)


@app.route("/like-or-unlike-post/<post_id>", methods=["POST"])
def like_or_unlike_post(post_id):
    action = request.form['action']
    username = "Guest"  # Default to Guest if no auth token is found

    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        user = token_collection.find_one({"auth_token": at})
        if user:
            username = user["username"]

    post = post_collection.find_one({"_id": post_id})
    if not post:
        return "Post not found", 404

    existing_answer = next((ans for ans in post.get('answers', []) if ans['user'] == username), None)
    if existing_answer:
        return make_response("You have already answered this question", 200)

    is_correct = action == post['correct_answer']

    post_collection.update_one(
        {"_id": post_id},
        {"$push": {"answers": {"user": username, "is_correct": is_correct}}}
    )

    return make_response("Correct" if is_correct else "Incorrect", 200)

@app.route("/my-answers")
def my_answers():
    if "auth_token" not in request.cookies:
        return redirect(url_for("login_render"))  

    at = request.cookies.get('auth_token')
    user = token_collection.find_one({"auth_token": at})
    if not user:
        return redirect(url_for("login_render")) 

    username = user["username"]
    all_posts = post_collection.find()

    user_answers = []
    for post in all_posts:
        for answer in post.get('answers', []):
            if answer['user'] == username:
                user_answers.append({
                    'question': post['title'],
                    'your_answer': answer['is_correct']
                })

    return render_template('my_answers.html', user_answers=user_answers)

    
@app.route("/my-posts")
def my_posts():
    if "auth_token" not in request.cookies:
        return redirect(url_for("login_render"))  # Or your login page

    at = request.cookies.get('auth_token')
    user = token_collection.find_one({"auth_token": at})
    if not user:
        return redirect(url_for("login_render"))  # Or your login page

    username = user["username"]
    user_posts = post_collection.find({"author": username})

    posts_with_answers = []
    for post in user_posts:
        post_info = {
            'id': post['_id'],
            'title': post['title'],
            'description': post['description'],
            'answers': post.get('answers', [])
        }
        posts_with_answers.append(post_info)

    return render_template('my_posts.html', posts=posts_with_answers)







if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0",port=8080,debug=True, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
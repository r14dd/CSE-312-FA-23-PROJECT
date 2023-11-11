import secrets

from flask import *
import bcrypt
import hashlib
import random
import os
from flask_socketio import SocketIO, emit


from pymongo import MongoClient
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]
token_collection = db["tokens"]
post_collection=db["postsss"]
like_counter=db["likes"] 

all_users=post_collection.find()
for p in all_users:
    print(p)

app = Flask(__name__,template_folder='template')
socketio = SocketIO(app, cors_allowed_origins="*")


def generate_random_string():
    return str(random.randint(1000, 9999))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg','png'}
 
@app.route("/")
def registerPage():
    if "auth_token" in request.cookies:
        return redirect(url_for("index_page"))
    return render_template("register.html")

@app.route("/login.html")
def login_render():
    return render_template("login.html")

@app.route("/index.html")
def index_page():
    all_posts = post_collection.find()
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        usr = token_collection.find_one({"auth_token": at})
        return render_template('index.html', usr=usr["username"], posts=all_posts)


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

    new_post = {
        "_id": post_id,
        "title": post_title,
        "description": post_description,
        "correct_answer": correct_answer,
        "author": author,
        "likes": []
    }
    if image_filename:
        new_post['image'] = image_filename

    post_collection.insert_one(new_post)
    # Emit the new post to all clients
    emit('new_post', new_post, namespace='/', broadcast=True)

    return redirect(url_for("index_page"))

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        inputUsername = request.form['username_reg']
        inputPassword = request.form['password_reg']
        salt = bcrypt.gensalt()
        pwHash = bcrypt.hashpw(inputPassword.encode('utf-8'), salt)
        user_collection.insert_one({"username": inputUsername, "password": pwHash})
        return render_template("login.html")

@app.route("/login", methods=['POST'])
def login():
    inputUsername = request.form['username_log']
    inputPassword = request.form['password_log']
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

    username = ""
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        user = token_collection.find_one({"auth_token": at})
        username = user["username"]
    else:
        username = "Guest"

    post = post_collection.find_one({"_id": post_id})  

    if not post:
        return make_response("Post not found", 404)

    if username == "Guest":
        return make_response("You need to be logged in to like or unlike a post", 401)

    if 'likes' not in post:
        post['likes'] = []

    if action == "like":
        if username not in post['likes']:
            post_collection.update_one({"_id": post_id}, {"$push": {"likes": username}})
        return redirect(url_for("index_page"))
            
    elif action == "unlike":
        if username in post['likes']:
            post_collection.update_one({"_id": post_id}, {"$pull": {"likes": username}})
        return redirect(url_for("index_page"))

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)

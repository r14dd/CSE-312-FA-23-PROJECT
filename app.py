import secrets
from flask import *
import bcrypt
import hashlib
import random
import os
from flask_socketio import SocketIO, emit
import datetime
import time

from pymongo import MongoClient
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]
token_collection = db["tokens"]
post_collection=db["poster"]
like_counter=db["likes"] 
grade_collection = db["grades"]


all_users=post_collection.find()
for p in all_users:
    print(p)

app = Flask(__name__,template_folder='template')
socketio = SocketIO(app, cors_allowed_origins="*")

def grade_submissions(question_id):
    """Grade all submissions for a question."""
    question = post_collection.find_one({"_id": question_id})
    correct_answer = question['correct_answer']
    submissions = question.get('likes', [])
    
    graded_submissions = []
    for user in submissions:
        grade = "Correct" if user == correct_answer else "Incorrect"
        graded_submissions.append({"username": user, "grade": grade})

    post_collection.update_one(
        {"_id": question_id},
        {"$set": {"graded_submissions": graded_submissions}}
    )

@app.route("/end-question/<question_id>", methods=["POST"])
def end_question(question_id):
    grade_submissions(question_id)
    return '', 204  # No content to return


@app.route("/my-grades")
def view_my_grades():
    """View grades for the logged-in user."""
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        user = token_collection.find_one({"auth_token": at})
        if user:
            grades = grade_collection.find({"username": user["username"]})
            return render_template("my_grades.html", grades=grades)
        else:
            return redirect(url_for("login_render"))
    else:
        return redirect(url_for("login_render"))

@app.route("/gradebook/<question_id>")
def view_gradebook(question_id):
    """View all grades for a question created by the logged-in user."""
    if "auth_token" in request.cookies:
        at = request.cookies.get('auth_token')
        user = token_collection.find_one({"auth_token": at})
        question = post_collection.find_one({"_id": question_id})
        if question and question['author'] == user['username']:
            grades = grade_collection.find({"question_id": question_id})
            return render_template("gradebook.html", grades=grades, question=question)
        else:
            return make_response("Unauthorized", 401)
    else:
        return redirect(url_for("login_render"))

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
    current_time=datetime.time

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
    expiration_time = int(time.time()) + 60  # 1 minute duration
    new_post['expiration_time'] = expiration_time
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
        user_collection.update_many({}, {"$set": {"answered_questions": []}})
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
    user_answer = request.form['action']
    post = post_collection.find_one({"_id": post_id})

    if post:
        correct_answer = post['correct_answer']
        user = "Guest"  # Replace with actual user identification logic
        is_correct = user_answer == correct_answer

        # Update the post with the user's answer and whether it was correct
        post_collection.update_one(
            {"_id": post_id},
            {"$push": {"answers": {"user": user, "is_correct": is_correct}}}
        )

        return redirect(url_for("index_page"))
    else:
        return "Post not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)

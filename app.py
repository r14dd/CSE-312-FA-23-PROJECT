from flask import Flask, make_response, render_template, request, send_from_directory
import bcrypt
import hashlib
import random

from pymongo import MongoClient
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
user_collection = db["users"]

app = Flask(__name__,template_folder='template')

@app.route("/")
def indexPage():
    resp = make_response(render_template('index.html'))
    return resp

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
        user_collection.insert_one({"username": inputUsername, "password": pwHash.decode('utf-8')})
        return "Account Registered"

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)



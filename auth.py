from flask import redirect, flash, request, render_template, make_response
import bcrypt, secrets, hashlib
from db import Database

class Register:

    def register(username, password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        Database.insertUserIntoTheCollection(username, hashed_password)
        return make_response("You are now registered.", 301)

class Login:
    def login(username, password):
        current_user = Database.findUser(username)

        if current_user:
            if bcrypt.checkpw(password.encode('utf-8'), current_user['password'].encode('utf-8')):
                response = make_response("You are now logged in!", 200)
                random_auth_token = secrets.token_urlsafe(30)
                hashed_auth_token = hashlib.sha256(random_auth_token.encode('utf-8')).hexdigest()
                Database.addAuthToken(username, hashed_auth_token)
                response = response.set_cookie("auth_token", hashed_auth_token, max_age=3600, httponly=True)
                return response

            else:
                return make_response("Invalid username or password.", 200)

        else:
            return make_response("You need to register an account first.", 200)


class Root:
    def root():
        fetched_auth_token = request.cookies.get("auth_token")
        
        if fetched_auth_token:
            does_token_exist = Database.findToken(fetched_auth_token)

            if does_token_exist != None:
                return render_template('index.html', usr=does_token_exist["username"])
            
            else:
                return render_template("index.html", usr="Guest")
                
        else:
            return render_template("index.html", usr="Guest")


                



from flask import redirect, flash, request, render_template
import bcrypt, secrets, hashlib
from db import Database

class Register:

    def register(username, password):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        Database.insertUserIntoTheCollection(username, hashed_password)

class Login:
    def login(username, password):
        current_user = Database.findUser(username)

        if current_user != None:
            if bcrypt.checkpw(password.encode(), current_user['password']):
                random_auth_token = secrets.token_urlsafe(30)
                hashed_auth_token = hashlib.sha256(random_auth_token.encode()).hexdigest()
                Database.addAuthToken(username, hashed_auth_token)
                flash("Your authentication was successful!", category="message")
                response = redirect("/", 302)
                response = response.set_cookie("auth_token", hashed_auth_token, max_age=3600, httponly=True)
                return response

            else:
                flash("Invalid username or password.", category="error")
                return redirect("/", 302)

        else:
            flash("You need to register an account first.", category="error")
            return redirect("/", 302)

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


                



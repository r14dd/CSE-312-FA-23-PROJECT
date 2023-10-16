from flask import Flask, make_response, render_template
import bcrypt
import hashlib
import random

app = Flask(__name__,template_folder='template')

@app.route("/")
def indexPage():
    resp = make_response(render_template('index.html'))
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)



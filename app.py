from flask import Flask, request, abort, send_from_directory
from auth import Register, Login, Root
app = Flask(__name__, template_folder = 'template')


@app.route("/")
def root():
    return Root.root()

@app.route("/static/style.css")
def css():
    return send_from_directory('static', 'style.css')

@app.route("/register", methods=['POST'])
def registerHandler():
    _username = request.form.get('username_reg', None)
    _password = request.form.get('password_reg', None)

    if _username != None and _password != None:
        return Register.register(_username, _password)
        
    else:
        abort(400)

@app.route("/login", methods=['POST'])
def loginHandler():
    _username = request.form.get('username_log', None)
    _password = request.form.get('password_log', None)

    if _username != None and _password != None:
        return Login.login(_username, _password)

    else:
        abort(400)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
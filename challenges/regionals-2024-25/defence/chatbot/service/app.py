from flask import *
from db import *
from agent import *
import base64

app = Flask(__name__)
valid_sessions = []

@app.route("/ping")
def ping():
  return "Pong!"

@app.route("/")
def login():
  return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_user():
  print("Login request received")

  # Get the form data
  username = request.form.get("username")
  if not username:
    abort(400, "Username is required")
  password = request.form.get("password")
  if not password:
    abort(400, "Password is required")

  # Check if credentials are valid
  if not get_user(username, password):
    abort(400, "Invalid credentials")

  session = base64.b64encode(username.encode()).decode()
  valid_sessions.append(session)

  resp = make_response()
  resp.status_code = 200
  resp.set_cookie('session', session)
  return resp

@app.route("/register", methods=["POST"])
def register_user():
  print("Register request received")

  # Get the form data
  username = request.form.get("username")
  if not username:
    abort(400, "Username is required")
  password = request.form.get("password")
  if not password:
    abort(400, "Password is required")
  phone = request.form.get("phone")
  if not phone:
    abort(400, "Phone is required")
  email = request.form.get("email")
  if not email:
    abort(400, "Email is required")
  candidate = request.form.get("candidate")
  if not candidate:
    abort(400, "Candidate checkbox is required")

  platform = ""
  if candidate == "true":
    platform = request.form.get("platform")
    if not platform:
      abort(400, "Platform is required")

  # Check if user already exists
  if check_user(username):
    abort(400, "User already exists")

  # Create user in the db
  print(f"Creating user..., username: {username}, candidate: {candidate}")
  create_user(username, password, candidate, phone, email, platform)
  print(f"User {username} registered successfully")

  # Now login the user
  session = base64.b64encode(username.encode()).decode()
  valid_sessions.append(session)

  resp = make_response()
  resp.status_code = 200
  resp.set_cookie('session', session)
  return resp

@app.route("/chat")
def index():
    # Check if user is logged in
    session = request.cookies.get('session')
    if not session or session not in valid_sessions:
        return redirect('/')
    print("User connected to chat: ", session)

    # Lookup the user info
    username = base64.b64decode(session).decode()
    user = check_user(username)
    print("User info: ", user)
    if not user:
        return redirect('/')

    return render_template("chat.html", name=user[1], isCandidate=user[3], platform=user[5])

@app.route("/message")
def get_bot_response():
    # Check if user is logged in
    session = request.cookies.get('session')
    if not session or session not in valid_sessions:
        return redirect('/')
    print("User send request to chat: ", session)

    userText = request.args.get('msg')
    print("Received question: ", userText)
    resp = askAgent(userText)
    # Remove any special characters
    resp = ''.join(e for e in resp if e.isalnum() or e.isspace() or e in [",", ".", "?", "!", "-", ":", ";", "(", ")", "[", "]", "{", "}", "@", "_"])
    return resp

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=80, debug=True)
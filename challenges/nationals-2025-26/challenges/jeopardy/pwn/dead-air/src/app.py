#!/usr/bin/env python3

import os
import uuid
import subprocess
import shutil
from flask import Flask, request, render_template, send_file, abort

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

UPLOAD_DIR   = "/tmp/relay-uploads"
DUMMY_VIDEO  = "/opt/dummy.mp4"
VLC_BIN      = "/opt/vlc/bin/vlc"
VLC_PLUGIN   = "/opt/vlc/lib/vlc"
TIMEOUT_SECS = 15

ALLOWED_DOWNLOADS = {
    "bin/vlc":                             "/opt/vlc/bin/vlc",
    "lib/vlc/demux/libsubtitle_plugin.so": "/opt/vlc/lib/vlc/demux/libsubtitle_plugin.so",
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if f is None or f.filename == "":
        return render_template("index.html", error="No file selected.")

    allowed = (".srt", ".sub", ".ssa", ".ass", ".rt", ".txt", ".smi", ".vtt")
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in allowed:
        return render_template(
            "index.html",
            error=f"Unsupported format '{ext}'. Accepted: {', '.join(allowed)}"
        )

    job_id  = uuid.uuid4().hex
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir)

    sub_path   = os.path.join(job_dir, "broadcast" + ext)
    video_path = os.path.join(job_dir, "broadcast.mp4")

    f.save(sub_path)
    shutil.copy(DUMMY_VIDEO, video_path)

    env = {
        "PATH":             "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME":             "/home/relay",
        "VLC_PLUGIN_PATH":  VLC_PLUGIN,
        "VLC_DATA_PATH":    "/opt/vlc/share",
        "LD_LIBRARY_PATH":  "/opt/vlc/lib",
    }

    cmd = [
        "su", "-s", "/bin/bash", "relay", "-c",
        (
            f"{VLC_BIN}"
            f" -I dummy"
            f" --no-video --no-audio"
            f" --sub-file '{sub_path}'"
            f" --play-and-exit"
            f" --verbose 2"
            f" '{video_path}'"
            f" vlc://quit"
        ),
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_SECS,
            env=env,
        )
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)

    return render_template("index.html",
                           success="Subtitle received and queued for broadcast relay.")


@app.route("/download/<path:name>")
def download(name):
    real = ALLOWED_DOWNLOADS.get(name)
    if real is None or not os.path.isfile(real):
        abort(404)
    return send_file(real, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

# Step 2: App Stub Dockerfiles

Each app gets a minimal Dockerfile serving a health endpoint.

## `apps/canary/Dockerfile`

```dockerfile
FROM python:3.12-alpine
RUN pip install flask
COPY <<'EOF' /app/main.py
from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
EOF
EXPOSE 9000
CMD ["python", "/app/main.py"]
```

## `apps/experimental/Dockerfile`

Same as canary but port 9001:

```dockerfile
FROM python:3.12-alpine
RUN pip install flask
COPY <<'EOF' /app/main.py
from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
EOF
EXPOSE 9001
CMD ["python", "/app/main.py"]
```

## `apps/legacy/Dockerfile`

Same pattern, port 9002:

```dockerfile
FROM python:3.12-alpine
RUN pip install flask
COPY <<'EOF' /app/main.py
from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9002)
EOF
EXPOSE 9002
CMD ["python", "/app/main.py"]
```

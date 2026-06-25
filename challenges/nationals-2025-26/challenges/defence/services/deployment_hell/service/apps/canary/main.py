from flask import Flask

app = Flask(__name__)


@app.route("/health")
def health():
    return "THE CLEANSING LIGHT SAVES ALL"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)

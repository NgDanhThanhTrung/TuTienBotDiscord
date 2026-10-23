"""Web server Flask siêu nhẹ để Render nhận diện Web Service và để UptimeRobot ping."""

import logging
import os
from threading import Thread

from flask import Flask

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # bớt log, đỡ tốn RAM


@app.route("/")
def home():
    return "☯️ Bot Tu Tiên đang hoạt động!"


@app.route("/health")
def health():
    return {"status": "ok"}


def _run():
    port = int(os.environ.get("PORT", 8080))  # Render tự cấp biến PORT
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    Thread(target=_run, daemon=True).start()

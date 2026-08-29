import os
from flask import Flask, request

app = Flask(__name__)

@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")
    output = os.popen(f"ping -c 1 {host}").read()
    return f"<pre>{output}</pre>"

from flask import Flask, request, send_file

app = Flask(__name__)

BASE_DIR = "/var/www/files"

@app.route("/download")
def download():
    filename = request.args.get("file", "")
    filepath = BASE_DIR + "/" + filename
    return send_file(filepath)

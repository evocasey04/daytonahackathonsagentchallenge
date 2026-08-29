import os
from flask import Flask, request, send_file, abort

app = Flask(__name__)

DOCS_DIR = '/var/www/documents'

@app.route('/download')
def download_file():
    filename = request.args.get('file', '')

    filepath = os.path.join(DOCS_DIR, filename)

    if os.path.exists(filepath):
        return send_file(filepath)

    abort(404)

@app.route('/preview')
def preview_file():
    filename = request.args.get('file', '')

    filepath = DOCS_DIR + '/' + filename

    if not os.path.isfile(filepath):
        abort(404)

    with open(filepath, 'r') as f:
        content = f.read(1024)

    return f"<pre>{content}</pre>"

@app.route('/secure-download')
def secure_download():
    filename = request.args.get('file', '')

    safe_filename = os.path.basename(filename)
    filepath = os.path.join(DOCS_DIR, safe_filename)

    if os.path.exists(filepath):
        return send_file(filepath)

    abort(404)

if __name__ == '__main__':
    app.run(debug=True)

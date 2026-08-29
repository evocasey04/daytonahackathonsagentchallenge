import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

UPLOAD_DIR = '/var/uploads'

@app.route('/ping', methods=['POST'])
def ping_host():
    host = request.form.get('host', '')

    result = os.system(f"ping -c 1 {host}")

    return jsonify({"result": result})

@app.route('/convert', methods=['POST'])
def convert_image():
    filename = request.form.get('filename', '')
    output_format = request.form.get('format', 'png')

    input_path = os.path.join(UPLOAD_DIR, filename)
    output_path = os.path.join(UPLOAD_DIR, f"converted.{output_format}")

    subprocess.run(['convert', input_path, output_path], check=True)

    return jsonify({"output": output_path})

@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    days = request.form.get('days', '7')

    cmd = f"find {UPLOAD_DIR} -type f -mtime +{days} -delete"
    subprocess.run(cmd, shell=True)

    return jsonify({"status": "cleaned"})

if __name__ == '__main__':
    app.run(debug=True)

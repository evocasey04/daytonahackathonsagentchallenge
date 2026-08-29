import json
import threading
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

import main as arena

app = Flask(__name__)
CORS(app)

RESULTS_PATH = Path("results.json")

_run_lock = threading.Lock()
_is_running = False


def _run_arena():
    global _is_running
    try:
        arena.main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        with _run_lock:
            _is_running = False


@app.route("/run", methods=["POST"])
def run():
    global _is_running
    with _run_lock:
        if _is_running:
            return jsonify({"status": "already_running"}), 409
        _is_running = True

    threading.Thread(target=_run_arena, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/results", methods=["GET"])
def results():
    if not RESULTS_PATH.exists():
        return jsonify([])
    with open(RESULTS_PATH) as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(port=5000, debug=False)

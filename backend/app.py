import json
import os
import subprocess
import sys

from flask import Flask, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMO_DIR = os.path.join(BASE_DIR, "sumo")
STATE_FILE = os.path.join(SUMO_DIR, "state.json")
CONTROLLER_FILE = os.path.join(SUMO_DIR, "adaptive_controller.py")

controller_process = None

RESET_STATE = {
    "simulation_time": 0,
    "intersection": "center",
    "priority": "",
    "phase": 0,
    "green_time": 0,
    "prediction": {"ns": 0, "ew": 0},
    "actual": {"ns": 0, "ew": 0},
    "final": {"ns": 0, "ew": 0},
}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Cache-Control"] = "no-store"
    return response


def write_reset_state():
    os.makedirs(SUMO_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(RESET_STATE, f, indent=2)


def stop_process():
    global controller_process

    if controller_process is None:
        return

    if controller_process.poll() is None:
        controller_process.terminate()
        try:
            controller_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            controller_process.kill()
            controller_process.wait(timeout=5)

    controller_process = None


@app.route("/api/state", methods=["GET"])
def get_state():
    if not os.path.exists(STATE_FILE):
        return jsonify(RESET_STATE)

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/start", methods=["POST"])
def start_controller():
    global controller_process

    if controller_process is not None and controller_process.poll() is None:
        return jsonify({"status": "already_running"})

    if not os.path.exists(CONTROLLER_FILE):
        return jsonify({"error": f"Controller not found: {CONTROLLER_FILE}"}), 500

    controller_process = subprocess.Popen(
        [sys.executable, CONTROLLER_FILE],
        cwd=SUMO_DIR,
    )

    return jsonify({"status": "started"})


@app.route("/api/stop", methods=["POST"])
def stop_controller():
    was_running = (
        controller_process is not None
        and controller_process.poll() is None
    )

    stop_process()

    return jsonify({
        "status": "stopped" if was_running else "not_running"
    })


@app.route("/api/reset", methods=["POST"])
def reset_controller():
    stop_process()
    write_reset_state()
    return jsonify({"status": "reset"})


@app.route("/api/status", methods=["GET"])
def controller_status():
    running = (
        controller_process is not None
        and controller_process.poll() is None
    )
    return jsonify({"running": running})


if __name__ == "__main__":
    write_reset_state()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )

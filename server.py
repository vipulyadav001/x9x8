from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import subprocess
import sys
import os
from pathlib import Path

app = Flask(__name__, static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Track USB launcher status
usb_launcher_active = False

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"active": usb_launcher_active})

@app.route('/launch', methods=['POST'])
def launch_usb_detector():
    global usb_launcher_active
    try:
        if not usb_launcher_active:
            # Get the paths to the scripts
            launcher_path = Path(__file__).parent / 'usb_launcher.py'
            server_path = Path(__file__)
            
            # Start the USB launcher in a new process
            python_exe = sys.executable
            subprocess.Popen(
                [python_exe, str(launcher_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Start another instance of the server in a new process
            subprocess.Popen(
                [python_exe, str(server_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            usb_launcher_active = True
            socketio.emit('status_change', {'active': True})
            return jsonify({"status": "success", "message": "USB Launcher activated"}), 200
        else:
            return jsonify({"status": "warning", "message": "USB Launcher is already running"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/usb-detected', methods=['POST'])
def usb_detected():
    socketio.emit('usb_event', {'message': 'USB device detected!'})
    return jsonify({"status": "success"}), 200

@socketio.on('connect')
def handle_connect():
    emit('status_change', {'active': usb_launcher_active})

if __name__ == '__main__':
    socketio.run(app, port=8000, debug=True, allow_unsafe_werkzeug=True)

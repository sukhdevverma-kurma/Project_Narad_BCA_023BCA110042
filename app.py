# --- NARAYAN: OFFLINE DISASTER COMMUNICATION SERVER (FULL CODE) ---
import os
import time
import threading
import sys
import webbrowser
from threading import Timer
import qrcode
import io
import eventlet

# Flask & SocketIO imports
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_socketio import SocketIO, send, emit

# DNS Server import (Ensure dns_server.py is in the same folder)
import dns_server 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'narayan-secret'



socketio = SocketIO(app)

# Global Variables
SYSTEM_ACTIVE = False
HOST_IP = None
admin_session_id = None

# --- ROUTES ---

@app.route('/')
def index():
    # Agar system set hai to Chat Page, nahi to Config Page
    if SYSTEM_ACTIVE:
        return render_template('index_styled.html')
    else:
        return render_template('config.html')

@app.route('/initialize', methods=['POST'])
def initialize():
    global SYSTEM_ACTIVE, HOST_IP
    HOST_IP = request.form.get('host_ip')
    
    if HOST_IP:
        print(f"--- SYSTEM INITIALIZING WITH IP: {HOST_IP} ---")
        # Start DNS in background
        dns_thread = threading.Thread(target=dns_server.start_dns_service, args=(HOST_IP,))
        dns_thread.daemon = True 
        dns_thread.start()
        
        SYSTEM_ACTIVE = True
        return redirect(url_for('admin_dashboard'))
    return "Error: IP Required"

@app.route('/admin')
def admin_dashboard():
    if not SYSTEM_ACTIVE:
        return redirect('/')
    return render_template('admin_styled.html')

# --- QR CODE GENERATOR ---
@app.route('/get_qr')
def get_qr():
    if not HOST_IP:
        return "System not initialized", 404
    url = f"http://{HOST_IP}/"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


# --- ANDROID CAPTIVE PORTAL TRIGGERS ---
@app.route('/generate_204')
@app.route('/gen_204')
@app.route('/ncsi.txt')
def captive_portal_trigger():
    # Android ko force karo ki wo login page khol de
    return redirect(url_for('index'), code=302)

@app.route('/<path:path>')
def catch_all(path):
    # Koi kuch bhi type kare, seedha Home Page par bhejo
    return redirect(url_for('index'), code=302)

# --- SOCKET EVENTS (CHAT LOGIC) ---

@socketio.on('connect')
def handle_connect():
    if 'admin' in request.args:
        global admin_session_id
        admin_session_id = request.sid
        emit('admin_status', {'data': f'System Online on IP: {HOST_IP}'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"User disconnected: {request.sid}")

@socketio.on('victim_message')
def handle_victim_message(data):
    if admin_session_id:
        emit('new_victim_message', {'msg': data['msg'], 'id': request.sid}, room=admin_session_id)

@socketio.on('admin_reply')
def handle_admin_reply(data):
    emit('server_message', {'msg': data['msg']}, room=data['id'])

@socketio.on('admin_broadcast')
def handle_admin_broadcast(data):
    send({'msg': f"ADMIN: {data['msg']}"}, broadcast=True, include_self=False)

# --- STARTUP ---

def open_browser():
    webbrowser.open_new('http://127.0.0.1/')

if __name__ == '__main__':
    print("--- STARTING NARAYAN SETUP INTERFACE ---")
    
    # 1.5 second baad browser khulega
    Timer(1.5, open_browser).start()
    
    # Port 80 for Captive Portal (Admin Rights Needed)
    socketio.run(app, host='0.0.0.0', port=80, debug=True, allow_unsafe_werkzeug=True)
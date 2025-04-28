from flask import Blueprint, request
from flask_socketio import SocketIO, emit

websocket_bp = Blueprint('websocket', __name__)
socketio = SocketIO()

@websocket_bp.route('/socket.io')
def socket_io():
    return socketio.run()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('position_update')
def handle_position_update(data):
    print('Position update received:', data)
    emit('position_response', {'status': 'success'}, broadcast=True)
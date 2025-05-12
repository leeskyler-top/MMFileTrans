import random

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from MsgService.Login import jslogin, login, get_new_session, webwxnewloginpage, webwxinit, whitelist, webwxstatreport, \
    speed
from MsgService.Upload import upload_auto_file
from utils.ParseData import download_img
import base64
import io
import os
import uuid

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 设置为1G
socketio = SocketIO(app, cors_allowed_origins="*")

sessions = {}


def start_login(session, session_id):
    """Handles the login process and refreshing of QR code."""
    while True:
        whitelist(session)
        webwxstatreport(session)
        login_uuid = jslogin(session)
        qrcode_url = f"https://login.weixin.qq.com/qrcode/{login_uuid}"
        speed(session, qrcode_url=qrcode_url, duration=round(random.uniform(70, 120), 1))

        image_bytes = download_img(session, qrcode_url, show_img=False)

        buffered = io.BytesIO(image_bytes.getvalue())
        qr_code_base64 = base64.b64encode(buffered.read()).decode('utf-8')

        socketio.emit('update_qrcode', {'qrcode_base64': qr_code_base64})

        waiting_count = 0
        MAX_WAITING_COUNT = 20

        while waiting_count < MAX_WAITING_COUNT:
            socketio.sleep(1)  # Wait for 1 second
            code, redirect_url = login(session, login_uuid)

            socketio.emit('login_status', {'code': code})

            if code == '200':  # Login Successful
                cookies_dict, skey, pass_ticket = webwxnewloginpage(session, redirect_url)
                user_conf = webwxinit(session, pass_ticket=cookies_dict['webwx_data_ticket'], skey=skey,
                                      cookie_dict=cookies_dict)

                sessions[session_id] = {
                    'session': session,
                    'cookies': cookies_dict,
                    'user_conf': user_conf,
                    'skey': skey,
                    'pass_ticket': pass_ticket,
                }
                socketio.emit('login_success', {'message': 'Logged In'})
                return
            elif code == '201':
                waiting_count += 1
            elif code == '408':
                break


@app.route('/login', methods=['POST'])
def login_endpoint():
    session_id = str(uuid.uuid4())  # Generate a unique session ID for this request

    # Create a new session
    session = get_new_session()
    socketio.start_background_task(target=start_login, session=session, session_id=session_id)

    return {"message": "Running login process, please wait for updates via WebSocket.", "session_id": session_id}, 200


@app.route('/upload', methods=['POST'])
def handle_file_upload():
    session_id = request.form.get('session_id')

    if session_id not in sessions:
        return jsonify({'message': 'Session not valid or expired.'}), 403

    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400

    cookies_dict = sessions[session_id]['cookies']

    print(f"Uploading file: {file.filename}")

    try:
        upload_auto_file(
            None,  # 直接传递文件流
            cookies_dict=cookies_dict,
            user_config=sessions[session_id]['user_conf'],
            skey=sessions[session_id]['skey'],
            pass_ticket=sessions[session_id]['pass_ticket'],
            filename=file.filename,
            file_stream=file.read()
        )
        return jsonify({'message': 'File uploaded successfully.'}), 200
    except Exception as e:
        return jsonify({'message': f'File upload failed: {str(e)}'}), 500


@socketio.on('connect')
def handle_connect():
    emit('message', {'data': 'Connected to WebSocket.'})


if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5000)

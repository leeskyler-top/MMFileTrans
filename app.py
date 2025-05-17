import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from LoadEnviroment.LoadEnv import host
from MsgService.Login import (
    jslogin, login, get_new_session,
    webwxnewloginpage, webwxinit,
    whitelist, webwxstatreport,
    speed, logout
)
from MsgService.Upload import upload_auto_file
from utils.ParseData import download_img
import base64
import io
import uuid

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 设置为1G
socketio = SocketIO(app, cors_allowed_origins="*")

sessions = {}
active_login_threads = {}  # 用于跟踪每个 session 的登录线程


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
                    'expiry_time': datetime.now() + timedelta(seconds=3600 - 200)
                }
                socketio.emit('login_success', {'message': 'Logged In'})
                return  # 登录完成，退出
            elif code == '201':
                waiting_count += 1
            elif code == '408':
                break


@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id is None or sessions.get(session_id) is None or sessions[session_id]['expiry_time'] < datetime.now():
        # 如果已经有线程在处理该 session_id，则需要中止它
        if session_id in active_login_threads:
            # 停止已有的登录过程
            active_login_threads[session_id].cancel()  # 这个方法需要自定义以停止登录过程

        if session_id is None:
            session_id = str(uuid.uuid4())
        session = get_new_session()

        # 使用 Flask-SocketIO 的后台任务
        socketio.start_background_task(start_login, session, session_id)

        return {"message": "Running login process, please wait for updates via WebSocket.",
                "session_id": session_id}, 200

    return {"message": "Valid Session ID", "session_id": session_id}, 200


@app.route('/logout', methods=['DELETE'])
def logout_endpoint():
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id is None or session_id not in sessions:
        return {"message": "SessionID Not Found", "session_id": None}, 404

    # 清理会话信息
    status_code = logout(sessions[session_id]['session'], sessions[session_id]['skey'], sessions[session_id]['cookies'])
    del sessions[session_id]
    if session_id in active_login_threads:
        del active_login_threads[session_id]  # 清理活动线程

    return {"message": "Session has been logged out."}, status_code


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
            file_stream=file.read(),
            socketio=socketio
        )

        return jsonify({'message': 'File uploaded successfully.'}), 200
    except Exception as e:
        return jsonify({'message': f'File upload failed: {str(e)}'}), 500


@socketio.on('connect')
def handle_connect():
    emit('message', {'data': 'Connected to WebSocket.'})


if __name__ == "__main__":
    print(host)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5000, host=host)

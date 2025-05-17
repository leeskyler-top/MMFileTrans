import time
import hashlib
import os
import math
import mimetypes
from datetime import datetime

import requests
import json

from LoadEnviroment.LoadEnv import file_wx_baseurl, filetransfer_baseurl, file_wx_domain, filetransfer_domain
from utils.Generate import get_header, random_string, generate_client_media_id, generate_client_msg_id
from utils.LoadJson import get_aegis_id
from utils.ParseData import get_form_data_type

CHUNK_SIZE = 512 * 1024  # 512 KB
UPLOAD_MEDIA_BASE = f"{file_wx_baseurl}/cgi-bin/mmwebwx-bin/webwxuploadmedia"
UPLOAD_PARALLEL_BASE = f"{file_wx_baseurl}/cgi-bin/mmwebwx-bin/webwxuploadmediaparallel"
CHECK_UPLOAD_URL = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxcheckupload"
aid, uin, session_id, device_id, report_id = get_aegis_id()

import hashlib


def get_file_md5(file_path=None, file_stream=None):
    """计算文件的MD5值，可以从文件路径或文件流中获取。"""
    md5 = hashlib.md5()

    if file_stream is None and file_path is not None:
        # 从文件路径读取
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
    elif file_stream is not None:
        # 从文件流读取
        md5.update(file_stream)
    else:
        raise ValueError("Either 'file_path' must be provided or 'file_stream' must be given.")

    return md5.hexdigest()


def get_aes_signature(cookie_dict, user_config, skey, filename, filesize, file_md5):
    data = {
        "BaseRequest": {
            "DeviceID": str(device_id),
            "Sid": cookie_dict['wxsid'],
            "Skey": skey,
            "Uin": int(cookie_dict["wxuin"])
        },
        "FileMd5": file_md5,
        "FileName": filename,
        "FileSize": filesize,
        "FileType": 7,
        "FromUserName": user_config['UserName'],
        "ToUserName": "filehelper"
    }
    headers = get_header(filetransfer_domain, "application/json;charset=UTF-8")
    headers['Mmweb_appid'] = "wx_webfilehelper"
    headers['X-Kl-Kfa-Ajax-Request'] = "Ajax_Request"
    res = requests.post(CHECK_UPLOAD_URL, headers=headers, cookies=cookie_dict, json=data)
    print(res.json())
    return res.json()


def webwxsendappmsg(cookie_dict, filename, filesize, mediaid, pass_ticket, skey, user_config, aeskey, signature):
    file_ext = filename.split('.')[-1] if '.' in filename else ''
    params = {
        "fun": "async",
        "f": "json",
        "lang": "zh_CN",
        "pass_tciket": pass_ticket

    }
    base_request = {
        "Uin": cookie_dict['wxuin'],
        "Sid": cookie_dict['wxsid'],
        "Skey": skey,
        "DeviceID": device_id
    }
    msg = {
        "ClientMsgId": generate_client_msg_id(),
        "FromUserName": user_config['UserName'],
        "LocalID": generate_client_msg_id(),
        "ToUserName": "filehelper",
        "Type": 6,
        "Content": f"<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>{filename}</title><des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl><appattach><totallen>{filesize}</totallen><attachid>{mediaid}</attachid><fileext>{file_ext}</fileext></appattach><extinfo></extinfo></appmsg>",
        "AESKey": aeskey,
        "Signature": signature
    }
    url = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxsendappmsg"
    headers = get_header(filetransfer_domain, "application/json;charset=UTF-8")
    headers["Mmweb_appid"] = "wx_webfilehelper"
    res = requests.post(url, headers=headers, cookies=cookie_dict, json={
        "BaseRequest": base_request,
        "Msg": msg,
        "Scene": 0
    }, params=params)
    return res.json()


def upload_parallel(file_path, cookies_dict, user_config, skey, pass_ticket, file_stream=None, filename=None,
                    socketio=None):
    if not file_stream:
        file_size = os.path.getsize(file_path)
        total_chunks = math.ceil(file_size / CHUNK_SIZE)
        file_md5 = get_file_md5(file_path)
        filename = os.path.basename(file_path)
    else:
        file_size = len(file_stream)
        total_chunks = math.ceil(file_size / CHUNK_SIZE)
        file_md5 = get_file_md5(None, file_stream)  # 函数需要适应流
        filename = filename if filename else str(datetime.now().strftime('%Y%m%d%H%M%S') + "_" + random_string(8))

    file_config = get_aes_signature(cookies_dict, user_config, skey, filename, file_size, file_md5)
    result = {}
    upload_request = {
        "Signature": file_config["Signature"],
        "AESKey": file_config["AESKey"],
        "FileMD5": file_md5,
        "TotalLen": int(file_size),
        "Chunks": int(total_chunks),
        "Name": filename,
        "Chunk": 0,
        "BaseRequest": {
            "Uin": int(cookies_dict['wxuin']),
            "Sid": cookies_dict['wxsid'],
            "DeviceID": device_id,
            "Skey": skey
        }
    }

    for chunk_index in range(total_chunks):
        MAX_RETIRES = 5
        for attempt in range(MAX_RETIRES):
            if file_stream is None:
                # 如果没有 file_stream，从文件路径读取
                with open(file_path, "rb") as f:
                    f.seek(chunk_index * CHUNK_SIZE)
                    chunk_data = f.read(CHUNK_SIZE)
            else:
                # 如果有 file_stream，则从流中读取
                chunk_start = chunk_index * CHUNK_SIZE
                chunk_data = file_stream[chunk_start:chunk_start + CHUNK_SIZE]

            upload_request['Chunk'] = chunk_index
            upload_req = json.dumps(upload_request).replace(": ", ":").replace(", ", ",")
            data = {
                "pass_ticket": cookies_dict['webwx_data_ticket'],
                "webwx_data_ticket": cookies_dict['webwx_data_ticket'],
                "UploadMediaParallelRequest": upload_req,
                "filename": ("blob", chunk_data, "application/octet-stream"),
            }

            params = {
                "f": "json",
                "random": random_string()
            }

            headers = get_header(host=file_wx_domain)
            headers["Access-Control-Request-Headers"] = "mmweb_appid"
            headers["Access-Control-Request-Method"] = "POST"
            for inner_attempt in range(3):
                preflight = requests.options(UPLOAD_PARALLEL_BASE, params=params, headers=headers)
                if preflight.status_code == 200:
                    break
                else:
                    params['random'] = random_string()
                if inner_attempt == 2:
                    print(f"❌ Preflight failed after 3 attempts for chunk {chunk_index}")
                    return

            print(f"[{chunk_index + 1}/{total_chunks}] Uploading chunk...")
            if socketio is not None:
                socketio.emit('upload_progress', {
                    'progress': f"{(chunk_index + 1) / total_chunks}"
                })
            multipart_data, content_type = get_form_data_type(data)
            headers = get_header(host=file_wx_domain, content_type=content_type)
            headers['Mmweb_appid'] = 'wx_webfilehelper'
            resp = requests.post(
                UPLOAD_PARALLEL_BASE,
                params=params,
                data=multipart_data,
                headers=headers,
                cookies=cookies_dict,

            )
            result = resp.json()
            print(result)
            if result.get("BaseResponse", {}).get("Ret") == 0:
                # 成功
                if chunk_index == 0:
                    upload_request["UploadID"] = result["UploadID"]
                break
            elif result.get("BaseResponse", {}).get("Ret") == -1:
                if attempt == MAX_RETIRES - 1:
                    return
                print("⚠️ Logic err, retrying...")
                time.sleep(1)
                continue

    webwxsendappmsg(cookie_dict=cookies_dict, filename=filename, filesize=file_size,
                    mediaid=result['MediaId'], pass_ticket=pass_ticket, skey=skey, user_config=user_config,
                    aeskey=file_config["AESKey"], signature=file_config["Signature"])


print("✅ Upload completed.")


def upload_small_file(file_path, cookies_dict, user_config, skey, pass_ticket, file_stream=None, filename=None,
                      socketio=None):
    # 处理文件路径或文件流
    if file_stream is None and file_path is not None:
        # 从文件路径读取
        file_size = os.path.getsize(file_path)
        total_chunks = math.ceil(file_size / CHUNK_SIZE)
        file_md5 = get_file_md5(file_path)
        filename = os.path.basename(file_path)
    elif file_stream is not None:
        # 使用文件流
        file_size = len(file_stream)
        total_chunks = math.ceil(file_size / CHUNK_SIZE)
        file_md5 = get_file_md5(None, file_stream)  # 函数需要适应流
        filename = filename if filename else f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{random_string(8)}"
    else:
        raise ValueError("Either 'file_path' must be provided or 'file_stream' must be given.")

    file_config = get_aes_signature(cookies_dict, user_config, skey, filename, file_size, file_md5)
    result = {}
    client_media_id = generate_client_media_id()

    for chunk_index in range(total_chunks):
        if file_stream is None:
            # 如果没有 file_stream，就从文件中读取数据
            with open(file_path, 'rb') as f:
                f.seek(chunk_index * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)
        else:
            # 如果有 file_stream，则直接计算每个数据块
            chunk_start = chunk_index * CHUNK_SIZE
            chunk_data = file_stream[chunk_start:chunk_start + CHUNK_SIZE]

        upload_media_request = {
            "UploadType": 2,
            "BaseRequest": {
                "Uin": cookies_dict["wxuin"],
                "Sid": cookies_dict["wxsid"],
                "Skey": skey,
                "DeviceID": device_id
            },
            "ClientMediaId": client_media_id,
            "TotalLen": file_size,
            "StartPos": chunk_index * CHUNK_SIZE,
            "DataLen": len(chunk_data),
            "MediaType": 4,
            "FromUserName": user_config["UserName"],
            "ToUserName": "filehelper",
            "FileMd5": file_md5
        }
        upload_media_req = json.dumps(upload_media_request).replace(": ", ":").replace(", ", ",")
        data = {
            "name": filename,
            "lastModifiedDate": time.strftime('%a %b %d %Y %H:%M:%S GMT+0800 (中国标准时间)', time.localtime()),
            "size": str(file_size),
            "type": "",
            "chunks": str(total_chunks),
            "chunk": str(chunk_index),
            "mediatype": "doc",
            "uploadmediarequest": upload_media_req,
            "webwx_data_ticket": cookies_dict['webwx_data_ticket'],
            "pass_ticket": pass_ticket,
            "filename": (filename, chunk_data, mimetypes.guess_type(filename)[0] or "application/octet-stream")
        }

        params = {
            "f": "json",
            "random": random_string()
        }

        headers = get_header(host=file_wx_domain)
        headers["Access-Control-Request-Headers"] = "mmweb_appid"
        headers["Access-Control-Request-Method"] = "POST"
        for attempt in range(3):
            preflight = requests.options(UPLOAD_MEDIA_BASE, params=params, headers=headers)
            if preflight.status_code == 200:
                break
            params['random'] = random_string()
            if attempt == 2:
                print(f"❌ Preflight failed after 3 attempts for chunk {chunk_index}")
                return
        multipart_data, content_type = get_form_data_type(data)
        headers = get_header(host=file_wx_domain, content_type=content_type)
        headers['Mmweb_appid'] = "wx_webfilehelper"

        print(f"📤 Uploading chunk {chunk_index + 1}/{total_chunks}...")
        if socketio is not None:
            socketio.emit('upload_progress', {
                'progress': f"{(chunk_index + 1) / total_chunks}"
            })
        resp = requests.post(UPLOAD_MEDIA_BASE, params=params, data=multipart_data, headers=headers,
                             cookies=cookies_dict)
        try:
            result = resp.json()
            print("✅ Upload success:", result)
        except ValueError:
            print(resp.status_code, resp.text)

    webwxsendappmsg(cookie_dict=cookies_dict, filename=filename, filesize=file_size,
                    mediaid=result['MediaId'], pass_ticket=pass_ticket, skey=skey, user_config=user_config,
                    aeskey=file_config["AESKey"], signature=file_config["Signature"])


def upload_auto_file(file_path, cookies_dict, user_config, skey, pass_ticket, file_stream=None, filename=None,
                     socketio=None):
    if not file_path:
        file_size = len(file_stream)
    else:
        file_size = os.path.getsize(file_path)

    if file_size > 25 * 1024 * 1024:  # 大于25MB，使用并发上传
        print("📦 使用并发上传（webwxuploadmediaparallel）")
        upload_parallel(file_path, cookies_dict, user_config, skey, pass_ticket, file_stream, filename, socketio)
    else:
        print("📄 使用普通上传（webwxuploadmedia）")
        upload_small_file(file_path, cookies_dict, user_config, skey, pass_ticket, file_stream, filename, socketio)

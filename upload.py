import time
import hashlib
import os
import uuid
import math
import mimetypes
import requests
import json

CHUNK_SIZE = 512 * 1024  # 512 KB
UPLOAD_URL = "https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmediaparallel?f=json"
CHECK_URL = "https://filehelper.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxcheckupload?f=json"
UPLOAD_MEDIA_URL = "https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json"


def get_file_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    return md5.hexdigest()


def check_upload(file_path, user_info, pass_ticket, webwx_data_ticket):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)
    filemd5 = get_file_md5(file_path)

    data = {
        "BaseRequest": {
            "Uin": int(user_info["wxuin"]),
            "Sid": user_info["wxsid"],
            "Skey": user_info["skey"],
            "DeviceID": user_info["device_id"]
        },
        "FileName": filename,
        "FileSize": filesize,
        "FileMd5": filemd5,
        "FromUserName": user_info["from"],
        "ToUserName": "filehelper",
        "UploadType": 2,
        "ClientMediaId": int(uuid.uuid4().int >> 64)
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://wx.qq.com",
        "Referer": "https://wx.qq.com/"
    }

    cookies = user_info.get("cookies", {})
    cookies["webwx_data_ticket"] = webwx_data_ticket

    response = requests.post(CHECK_URL, headers=headers, json=data, cookies=cookies)
    return response.json()


def upload_parallel(file_path, user_info, pass_ticket, webwx_data_ticket, aeskey, signature):
    file_size = os.path.getsize(file_path)
    total_chunks = math.ceil(file_size / CHUNK_SIZE)
    file_md5 = get_file_md5(file_path)
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        for chunk_index in range(total_chunks):
            f.seek(chunk_index * CHUNK_SIZE)
            chunk_data = f.read(CHUNK_SIZE)

            upload_request = {
                "BaseRequest": {
                    "Uin": int(user_info["wxuin"]),
                    "Sid": user_info["wxsid"],
                    "Skey": user_info["skey"],
                    "DeviceID": user_info["device_id"]
                },
                "FileMD5": file_md5,
                "TotalLen": file_size,
                "Chunks": total_chunks,
                "Chunk": chunk_index,
                "Name": filename,
                "AESKey": aeskey,
                "Signature": signature
            }

            files = {
                "filename": (
                    filename,
                    chunk_data,
                    mimetypes.guess_type(filename)[0] or "application/octet-stream"
                )
            }

            data = {
                "UploadMediaParallelRequest": json.dumps(upload_request, ensure_ascii=False),
                "webwx_data_ticket": webwx_data_ticket,
                "pass_ticket": pass_ticket
            }

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://wx.qq.com/",
                "Origin": "https://wx.qq.com"
            }

            print(f"[{chunk_index + 1}/{total_chunks}] Uploading chunk...")
            resp = requests.post(
                UPLOAD_URL,
                data=data,
                files=files,
                headers=headers,
                cookies=user_info.get("cookies")
            )
            try:
                print(resp.json())
            except:
                print(resp.status_code, resp.text)

    print("✅ Upload completed.")


def upload_file_with_signature(file_path, user_info, pass_ticket, webwx_data_ticket):
    check_result = check_upload(file_path, user_info, pass_ticket, webwx_data_ticket)
    if check_result.get("BaseResponse", {}).get("Ret") != 0:
        print("❌ check_upload failed:", check_result)
        return

    aeskey = check_result.get("AESKey", "")
    signature = check_result.get("Signature", "")
    upload_parallel(file_path, user_info, pass_ticket, webwx_data_ticket, aeskey, signature)


def upload_small_file(file_path, user_info, pass_ticket, webwx_data_ticket):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)
    filemd5 = get_file_md5(file_path)

    with open(file_path, 'rb') as f:
        file_content = f.read()

    client_media_id = int(time.time() * 1000)

    upload_media_request = {
        "UploadType": 2,
        "BaseRequest": {
            "Uin": int(user_info["wxuin"]),
            "Sid": user_info["wxsid"],
            "Skey": user_info["skey"],
            "DeviceID": user_info["device_id"]
        },
        "ClientMediaId": client_media_id,
        "TotalLen": filesize,
        "StartPos": 0,
        "DataLen": filesize,
        "MediaType": 4,
        "FromUserName": user_info["from"],
        "ToUserName": "filehelper",
        "FileMd5": filemd5
    }

    files = {
        "filename": (
            filename,
            file_content,
            mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
    }

    data = {
        "name": filename,
        "lastModifiedDate": time.strftime('%a %b %d %Y %H:%M:%S GMT+0800 (中国标准时间)', time.localtime()),
        "size": str(filesize),
        "type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
        "mediatype": "doc",
        "uploadmediarequest": json.dumps(upload_media_request, ensure_ascii=False),
        "webwx_data_ticket": webwx_data_ticket,
        "pass_ticket": pass_ticket
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://wx.qq.com/",
        "Origin": "https://wx.qq.com"
    }

    cookies = user_info.get("cookies", {})
    cookies["webwx_data_ticket"] = webwx_data_ticket

    print("📤 Uploading small file...")
    resp = requests.post(UPLOAD_MEDIA_URL, data=data, files=files, headers=headers, cookies=cookies)
    try:
        result = resp.json()
        print("✅ Upload success:", result)
        return result
    except:
        print(resp.status_code, resp.text)
        return None

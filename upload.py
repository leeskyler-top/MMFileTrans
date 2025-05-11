import time
import hashlib
import os
import math
import mimetypes
import random
import string
import requests
import json

from LoadEnviroment.LoadEnv import file_wx_baseurl, filetransfer_baseurl, file_wx_domain
from utils.Generate import get_header
from utils.LoadJson import get_aegis_id
from utils.ParseData import get_form_data_type

CHUNK_SIZE = 512 * 1024  # 512 KB
UPLOAD_MEDIA_BASE = f"{file_wx_baseurl}/cgi-bin/mmwebwx-bin/webwxuploadmedia"
UPLOAD_PARALLEL_BASE = f"{file_wx_baseurl}/cgi-bin/mmwebwx-bin/webwxuploadmediaparallel"
CHECK_UPLOAD_URL = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxcheckupload?f=json"
aid, uin, session_id, device_id, report_id = get_aegis_id()


def random_string(length=4):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_file_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    return md5.hexdigest()


def upload_parallel(file_path, cookies_dict, aeskey, signature, pass_ticket):
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
                    "Uin": cookies_dict["wxuin"],
                    "Sid": cookies_dict["wxsid"],
                    "Skey": cookies_dict["skey"],
                    "DeviceID": device_id
                },
                "FileMD5": file_md5,
                "TotalLen": file_size,
                "Chunks": total_chunks,
                "Chunk": chunk_index,
                "Name": filename,
                "AESKey": aeskey,
                "Signature": signature
            }

            data = {
                "UploadMediaParallelRequest": json.dumps(upload_request, ensure_ascii=False),
                "webwx_data_ticket": cookies_dict['webwx_data_ticket'],
                "pass_ticket": pass_ticket,
                "filename": (filename, chunk_data, mimetypes.guess_type(filename)[0] or "application/octet-stream")
            }

            params = {
                "f": "json",
                "random": random_string()
            }

            headers = get_header(host=file_wx_domain)
            headers["Access-Control-Request-Headers"] = "mmweb_appid",
            headers["Access-Control-Request-Method"] = "POST",
            for attempt in range(3):
                preflight = requests.options(UPLOAD_PARALLEL_BASE, params=params, headers=headers)
                if preflight.status_code == 200:
                    break
                if attempt == 2:
                    print(f"❌ Preflight failed after 3 attempts for chunk {chunk_index}")
                    return

            print(f"[{chunk_index + 1}/{total_chunks}] Uploading chunk...")
            multipart_data, content_type = get_form_data_type(data)
            headers = get_header(host=file_wx_domain, content_type=content_type)
            headers['Mmweb_appid'] = 'wx_webfilehelper'
            resp = requests.post(
                UPLOAD_PARALLEL_BASE,
                params=params,
                data=multipart_data,
                headers=headers,
                cookies=cookies_dict
            )
            try:
                print(resp.json())
            except:
                print(resp.status_code, resp.text)

    print("✅ Upload completed.")


def upload_small_file(file_path, cookies_dict, from_user_name, pass_ticket):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)
    filemd5 = get_file_md5(file_path)
    total_chunks = math.ceil(filesize / CHUNK_SIZE)

    with open(file_path, 'rb') as f:
        for chunk_index in range(total_chunks):
            f.seek(chunk_index * CHUNK_SIZE)
            chunk_data = f.read(CHUNK_SIZE)

            client_media_id = int(time.time() * 1000)

            upload_media_request = {
                "UploadType": 2,
                "BaseRequest": {
                    "Uin": cookies_dict["wxuin"],
                    "Sid": cookies_dict["wxsid"],
                    "Skey": cookies_dict["skey"],
                    "DeviceID": device_id
                },
                "ClientMediaId": client_media_id,
                "TotalLen": filesize,
                "StartPos": chunk_index * CHUNK_SIZE,
                "DataLen": len(chunk_data),
                "MediaType": 4,
                "FromUserName": from_user_name,
                "ToUserName": "filehelper",
                "FileMd5": filemd5
            }

            data = {
                "name": filename,
                "lastModifiedDate": time.strftime('%a %b %d %Y %H:%M:%S GMT+0800 (中国标准时间)', time.localtime()),
                "size": str(filesize),
                "type": "",
                "chunks": str(total_chunks),
                "chunk": str(chunk_index),
                "mediatype": "doc",
                "uploadmediarequest": json.dumps(upload_media_request, ensure_ascii=False),
                "webwx_data_ticket": cookies_dict['webwx_data_ticket'],
                "pass_ticket": pass_ticket,
                "filename": (filename, chunk_data, mimetypes.guess_type(filename)[0] or "application/octet-stream")
            }

            params = {
                "f": "json",
                "random": random_string()
            }

            headers = get_header(host=file_wx_domain)
            headers["Access-Control-Request-Headers"] = "mmweb_appid",
            headers["Access-Control-Request-Method"] = "POST",
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
            resp = requests.post(UPLOAD_MEDIA_BASE, params=params, data=multipart_data, headers=headers,
                                 cookies=cookies_dict)
            try:
                result = resp.json()
                print("✅ Upload success:", result)
            except:
                print(resp.status_code, resp.text)

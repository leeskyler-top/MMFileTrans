import io
import json
import re
import time
import os
import uuid
import random
from datetime import datetime, timedelta
import numpy as np

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from LoadEnviroment.LoadEnv import aegis_id_json_path, sec_ch_ua, user_agent, filetransfer_domain, expiry_duration_sec, \
    filetransfer_baseurl, cookie_path

import xml.etree.ElementTree as ET


def get_form_data_type(data):
    # 使用 MultipartEncoder 构造 multipart/form-data
    multipart_data = MultipartEncoder(fields=data)
    return multipart_data, multipart_data.content_type


def random_base36(length=11):
    # 生成随机 Base36 字符串
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(chars) for _ in range(length))


def generate_deviceid():
    # 生成一个0到1之间的随机浮点数
    random_float = random.random()

    # 格式化为15位小数的字符串
    formatted_str = f"{random_float:.15f}"

    # 提取从索引2到17之间的子字符串
    random_string = formatted_str[2:17]
    return random_string


def generate_aegis(expiry_duration: int = 86400):
    # 如果不存在或者过期则生成新的 aegis_id 和 uin
    aid = str(uuid.uuid4())
    # report_id = random_base36()
    report_id = "neGcmxiTIeDBcIOiWX"
    uin = random_base36()
    expiry = time.time() + expiry_duration  # 设置新的 expiry
    timestamp_ms = int(time.time() * 1000)
    device_id = generate_deviceid()

    try:
        with open(aegis_id_json_path, "w") as f:
            data = {
                "aegis_id": aid,
                "uin": uin,
                "session_id": f"session-{timestamp_ms}",
                "device_id": device_id,
                "report_id": report_id,
                "expiry": expiry  # 保存新的 expiry
            }
            print(device_id)
            json.dump(data, f)
        return aid, uin, f"session-{timestamp_ms}", device_id, report_id  # 返回新的 aegis_id 和 uin
    except Exception as e:
        print(f"Error saving AEGIS_ID: {e}")
        return None, None, None, None, None  # 返回 None 值以指示错误


def get_aegis_id():
    if os.path.exists(aegis_id_json_path):
        with open(aegis_id_json_path, "r") as f:
            storage = json.load(f)
            if "aegis_id" in storage and "uin" in storage and "session_id" in storage and "expiry" in storage:
                current_time = time.time()
                if current_time < storage["expiry"]:  # 检查是否过期
                    return storage["aegis_id"], storage["uin"], storage["session_id"], storage["device_id"], storage[
                        'report_id']
                return generate_aegis(expiry_duration_sec)
            return generate_aegis(expiry_duration_sec)
    return generate_aegis(expiry_duration_sec)


def get_header(host, content_type=None, referer=filetransfer_baseurl):
    header = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": content_type,
        "Host": host,
        "Referer": filetransfer_baseurl,
        "Origin": filetransfer_baseurl,
        "Sec-Ch-Ua": sec_ch_ua,
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "User-Agent": user_agent
    }
    if not content_type:
        del header["Content-Type"]
    return header


def checkCookieExpired(cookies=None, white_list: list = []):
    if not cookies:
        return True

    for cookie in cookies:
        if cookie['name'] in white_list:
            continue
        expiry_time = cookie.get('expiry')
        # is_http_only = cookie.get('httpOnly', False)

        if expiry_time and expiry_time <= time.time():
            print(f"cookie '{cookie['name']}' has expired.")
            return True

    return False


def save_cookies_as_json(cookies, skey, expires_sec: int):
    cookies_list = []
    expiry_time = datetime.now() + timedelta(seconds=expires_sec)

    for cookie_name, cookie_value in cookies.items():
        current_cookie = {
            "domain": filetransfer_domain,  # 设置你的域名
            "httpOnly": True,  # 根据需要设置
            "name": cookie_name,
            "path": "/",
            "secure": False,  # 根据需要设置
            "value": cookie_value,
            "expiry": int(expiry_time.timestamp())
        }
        cookies_list.append(current_cookie)
        cookies_list.append({
            "domain": filetransfer_domain,  # 设置你的域名
            "httpOnly": True,  # 根据需要设置
            "name": "skey",
            "path": "/",
            "secure": False,  # 根据需要设置
            "value": skey,
            "expiry": int(expiry_time.timestamp())
        })
    # 保存 cookies 到文件
    try:
        with open(cookie_path, 'w') as file:
            json.dump(cookies_list, file, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cookies: {e}")

    print(f"Cookies have been saved to {cookie_path}")
    return {cookie['name']: cookie['value'] for cookie in cookies_list}


def load_cookies_from_json():
    try:
        if os.path.exists(cookie_path):
            with open(cookie_path, 'r') as file:
                cookies_list = json.load(file)
                if checkCookieExpired(cookies_list):
                    return None
                for cookie in cookies_list:
                    if cookie['name'] == 'skey':
                        skey = cookie['value']
            return {cookie['name']: cookie['value'] for cookie in cookies_list if cookie['name'] != 'skey'}, skey
        return None, None
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return None, None


def parse_webwxnewloginpage_response(response_text: str):
    """
    解析 webwxnewloginpage 的 text/plain 响应体，提取 skey 等信息。
    """
    try:
        root = ET.fromstring(response_text)
        result = {
            'skey': root.findtext('skey'),
            'wxsid': root.findtext('wxsid'),
            'wxuin': root.findtext('wxuin'),
            'pass_ticket': root.findtext('pass_ticket'),
            'isgrayscale': root.findtext('isgrayscale'),
        }
        return result
    except ET.ParseError as e:
        print(f"[parse_webwxnewloginpage_response] XML解析失败: {e}")
        return None


def parse_jslogin_response(js_text):
    """
    解析 jslogin 接口返回的 JS 代码，提取 code 和 redirect_uri。
    示例输入：
      window.code = 200;
      window.redirect_uri = "https://....";

    返回：
      {
          "code": 200,
          "redirect_uri": "https://...."
      }
    如果没有 code，返回 None。
    """
    code_match = (re.search(r'window\.code\s*=\s*(\d+);', js_text).group(1)
                  if re.search(r'window\.code\s*=\s*(\d+);', js_text) else None)

    redirect_match = (re.search(r'window\.redirect_uri\s*=\s*"([^"]+)"', js_text).group(1)
                      if re.search(r'window\.redirect_uri\s*=\s*"([^"]+)"', js_text) else None)

    return code_match, redirect_match


def download_img(image_url, show_img=False, show_time_ms=7000):
    # 使用 requests 下载图片数据
    resp = requests.get(image_url)
    if resp.status_code != 200:
        return "Failed to fetch image", 502

    # 将 JPEG 图片数据加载到内存中
    image_bytes = io.BytesIO(resp.content)
    if show_img:
        import cv2
        img_array = np.frombuffer(image_bytes.getvalue(), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # img 就是 OpenCV 图像对象
        cv2.imshow("qrcode", img)
        cv2.waitKey(show_time_ms)
        cv2.destroyAllWindows()
    else:
        return image_bytes

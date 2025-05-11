import json
import time
import os
from datetime import datetime, timedelta
from LoadEnviroment.LoadEnv import filetransfer_domain, cookie_path


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


def save_cookies_as_json(cookies, skey, pass_ticket, expires_sec: int, save_cookie_path=cookie_path):
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
        cookies_list.append({
            "domain": filetransfer_domain,  # 设置你的域名
            "httpOnly": True,  # 根据需要设置
            "name": "pass_ticket",
            "path": "/",
            "secure": False,  # 根据需要设置
            "value": pass_ticket,
            "expiry": int(expiry_time.timestamp())
        })
    # 保存 cookies 到文件
    try:
        with open(save_cookie_path, 'w') as file:
            json.dump(cookies_list, file, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cookies: {e}")

    print(f"Cookies have been saved to {save_cookie_path}")
    return {cookie['name']: cookie['value'] for cookie in cookies_list}


def load_cookies_from_json(load_cookie_path=cookie_path):
    try:
        if os.path.exists(load_cookie_path):
            with open(load_cookie_path, 'r') as file:
                cookies_list = json.load(file)
                if checkCookieExpired(cookies_list):
                    return None, None, None
                for cookie in cookies_list:
                    if cookie['name'] == 'skey':
                        skey = cookie['value']
                    if cookie['name'] == 'pass_ticket':
                        pass_ticket = cookie['value']
            return {cookie['name']: cookie['value'] for cookie in cookies_list if
                    cookie['name'] != 'skey' and cookie['name'] != 'pass_ticket'}, skey, pass_ticket
        return None, None, None
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return None, None, None

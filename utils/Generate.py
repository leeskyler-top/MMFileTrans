import json
import time
import uuid
import random
import string

from LoadEnviroment.LoadEnv import aegis_id_json_path, sec_ch_ua, user_agent, \
    filetransfer_baseurl


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


def random_string(length=4):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

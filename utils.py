import json
import os
import uuid

from LoadEnviroment.LoadEnv import aegis_id_json_path, sec_ch_ua, user_agent, filetransfer_domain


def get_aegis_id():
    if os.path.exists(aegis_id_json_path):
        with open(aegis_id_json_path, "r") as f:
            storage = json.load(f)
            if "aegis_id" in storage:
                return storage["aegis_id"]
    else:
        aid = uuid.uuid4()
        try:
            with open(aegis_id_json_path, "w") as f:
                data = {
                    "aegis_id": str(aid)
                }
                json.dump(data, f)
            return aid
        except Exception as e:
            print(f"Error saving AEGIS_ID: {e}")


def get_header(host, content_type=None):
    header = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": content_type,
        "Host": host,
        "Referer": f"https://{filetransfer_domain}",
        "Sec-Ch-Ua": sec_ch_ua,
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "User-Agent": user_agent
    }
    if not content_type:
        del header["Content-Type"]
    return header

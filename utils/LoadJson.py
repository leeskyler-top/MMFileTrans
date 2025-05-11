import json
import time
import os

from LoadEnviroment.LoadEnv import aegis_id_json_path, expiry_duration_sec
from utils.Generate import generate_aegis


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

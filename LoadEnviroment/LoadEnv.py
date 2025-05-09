import json
import os

aegis_id_json_path = "./aegis_report_id.json"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
sec_ch_ua = "Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\""
filetransfer_domain = "filehelper.weixin.qq.com"
filetransfer_baseurl = "https://filehelper.weixin.qq.com"
aegis_report_id = "neGcmxiTIeDBcIOiWX"
aegis_uin = "hpvbrapn64s"
aegis_domain = "aegis.qq.com"
aegis_baseurl = "https://aegis.qq.com"
aegis_version = "1.36.0"


def load_env(filepath):
    global aegis_report_id_json_path, user_agent, sec_ch_ua, \
        aegis_report_id

    with open(filepath, 'r') as f:
        data = json.load(f)
        aegis_report_id_json_path = data['aegis_id_json_path']
        user_agent = data['user_agent']
        aegis_report_id = data['aegis_report_id']


_default_env_path = os.path.join(os.getcwd(), '.env.json')
print(_default_env_path)
if os.path.exists(_default_env_path):
    print("Successfully loaded .env.json")
    load_env(_default_env_path)

import json
import os

aegis_report_id = "neGcmxiTIeDBcIOiWX"
aegis_id_json_path = "./aegis_report_id.json"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
sec_ch_ua = "Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\""
filetransfer_domain = "filehelper.weixin.qq.com"
filetransfer_baseurl = "https://filehelper.weixin.qq.com"
aegis_domain = "aegis.qq.com"
aegis_baseurl = "https://aegis.qq.com"
aegis_version = "1.36.0"
wechat_login_domain = "login.wx2.qq.com"
wechat_login_baseurl = "https://login.wx2.qq.com"
file_domain = "file.weixin.qq.com"
file_baseurl = "https://file.weixin.qq.com"
file_wx_domain = "file.wx.qq.com"
file_wx_baseurl = "https://file.wx.qq.com"
szfiletransfer_domain = "szfilehelper.weixin.qq.com"
szfiletransfer_baseurl = "https://szfilehelper.weixin.qq.com"
expiry_duration_sec = 86400
cookie_path = "./micromsg.json"


def load_env(filepath):
    global aegis_report_id_json_path, user_agent, sec_ch_ua, \
        expiry_duration_sec, cookie_path

    with open(filepath, 'r') as f:
        data = json.load(f)
        aegis_report_id_json_path = data['aegis_id_json_path']
        user_agent = data['user_agent']
        expiry_duration_sec = data['expiry_duration_sec']
        cookie_path = data['cookie_path']
        aegis_report_id = data['aegis_report_id']


_default_env_path = os.path.join(os.getcwd(), '.env.json')
print(_default_env_path)
if os.path.exists(_default_env_path):
    print("Successfully loaded .env.json")
    load_env(_default_env_path)

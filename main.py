import random
import ssl
import time
import requests
import urllib3
from requests.adapters import HTTPAdapter

from LoadEnviroment.LoadEnv import user_agent, sec_ch_ua, filetransfer_domain, filetransfer_baseurl, aegis_baseurl, \
    aegis_version, aegis_domain, wechat_login_baseurl, wechat_login_domain, szfiletransfer_domain, \
    szfiletransfer_baseurl
from utils import get_header, get_aegis_id, get_form_data_type, save_cookies_as_json, parse_webwxnewloginpage_response, \
    parse_jslogin_response, download_img, load_cookies_from_json


class CustomHttpAdapter(HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_new_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
    ctx.check_hostname = False
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session


def reqApi(session, url: str, headers: dict, method: str = "GET", json: dict = None, params: dict = None,
           data=None, cookie_dict=None, allow_redirect=True) -> requests.models.Response:
    """
    :param url: API名称
    :type url: str
    :param method: 请求方式
    :type method: str
    :param json: application/json Body Payload
    :type json: dict
    :param params: Params参数
    :type params: dict
    :param headers: 请求头
    :type headers: dict

    :return: req.json()
    :rtype: dict
    """
    if not json:
        json = {}
    if method == "GET" and not params:
        session = session.get(url, headers=headers, cookies=cookie_dict, allow_redirects=allow_redirect)
        return session
    elif method == "GET" and params:
        session = session.get(url, headers=headers, params=params, cookies=cookie_dict, allow_redirects=allow_redirect)
        return session
    elif method == "POST":
        if data is not None:
            session = session.post(url, data=data, headers=headers, params=params, cookies=cookie_dict, allow_redirects=allow_redirect)
        else:
            session = session.post(url, headers=headers, json=json, params=params, cookies=cookie_dict, allow_redirects=allow_redirect)
        return session
    elif method == "PATCH":
        # 注意这里没有json.dumps, 自己传的时候json.dumps()一下
        session = session.patch(url, headers=headers, json=json, cookies=cookie_dict, allow_redirects=allow_redirect)
        return session


def webwxstatreport(session, data=None):
    # 登录时Action设为3
    url = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxstatreport"
    if not data:
        data = {
            "mmweb_appid": "xxx",
            "sid": "xxx",
            "skey": "xxx",
            "pass_ticket": "xxx",
            "Action": "1",
            "ExitSource": "6"
        }
    params = {
        "sid": None,
        "skey": None,
        "pass_ticket": None,
    }
    data, content_type = get_form_data_type(data)
    headers = get_header(host=filetransfer_domain, content_type=content_type)
    headers['Mmweb_appid'] = 'wx_webfilehelper'
    reqApi(session, url, headers, "POST", params=params, data=data)


def whitelist(session):
    url = f"{aegis_baseurl}/collect/whitelist"
    aid, uin, session_id, device_id, report_id = get_aegis_id()
    url = f'https://aegis.qq.com/collect/whitelist?id=neGcmxiTIeDBcIOiWX&uin=2sn4oyl4n37&version=1.36.0&aid=a0467acb-97cf-49fa-9acb-a987bb549172&env=production&platform=3&netType=4&vp=210%20*%20742&sr=1536%20*%20864&sessionId=session-1746804015703&from=https%3A%2F%2Ffilehelper.weixin.qq.com%2F&referer='
    params = {
        "id": report_id,
        "uin": uin,
        "version": aegis_version,
        "aid": aid,
        "env": "production",
        "platform": "3",
        "netType": "4",
        "vp": "855 * 742",
        "sr": "1536 * 864",
        "sessionId": session_id,
        "from": "https://filehelper.weixin.qq.com/",
        "referer": None,
    }

    print(params)
    headers = get_header(host=aegis_domain, content_type=None)
    session = reqApi(session, url, headers, "GET")
    print(f"whitelist: {session.status_code}")


def speed(session, qrcode_url, duration, uin=None):
    url = f"{aegis_baseurl}/collect/whitelist"
    aid, origin_uin, session_id, device_id, report_id = get_aegis_id()
    if not uin:
        uin = origin_uin
    params = {
        "id": report_id,
        "uin": uin,
        "version": aegis_version,
        "aid": aid,
        "env": "production",
        "platform": "3",
        "netType": "4",
        "vp": "855 * 742",
        "sr": "1536 * 864",
        "sessionId": session_id,
        "from": "https://filehelper.weixin.qq.com/",
        "referer": None,
    }
    payload = str(
        {
            'duration': {
                'fetch': [],
                'static': [
                    {
                        'url': f'{qrcode_url}',
                        'method': 'get',
                        'duration': f"{duration}",
                        'status': "200",
                        'type': 'static',
                        'isHttps': "true",
                        'urlQuery': '',
                        'domainLookup': '0',
                        'connectTime': '0'
                    }
                ]
            },
            'id': 'neGcmxiTIeDBcIOiWX',
            'uin': '485z5s4q64z',
            'version': '1.36.0',
            'aid': aid,
            'env': 'production',
            'platform': "3",
            'netType': "4",
            'vp': '694 * 742',
            'sr': '1536 * 864',
            'sessionId': session_id,
            'from': 'https://szfilehelper.weixin.qq.com/',
            'referer': ''
        }
    )
    form_data, content_type = get_form_data_type({'payload': payload})
    print(duration)
    headers = get_header(host=aegis_domain, content_type=content_type)
    session = reqApi(session, url, headers, "GET", params=params, data=form_data)
    print(f"speed: {session.status_code}")


# 拿login uuid 做二维码后缀
def jslogin(session):
    url = f"{wechat_login_baseurl}/jslogin"
    timestamp_ms = int(time.time() * 1000)
    params = {
        "appid": "wx_webfilehelper",
        "redirect_uri": "https%3A%2F%2Fszfilehelper.weixin.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage",
        "fun": "new",
        "lang": "zh_CN",
        "_": f"{timestamp_ms}"
    }
    headers = get_header(host=wechat_login_domain)
    session = reqApi(session, url, headers, "POST", params=params)
    print(f"get login uuid: {session.status_code}, text: {session.text}")
    return session.text.split(' ')[-1].replace(';', "").replace('"', "").replace("'", "").replace(" ", "").strip()


# speed("https://login.weixin.qq.com/qrcode/YfGT4ER6IQ==", round(random.uniform(60,120), 1))

def login(session, uuid):
    url = f"{wechat_login_baseurl}/cgi-bin/mmwebwx-bin/login"
    timestamp_ms = int(time.time() * 1000)
    params = {
        "loginicon": "true",
        "uuid": uuid,
        "tip": "1",
        "r": "1286961880",
        "_": f"{timestamp_ms}",
        "appid": "wx_webfilehelper"
    }
    headers = get_header(host=wechat_login_domain)
    session = reqApi(session, url, headers, "POST", params=params)
    print(f"try_login: {session.status_code}, text: {session.text}")
    code, redirect_uri = parse_jslogin_response(session.text)
    return code, redirect_uri


# 该操作将Set-Cookie!
def webwxnewloginpage(session, redirect_url):
    headers = get_header(host=filetransfer_domain)
    headers['Mmweb_appid'] = 'wx_webfilehelper'
    res = reqApi(session, redirect_url, headers, "POST", allow_redirect=False)
    print(res.cookies.get_dict())
    login_data = parse_webwxnewloginpage_response(res.text)
    cookie_dict = save_cookies_as_json(res.cookies.get_dict(), login_data['skey'], 6000)
    print(cookie_dict)
    reqApi(session, filetransfer_baseurl, headers=headers, allow_redirect=False)
    return cookie_dict, login_data['skey']


def webwxinit(session, pass_ticket, skey, cookie_dict):
    url = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxinit"
    params = {
        "r": cookie_dict['wxloadtime'],
        "lang": "zh_CN",
        "pass_ticket": pass_ticket
    }
    aid, uin, session_id, device_id, report_id = get_aegis_id()
    data = {
        "BaseRequest": {
            "Uin": cookie_dict['wxuin'],
            "Sid": cookie_dict['wxsid'],
            "Skey": skey,
            "DeviceID": device_id
        }
    }
    header = get_header(filetransfer_domain)
    header['Mmweb_appid'] = 'wx_webfilehelper'
    req = reqApi(session, url, header, "POST", params=params, data=data, cookie_dict=cookie_dict)
    print(f"webwxinit: {req.status_code}")
    print(req.text)
    return req


def run_login():
    session = get_new_session()
    cookies_dict, skey = load_cookies_from_json()
    if cookies_dict:
        return session, cookies_dict, skey
    whitelist(session)
    webwxstatreport(session)

    MAX_WAITING_COUNT = 20


    while True:
        # 获取二维码 UUID
        login_uuid = jslogin(session)
        if not login_uuid:
            return  # 处理 UUID 获取失败的情况

        qrcode_url = f"https://login.weixin.qq.com/qrcode/{login_uuid}"
        # 调用 speed 请求
        speed(session, qrcode_url=qrcode_url, duration=round(random.uniform(70, 120), 1))
        # 下载二维码图片
        download_img(qrcode_url, show_img=True)

        waiting_count = 0  # 在每次新的二维码扫描之前重置计数器
        while waiting_count < MAX_WAITING_COUNT:
            time.sleep(1)  # 等待1秒
            code, redirect_url = login(session, login_uuid)

            if code == '200':  # 登录成功
                cookies_dict, skey = webwxnewloginpage(session, redirect_url)
                webwxinit(session, pass_ticket=cookies_dict['webwx_data_ticket'], skey=skey, cookie_dict=cookies_dict)
                return session, cookies_dict, skey # 成功后退出
            elif code == '201':  # 已扫码，待确认
                waiting_count += 1
                continue  # 继续等待二维码确认
            break

        # 如果达到最大等待次数，重新获取二维码 UUID
        print("Waiting for confirmation timed out, generating a new QR code...")
        # 此处会自动回到外层循环，获取新的 UUID 和二维码

if __name__ == "__main__":
    session, cookies_dict, skey = run_login()
    print(skey)

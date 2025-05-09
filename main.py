import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from LoadEnviroment.LoadEnv import user_agent, sec_ch_ua, filetransfer_domain, filetransfer_baseurl, aegis_baseurl, \
    aegis_version, aegis_uin, aegis_report_id, aegis_domain
from utils import get_header, get_aegis_id

timestamp_ms = int(time.time() * 1000)

def get_form_data_type(data):
    # 使用 MultipartEncoder 构造 multipart/form-data
    multipart_data = MultipartEncoder(fields=data)
    return multipart_data, multipart_data.content_type


def reqApi(url: str, headers: dict, method: str = "GET", json: dict = None, params: dict = None,
           data=None) -> requests.models.Response:
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
        req = requests.get(url, headers=headers)
        return req
    elif method == "GET" and params:
        req = requests.get(url, headers=headers, params=params)
        return req
    elif method == "POST":
        if data is not None:
            req = requests.post(url, data=data, headers=headers, params=params)
        else:
            req = requests.post(url, headers=headers, json=json, params=params)
        return req
    elif method == "PATCH":
        # 注意这里没有json.dumps, 自己传的时候json.dumps()一下
        req = requests.patch(url, headers=headers, json=json)
        return req


def webwxstatreport():
    url = f"{filetransfer_baseurl}/cgi-bin/mmwebwx-bin/webwxstatreport"
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
    reqApi(url, headers, "POST", params=params, data=data)


def whitelist():
    url = f"{aegis_baseurl}/collect/whitelist"
    aid = get_aegis_id()
    params = {
        "id": aegis_report_id,
        "uin": aegis_uin,
        "version": aegis_version,
        "aid": aid,
        "env": "production",
        "platform": "3",
        "netType": "4",
        "vp": "855 * 742",
        "sr": "1536 * 864",
        "sessionId": f"session-{timestamp_ms}",
        "from": "https://filehelper.weixin.qq.com/",
        "referer": None,
    }
    headers = get_header(host=aegis_domain, content_type=None)
    reqApi(url, headers, "GET", params=params)

whitelist()

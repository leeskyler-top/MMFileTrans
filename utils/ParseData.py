import io
import re
import requests
import numpy as np

from requests_toolbelt.multipart.encoder import MultipartEncoder
import xml.etree.ElementTree as ET


def get_form_data_type(data):
    # 使用 MultipartEncoder 构造 multipart/form-data
    multipart_data = MultipartEncoder(fields=data)
    # print("------ BEGIN RAW MULTIPART FORM ------")
    # print(multipart_data.to_string().decode('utf-8', errors='replace'))  # 输出原始 body 内容
    # print("------ END RAW MULTIPART FORM ------")
    # print("Content-Type Header:\n", multipart_data.content_type)
    return multipart_data, multipart_data.content_type


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


def download_img(session, image_url, show_img=False, show_time_ms=7000):
    # 使用 requests 下载图片数据
    resp = session.get(image_url)
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

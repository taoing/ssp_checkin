"""
ssp checkin(机场签到)
"""
import os
import sys
import logging
import json

import requests
from urllib import parse

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" \
             "90.0.4430.212 Safari/537.36 Edg/90.0.818.62"


class SSPCheckin:

    def __init__(self, web_name, web_home, login_url, checkin_url, logout_url, login_is_json, account, password,
                 bark_key, bark_sound):
        self.web_name = web_name
        self.web_home = web_home
        self.login_url = login_url
        self.checkin_url = checkin_url
        self.logout_url = logout_url
        self.login_is_json = login_is_json
        self.account = account
        self.password = password
        self.bark_key = bark_key
        self.bark_sound = bark_sound
        self.all_message = ""

    def checkin(self):
        s = requests.session()
        s.headers['User-Agent'] = USER_AGENT
        # 登录
        login_url = self.web_home + self.login_url
        login_data = {
            "email": self.account,
            "passwd": self.password
        }
        if self.login_is_json:
            resp = s.post(login_url, json=login_data)
        else:
            resp = s.post(login_url, data=login_data)
        if resp.status_code != requests.codes.ok:
            self.all_message += f"登录失败, 状态码: {resp.status_code}\n"
            logging.error(f"{self.web_name}{self.all_message}")
        else:
            body = resp.json()
            logging.info(f"{self.web_name}登录结果: {body}")
            self.all_message += "登录结果: " + body.get("msg") + "\n"

            # 签到
            checkin_url = self.web_home + self.checkin_url
            resp = s.post(checkin_url)
            if resp.status_code != requests.codes.ok:
                logging.info(f"{self.web_name} 签到失败, 状态码: {resp.status_code}")
                self.all_message += f"签到失败, 状态码: {resp.status_code}\n"
            else:
                body = resp.json()
                logging.info(f"{self.web_name}签到结果: {body}")
                self.all_message += "签到结果: " + body.get("msg") + "\n"
            # 登出
            logout_url = self.web_home + self.logout_url
            resp = s.get(logout_url)
            if resp.status_code != requests.codes.ok:
                logging.info(f"{self.web_name}登出失败, 请求状态码: {resp.status_code}")
                self.all_message += f"登出失败, 请求状态码: {resp.status_code}"
            else:
                logging.info(f"{self.web_name}登出成功")
                self.all_message += "登出成功"

        s.close()
        self.notify()

    def notify(self):
        """
        发送bark app消息通知
        """
        bark_url = "https://api.day.app/{}/{}/{}?sound={}".format(self.bark_key, parse.quote(f"{self.web_name}签到结果"),
                                                                  parse.quote(self.all_message), self.bark_sound)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            r = requests.get(url=bark_url, headers=headers)
        except Exception as ex:
            logging.info(f"Bark App发送通知调用api失败: {ex}")
            return

        if r.status_code == 200:
            logging.info("Bark APP发送通知消息成功")
        else:
            logging.info("Bark App发送通知失败: %s-%s", r.status_code, r.text)


def main():
    checkin_config = os.environ.get("CHECKIN_CONFIG")
    if not checkin_config:
        logging.error("请先配置签到配置环境变量: CHECKIN_CONFIG")
        return
    config = json.loads(checkin_config)
    for item in config:
        task = SSPCheckin(item["web_name"], item["web_home"], item["login_url"], item["checkin_url"],
                          item["logout_url"], item["login_is_json"], item["account"], item["password"],
                          item["bark"]["key"], item["bark"]["sound"])
        task.checkin()


if __name__ == "__main__":
    main()

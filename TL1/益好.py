# -*- coding: utf-8 -*-
import requests
import os
import time
from datetime import datetime

"""
小程序：益好定制 签到V1.2
变量名：yh_gpt (格式：备注1#Authorization1&备注2#Authorization2)
功能：自动签到 + 实时积分查询
定时：cron 5 6 * * * 一天一次自行修改
"""

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def qywx_push(title, content):
    """【硬核推送】直接对接企业微信机器人"""
    key = os.getenv("QYWX_KEY")
    if not key:
        log("⚠️ 未检测到 QYWX_KEY，跳过推送。")
        return
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"📜 {title}\n{'-'*20}\n{content}"
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        if res.get("errcode") == 0:
            log("🔔 企业微信推送成功！")
        else:
            log(f"❌ 推送失败: {res.get('errmsg')}")
    except Exception as e:
        log(f"💥 推送异常: {str(e)}")

class YiHaoSign:
    def __init__(self, name, auth):
        self.name = name
        # 自动补全 Bearer 逻辑
        self.auth = auth if "Bearer" in auth else f"Bearer {auth}"
        self.headers = {
            "Host": "wmall.36588.com.cn",
            "Authorization": self.auth,
            "terminal": "client",
            "uuid": "b484e2f0-00be-11f1-9fd3-4bb525caa662",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://servicewechat.com/wxee2de3fd541cc3b1/121/page-frame.html"
        }

    def run(self):
        # 1. 执行签到 (保持你原本最稳的地址和签名)
        sign_url = "https://wmall.36588.com.cn/shopex-api/user/buyer/members/sign?nonce=fHIJpL&timestamp=1770095890&sign=a9caf743caa89aa50aea68f90659545f"
        status = "未知"
        try:
            res = requests.post(sign_url, headers=self.headers, json={}, timeout=10).json()
            msg = res.get("message") or res.get("msg") or ""
            
            if res.get("success") == True or res.get("code") == 200:
                status = "✅ 签到成功"
            elif "重复" in msg or "已签到" in msg:
                status = "💡 今日已签"
            elif "失效" in msg or "过期" in msg:
                status = "❌ Token失效"
            else:
                status = f"❓ {msg}"
        except:
            status = "❌ 签到异常"

        # 2. 获取实时积分 (接入你刚才抓包的接口)
        point_val = "获取失败"
        try:
            time.sleep(1) # 签到完歇一秒再查，防止被拦截
            info_url = "https://wmall.36588.com.cn/shopex-api/user/buyer/member"
            info_res = requests.get(info_url, headers=self.headers, timeout=10).json()
            if info_res.get("success") == True:
                # 对应你发的 JSON 结构: result -> point
                point_val = info_res.get("result", {}).get("point", 0)
        except:
            pass

        return f"👤 账号：{self.name}\n📢 状态：{status}\n💰 积分：{point_val}\n"

def main():
    yh_env = os.getenv("yh_gpt")
    if not yh_env:
        log("❌ 找不到变量 yh_gpt，请检查青龙环境变量设置！")
        return
    
    accounts = yh_env.split("&")
    results = []
    
    log(f"🚀 开始执行益好签到，共 {len(accounts)} 个账号...")
    for acc in accounts:
        if "#" not in acc:
            continue
        name, token = acc.split("#", 1)
        bot = YiHaoSign(name.strip(), token.strip())
        res_text = bot.run()
        log(res_text)
        results.append(res_text)
        time.sleep(2)

    if results:
        final_report = "--------------------\n".join(results)
        qywx_push("益好签到🙋‍♀️", final_report)

if __name__ == "__main__":
    main()

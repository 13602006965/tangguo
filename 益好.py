# -*- coding: utf-8 -*-
import requests
import os
import time
from datetime import datetime

"""
小程序：益好 签到V1.0
变量名：yh_gpt (格式：备注1#token1&备注2#token2)
定时：cron 5 6 * * * 一天一次自行修改
"""

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def qywx_push(title, content):
    """【硬核推送】绕过任何外部JS/PY文件，直接对接企业微信机器人"""
    key = os.getenv("QYWX_KEY")
    if not key:
        log("⚠️ 未检测到 QYWX_KEY 环境变量，跳过通知。")
        return
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    # 构造企业微信需要的格式
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
            log(f"❌ 推送失败，错误信息：{res.get('errmsg')}")
    except Exception as e:
        log(f"💥 推送过程发生异常: {str(e)}")

class YiHaoSign:
    def __init__(self, name, auth):
        self.name = name
        # 自动补全 Bearer 开头
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
        # 签到接口 URL (目前签名算法固定)
        url = "https://wmall.36588.com.cn/shopex-api/user/buyer/members/sign?nonce=fHIJpL&timestamp=1770095890&sign=a9caf743caa89aa50aea68f90659545f"
        try:
            res_obj = requests.post(url, headers=self.headers, json={}, timeout=10)
            res = res_obj.json()
            msg = res.get("message") or res.get("msg") or ""
            
            # --- 核心状态修复逻辑 ---
            if res.get("success") == True or res.get("code") == 200:
                status = "✅ 签到成功"
            elif "重复" in msg or "已签到" in msg:
                status = "💡 今日已签"
            elif "失效" in msg or "过期" in msg:
                status = "❌ Token已失效"
            else:
                status = f"❓ 异常: {msg}"

            return f"👤 账号：{self.name}\n📢 状态：{status}\n💰 积分：内测中\n"
        except Exception as e:
            return f"👤 账号：{self.name}\n💥 报错：接口连接失败\n"

def main():
    # 获取环境变量
    yh_env = os.getenv("yh_gpt")
    if not yh_env:
        log("❌ 找不到变量 yh_gpt，请先设置后再运行！")
        return
    
    # 解析账号（支持 & 分割）
    accounts = yh_env.split("&")
    results = []
    
    log(f"找到 {len(accounts)} 个账号，开始执行...")
    for acc in accounts:
        if "#" not in acc:
            continue
        name, token = acc.split("#", 1)
        bot = YiHaoSign(name.strip(), token.strip())
        res_text = bot.run()
        log(res_text)
        results.append(res_text)
        time.sleep(1.5) # 防止频率过快

    # 汇总结果并推送
    if results:
        final_report = "--------------------\n".join(results)
        qywx_push("益好签到🙋‍♀️", final_report)

if __name__ == "__main__":
    main()

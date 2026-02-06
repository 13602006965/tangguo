# -*- coding: utf-8 -*-
import requests, os, time

"""
小程序：绿动新球旧衣物回收 签到V1.0
      提现未些手动提吧
变量名：ldxq_gpt (账号1#token&账号2#token)
换算比例：1 环保豆 = 0.1 元
定时：cron 15 9 * * * 每天一次自行修改
"""

def qywx_push(title, content):
    key = os.getenv("QYWX_KEY")
    if not key: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    payload = {"msgtype": "text", "text": {"content": f"🎋 {title}\n{'-'*25}\n{content}"}}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

class LvDong:
    def __init__(self, name, token):
        self.name = name
        self.token = token
        self.headers = {
            "Host": "lvdong.fzjingzhou.com",
            "platform": "MP-WEIXIN",
            "content-type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16.3) AppleWebKit/605.1.15"
        }

    def run(self):
        # 1. 执行真签到接口
        sign_url = "https://lvdong.fzjingzhou.com/api/Person/sign"
        data = {"token": self.token}
        
        sign_res_msg = "未知"
        try:
            res = requests.post(sign_url, headers=self.headers, data=data, timeout=15, verify=False).json()
            if res.get('code') == 1000:
                sign_res_msg = "✅ 签到成功"
            elif "已签到" in res.get('msg', ''):
                sign_res_msg = "💡 今日已签"
            else:
                sign_res_msg = f"🔈 {res.get('msg')}"
        except:
            sign_res_msg = "❌ 签到异常"

        # 2. 查询资产并换算
        info_url = "https://lvdong.fzjingzhou.com/api/Person/index"
        try:
            time.sleep(1.5)
            info = requests.post(info_url, headers=self.headers, data=data, timeout=10, verify=False).json()
            if info.get('code') == 1000:
                d = info.get('data', {})
                score = int(d.get('score', 0))
                money = d.get('money', '0.00')
                days = d.get('days', 0)
                
                # 换算逻辑：1豆 = 0.1元
                score_to_money = score * 0.1
                
                return (f"👤 账号：{self.name}\n"
                        f"🎯 状态：{sign_res_msg}\n"
                        f"🌱 环保豆：{score} 个 (≈{score_to_money:.1f}元)\n"
                        f"🧧 余额：{money} 元\n"
                        f"📅 连签：第 {days} 天\n")
        except:
            pass
        return f"👤 账号：{self.name}\n📢 签到完成，资产查询失败\n"

def main():
    env = os.getenv("ldxq_gpt")
    if not env: return
    
    accounts = env.split("&")
    summary = []
    for acc in accounts:
        if "#" not in acc: continue
        name, token = acc.split("#", 1)
        result = LvDong(name.strip(), token.strip()).run()
        print(result)
        summary.append(result)
        time.sleep(2)

    if summary:
        qywx_push("绿动新球·🙋‍♀️", "\n".join(summary))

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    main()

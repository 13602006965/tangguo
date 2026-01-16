# -*- coding:utf-8 -*-
"""
小程序：杜蕾斯会员中心  V2.2
变量名： dls_gpt 格式token#备注
       （抓包access-token）多账号使用&分割或者换行
功能：签到＋积分收入支出明细
注意：抓包以后没必要不要登录小程序，进小程序ck失效
定时参考：cron 23 6 * * * 每天一次自行修改

"""
import requests
import os
import time
import json

def send_notification(title, content):
    try:
        from notify import send
        send(title, content)
    except: pass

class Durex:
    def __init__(self, token, note):
        self.token = token.strip()
        self.note = note.strip()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) XWEB/8555",
            "content-type": "application/json;charset=utf-8",
            "access-token": self.token,
            "sid": "10006",
            "platform": "MP-WEIXIN",
            "enterprise-hash": "10006",
            "referer": "https://servicewechat.com/wxe11089c85860ec02/34/page-frame.html"
        }

    def get_info(self):
        """获取积分信息"""
        url = "https://vip.ixiliu.cn/mp/points.log/info"
        try:
            # 增加到30秒超时，防止服务器响应慢
            res = requests.get(url, headers=self.headers, timeout=30).json()
            if res.get("status") == 200:
                return res.get("data", {})
        except:
            return None
        return None

    def sign_in(self):
        # 1. 签到前先拿一次积分，作为基准
        before_data = self.get_info()
        before_points = before_data.get("balance", 0) if before_data else 0

        # 2. 执行签到
        url = "https://vip.ixiliu.cn/mp/sign/applyV2"
        msg = ""
        try:
            res = requests.get(url, headers=self.headers, timeout=30).json()
            print(f"👤 {self.note} 原始返回: {json.dumps(res, ensure_ascii=False)}")
            
            s_code = res.get("status")
            s_text = res.get("message", "")
            
            if s_code == 200:
                msg = "✅ 签到成功"
            elif s_code == 400 or "已签到" in s_text:
                msg = "🆗 今日已完成"
            else:
                msg = f"⚠️ {s_text}"
        except Exception as e:
            msg = "⌛ 请求超时(等待复核)"

        # 3. 停顿一下，给服务器同步时间
        time.sleep(2)

        # 4. 签到后复核积分
        after_data = self.get_info()
        if after_data:
            after_points = after_data.get("balance", 0)
            if after_points > before_points:
                msg = f"✅ 签到成功(增加{after_points - before_points}分)"
            
            report = (f"--- 👤 {self.note} ---\n"
                      f"📝 任务状态：{msg}\n"
                      f"💰 当前余额：{after_points}\n"
                      f"📈 总入积分：{after_data.get('total', 0)}\n"
                      f"📉 总出积分：{after_data.get('used', 0)}")
        else:
            report = f"--- 👤 {self.note} ---\n📝 任务状态：{msg}\n💰 资产同步失败(建议检查CK)"

        print(f"\n{report}\n")
        return report

def main():
    raw = os.environ.get("dls_gpt")
    if not raw:
        print("❌ 未找到环境变量: dls_gpt")
        return

    accounts = raw.replace('&', '\n').strip().splitlines()
    reports = []
    for acc in accounts:
        if not acc.strip(): continue
        token, note = acc.split("#") if "#" in acc else (acc, "默认账号")
        reports.append(Durex(token, note).sign_in())
        time.sleep(3)

    if reports:
        send_notification("📦 杜蕾斯会员中心报告", "\n\n".join(reports))

if __name__ == "__main__":
    main()

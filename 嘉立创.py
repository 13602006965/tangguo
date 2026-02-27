# -*- coding: utf-8 -*-
"""
名称：小程序  嘉立创签到 V1.0
变量：jlc_gpt（备注#X-JLC-AccessToken#secretkey）     多账号&分割或换行分割
功能：签到＋积分统计＋美化推送
定时：cron 45 5 * * * 每天一次自行修改
"""
import os, time, json, requests, re

def ql_send(title, content):
    qywx_key = os.getenv("QYWX_KEY")
    if qywx_key:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qywx_key}"
        payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
        try:
            res = requests.post(url, json=payload, timeout=5).json()
            if res.get("errcode") == 0:
                print("🚀 [企微推送] 发送成功")
        except: pass

class JLCManager:
    def __init__(self, account_info, index):
        self.index = index
        parts = account_info.split('#')
        self.remark = parts[0] if len(parts) > 0 else f"账号{index}"
        self.access_token = parts[1] if len(parts) > 1 else ""
        self.secret_key = parts[2] if len(parts) > 2 else ""
        
        self.sess = requests.Session()
        self.sess.headers.update({
            "Host": "m.jlc.com",
            "X-JLC-ClientType": "MP-WEIXIN",
            "X-JLC-AccessToken": self.access_token,
            "secretkey": self.secret_key,
            "X-JLC-MP-AppId": "wx6c7b851c877dba42",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://servicewechat.com/wx6c7b851c877dba42/129/page-frame.html"
        })

    def log(self, msg):
        print(f"DEBUG [{self.remark}]: {msg}")

    def task(self):
        print(f"\n>>>>>> 开始执行账号 [{self.remark}] <<<<<<")
        status = "未运行"
        today_income = "0"
        total_balance = "0"
        expire_date = "未知"

        try:
            # Step 1: 获取签到配置 (运营对账)
            self.log("正在请求签到配置...")
            conf_res = self.sess.get("https://m.jlc.com/api/activity/sign/getSignInConfig?platformType=MP-WEIXIN&configCode=sign002").json()
            if conf_res.get("success"):
                self.log("配置获取成功，准备触发签到动作...")

            # Step 2: 执行签到
            sign_url = "https://m.jlc.com/api/activity/sign/doSignIn"
            sign_res = self.sess.post(sign_url, json={"platformType": "MP-WEIXIN", "configCode": "sign002"}).json()
            
            if sign_res.get("success"):
                today_income = str(sign_res.get("data", {}).get("rewardValue", "2"))
                status = "✅ 签到成功"
                self.log(f"签到动作成功，获得奖励: {today_income}")
            else:
                msg = sign_res.get('message') or '今日已签'
                status = f"🆗 {msg}"
                self.log(f"签到接口返回: {msg}")

            # Step 3: 查询今日流水 (确认收益)
            time.sleep(1.5)
            self.log("正在查询签到历史记录...")
            rec_res = self.sess.get("https://m.jlc.com/api/activity/sign/getSignInRecord?platformType=MP-WEIXIN&configCode=sign002").json()
            records = rec_res.get("data", [])
            if records and time.strftime("%Y-%m-%d") in records[0].get("signTime", ""):
                today_income = str(records[0].get("rewardValue", today_income))
                self.log(f"确认今日流水收益: +{today_income}")

            # Step 4: 查询账户总积分
            self.log("正在查询账户总资产...")
            asset_res = self.sess.get("https://m.jlc.com/api/activity/front/getCustomerIntegral").json()
            if asset_res.get("success"):
                data = asset_res.get("data", {})
                total_balance = str(data.get("integralVoucher", "0"))
                expire_date = data.get("expireTime", "未知")
                self.log(f"资产查询成功: 余额 {total_balance}, 过期时间 {expire_date}")

        except Exception as e:
            status = "❌ 运行崩溃"
            self.log(f"运行时发生错误: {str(e)}")

        print(f">>>>>> 账号 [{self.remark}] 执行结束 <<<<<<\n")
        return [
            f"--- 👤 {self.remark} ---",
            f"📝 签到状态：{status}",
            f"🎁 今日收益：+{today_income} 立创币",
            f"💰 账户余额：{total_balance} 立创币",
            f"⌛ 过期时间：{expire_date}"
        ]

def main():
    print("## 📏 嘉立创资产运营脚本启动 ##")
    raw = os.getenv("jlc_gpt", "").strip()
    if not raw:
        print("❌ 环境变量 jlc_gpt 缺失，请检查配置。")
        return
    
    accounts = raw.split('&')
    final_reports = []
    for i, info in enumerate(accounts):
        if info.strip():
            final_reports.append("\n".join(JLCManager(info.strip(), i + 1).task()))
            time.sleep(2)
    
    if final_reports:
        ql_send("📏 嘉立创🙋‍♀️签到日报", "\n\n".join(final_reports))

if __name__ == "__main__":
    main()

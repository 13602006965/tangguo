# -*- coding: utf-8 -*-
import os, requests, time, random, re, urllib3
from datetime import datetime

"""
名称：小程序 桃色（趣网商城） V2.0
变量：ts_gpt （备注#ssid）多账号&分割
功能：签到＋积分统计＋美化推送
定时：cron 25 5 * * * 每天一次自行修改
"""

# 屏蔽SSL证书校验警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class QuWang:
    def __init__(self, name, ssid):
        self.name = name
        self.ssid = ssid
        # 使用你抓包里的 iPhone UA，更真实
        self.ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61"

    def login(self):
        """执行微信登录模拟"""
        url = "https://wxapp.lllac.com/xqw/login.php"
        headers = {'User-Agent': self.ua, 'Cookie': f"SSID={self.ssid}"}
        payload = {'act': "wx_login", 'u_name': "微信用户", 'session_id': self.ssid}
        try:
            res = requests.post(url, data=payload, headers=headers, timeout=10, verify=False).json()
            return res.get('msg', '成功')
        except: return "登录失败"

    def checkin(self):
        """执行每日签到"""
        url = "https://wxapp.lllac.com/xqw/user_mall.php"
        params = {'act': 'signToday', 'ssid': self.ssid}
        try:
            res = requests.post(url, params=params, headers={'User-Agent': self.ua}, timeout=10, verify=False).json()
            return res.get('msg', '已签到')
        except: return "签到异常"

    def get_balance(self):
        """从HTML页面中提取消费积分"""
        url = "https://wxapp.lllac.com/xqw/user_account_log.php"
        params = {'ssid': self.ssid}
        try:
            res = requests.get(url, params=params, headers={'User-Agent': self.ua}, timeout=10, verify=False)
            # 正则匹配：提取“消费积分：</strong>数字”
            p_match = re.search(r'消费积分：</strong>(\d+)', res.text)
            return p_match.group(1) if p_match else "未知"
        except: return "查询失败"

    def run(self):
        log(f"🚀 账号【{self.name}】开始收割...")
        
        # 1. 登录验证
        l_status = self.login()
        log(f"🔑 登录状态: {l_status}")
        
        # 2. 随机延迟后签到
        time.sleep(random.randint(2, 5))
        c_status = self.checkin()
        log(f"📅 签到反馈: {c_status}")
        
        # 3. 查账
        time.sleep(2)
        balance = self.get_balance()
        log(f"💰 账户资产: {balance} 趣豆")
        
        # 返回格式化的推送内容
        return f"👤 {self.name}\n🔑 状态：{l_status}\n📅 签到：{c_status}\n💎 余额：{balance} 趣豆\n"

def main():
    # 变量获取：ts_gpt
    env = os.getenv("ts_gpt")
    if not env:
        log("❌ 错误：请先设置环境变量 ts_gpt")
        return
    
    # 账号分割
    accounts = env.split("&")
    summary = []
    
    log(f"ℹ️ 检测到 {len(accounts)} 个收割账号，开始任务...")
    
    for acc in accounts:
        if "#" in acc:
            name, ssid = acc.split("#")
            bot = QuWang(name, ssid)
            summary.append(bot.run())
            # 账号间随机冷却，防止封IP
            if len(accounts) > 1:
                time.sleep(random.randint(5, 10))
        else:
            log(f"⚠️ 变量格式不规范: {acc} (应为 备注#ssid)")

    # 4. 汇总推送
    if summary:
        report = "【趣网商城收割日报】\n" + "\n".join(summary)
        print("\n" + "="*30 + "\n" + report + "="*30)
        try:
            from notify import send
            send("桃色🙋‍♀️趣网商城", report)
        except:
            log("📢 未配置通知推送，仅输出日志")

if __name__ == "__main__":
    main()

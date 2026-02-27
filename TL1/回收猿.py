# -*- coding: utf-8 -*-
"""
小程序  回收猿（修改版V3.2）
变量: hsy_gpt ，username=xxx;NAME=xxx多账号@分割
自动签到 + 抽奖 + 查询 ＋今日/七日累计奖励统计
推送显示收入明细
支持备注名、多账号、彩色日志、美化推送
cron 16 6 * * * 定时自行修改
"""
import os, time, random, hashlib, requests
from urllib.parse import urlencode
from datetime import datetime

# ========= 推送模块 =========
try:
    from notify import send as ql_send
except Exception:
    def ql_send(title, content):
        print(f"\n🔔 {title}\n{content}\n")

# ========= 彩色输出（日志专用）=========
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    def line(char="━", length=55): print(Fore.CYAN + char * length + Style.RESET_ALL)
    def color(text, c): return getattr(Fore, c.upper()) + str(text) + Style.RESET_ALL
except ImportError:
    def line(char="━", length=55): print(char * length)
    def color(text, c): return str(text)

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_3 like Mac OS X) AppleWebKit/605.1.15"

class Hsy:
    def __init__(self, username, name=None):
        self.key = "1079fb245839e765"
        self.scret = "UppwYkfBlk"
        self.username = username
        self.name = name
        self.headers = {'User-Agent': UA, 'content-type': "application/json"}

    def md5_sign(self, params: dict) -> str:
        s = urlencode(sorted(params.items())) + self.scret
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def get_financial_data(self):
        """核心财务接口：含未提现账号逻辑修正"""
        url = "https://www.52bjy.com/api/app/hsy.php"
        params = {'action': "user", 'appkey': self.key, 'merchant_id': "2", 'method': "center", 'username': self.username}
        params['sign'] = self.md5_sign(params)
        try:
            r = requests.get(url, params=params, headers=self.headers, timeout=10).json()
            if r.get('code') == 200:
                d = r.get('data', {})
                balance = float(d.get("award", 0))
                total_in = float(d.get("award_total", 0))
                # 🛠️ 针对未提现账号的修正：若总收入数据缺失或小于余额，则总收入=余额
                if total_in < balance: total_in = balance
                total_out = total_in - balance
                return {"balance": f"{balance:.2f}", "total_in": f"{total_in:.2f}", "total_out": f"{total_out:.2f}"}
        except: pass
        return {"balance": "0.00", "total_in": "0.00", "total_out": "0.00"}

    def get_records_and_today(self):
        """获取明细并计算今日收入"""
        url = "https://www.52bjy.com/api/app/envcash.php"
        params = {'action': "awardlist", 'appkey': self.key, 'merchant_id': "2", 'page': "1", 'type': "award", 'username': self.username}
        params['sign'] = self.md5_sign(params)
        t_in = 0.0
        recs = []
        try:
            r = requests.get(url, params=params, headers=self.headers, timeout=10).json()
            recs = r.get('data', {}).get('record', [])
            today_str = datetime.now().strftime("%Y-%m-%d")
            for rec in recs:
                try:
                    amt = float(str(rec.get("amount", "0")).replace("+", ""))
                    if amt > 0 and rec.get("addtime", "").startswith(today_str):
                        t_in += amt
                except: continue
        except: pass
        return recs, t_in

    def signin(self):
        url = "https://www.52bjy.com/api/app/hsy.php"
        params = {'action': "user", 'app': "hsywx", 'appkey': self.key, 'merchant_id': "2", 'method': "qiandao", 'username': self.username, 'version': "2"}
        params['sign'] = self.md5_sign(params)
        try:
            r = requests.get(url, params=params, headers=self.headers, timeout=10).json()
            return r.get('code') == 200, r.get('message', '')
        except: return False, "网络异常"

    def task(self):
        name_display = self.name or self.username
        line()
        print(f"💎 账号：{color(name_display, 'GREEN')}（{self.username}）")
        
        ok_s, msg_s = self.signin()
        print("📋 签到状态：", color("成功" if ok_s else "已完成/失败", "GREEN" if ok_s else "YELLOW"), msg_s)
        
        # ⏳ 只有签到成功时才等待，避免浪费时间
        if ok_s:
            print(f"⏳ 正在等待 10 秒让奖励入账...")
            time.sleep(10)

        money = self.get_financial_data()
        recs, today_in = self.get_records_and_today()
        
        print(color("\n📊 最近奖励记录（前5条）", "CYAN"))
        for i, item in enumerate(recs[:5], 1):
            print(f"  {i}. {item['addtime']}｜{item['amount']}｜{item['reason']}")
        
        print(color(f"\n💰 今日收入：+{today_in:.2f} 元", "GREEN"))
        line()

        return [
            f"--- 👤 {name_display} ---",
            f"📝 任务状态：{'✅ 签到成功' if ok_s else '🆗 ' + msg_s}",
            f"💰 现金余额：{money['balance']} 元",
            f"📈 今日收入：{today_in:.2f} 元",
            f"📊 总入现金：{money['total_in']} 元",
            f"📉 总出现金：{money['total_out']} 元"
        ]

def main():
    raw = os.getenv("hsy_gpt", "").strip()
    if not raw: return
    accounts = []
    for part in raw.split("@"):
        conf = {}
        for kv in part.split(";"):
            if "=" in kv: k, v = kv.split("=", 1); conf[k.strip().upper()] = v.strip()
        if conf.get("USERNAME"): accounts.append(conf)
    
    print(f"🚀 准备执行 {len(accounts)} 个账号\n")
    final_reports = []
    for a in accounts:
        final_reports.append("\n".join(Hsy(a.get("USERNAME"), a.get("NAME")).task()))
    
    if final_reports:
        ql_send("📬 回收猿 收入日报", "\n\n".join(final_reports))

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import os, requests, time, random, urllib3
from datetime import datetime

"""
名称：小程序 桃色（趣网商城） V2.0
变量：ts_gpt （备注#ssid#pass）多账号&分割
更新：增加pass值模拟每天点击小程序
功能：签到＋积分统计＋美化推送
定时：cron 25 5 * * * 每天一次自行修改
"""

try:
    from notify import send
except ImportError:
    def send(title, content):
        print(f"\n[通知推送] {title}\n{content}")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

ts_gpt = os.getenv("ts_gpt")
UA = "Mozilla/5.0 (Linux; Android 15; PKG110) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.180 Mobile Safari/537.36 XWEB/1380215 MMWEBSDK/20250904 MicroMessenger/8.0.64.2940(0x28004034) MiniProgramEnv/android"

def run_task():
    if not ts_gpt:
        log("❌ 未配置变量 ts_gpt")
        return

    accounts = [a for a in ts_gpt.split('&') if a]
    log(f"ℹ️ 检测到 {len(accounts)} 个账号，开始全任务收割...")
    
    summary = []

    for idx, acc in enumerate(accounts, 1):
        if '#' not in acc: continue
        items = acc.split('#')
        mark, ssid = items[0], items[1]
        device_pass = items[2] if len(items) > 2 else ""
        
        log(f"\n🚀 正在收割账号【{mark}】...")
        headers = {
            'User-Agent': UA,
            'Cookie': f'SSID={ssid}',
            'Referer': 'https://servicewechat.com/wxb96c32e3d2d4b224/102/page-frame.html',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            # --- 1. 首页唤醒 ---
            requests.post("https://wxapp.lllac.com/xqw/index.php", data={'act': 'index', 'pass': device_pass, 'session_id': ssid}, headers=headers, timeout=10)
            
            # --- 2. 登录同步 ---
            login_data = {'act': 'wx_login', 'session_id': ssid, 'u_name': '微信用户', 'pass': device_pass}
            login_res = requests.post("https://wxapp.lllac.com/xqw/login.php", data=login_data, headers=headers, timeout=10).json()
            log(f"🔑 登录反馈: {login_res.get('msg', '未知')}")

            # --- 3. 核心任务：每日签到 ---
            sign_res = requests.post("https://wxapp.lllac.com/xqw/user_mall.php", data={'act': 'signToday', 'ssid': ssid}, headers=headers, timeout=10).json()
            sign_msg = sign_res.get('msg', '已完成')
            log(f"📅 签到结果: {sign_msg}")

            # --- 4. 额外收割：三个积分任务 (重点添加) ---
            log("🎁 正在执行额外积分任务...")
            tasks = [
                ("新品浏览", "https://wxapp.lllac.com/xqw/goods_v2.php?act=task&id={}&type=28"),
                ("热销浏览", "https://wxapp.lllac.com/xqw/goods_v2.php?act=task&id={}&type=29"),
                ("评测阅读", "https://wxapp.lllac.com/xqw/ch_article_info.php?id={}&act=task")
            ]
            for t_name, t_url in tasks:
                t_id = random.randint(3000, 15000)
                try:
                    t_res = requests.post(t_url.format(t_id), headers=headers, timeout=10).json()
                    log(f"   ∟ {t_name}: {t_res.get('msg', '完成')}")
                except: pass
                time.sleep(random.uniform(1.5, 3))

            # --- 5. 资产汇总 ---
            info_res = requests.post("https://wxapp.lllac.com/xqw/user_home_v2.php?act=home", headers=headers, timeout=10).json()
            points = info_res.get('user_point', '0')
            dou = info_res.get('user_dou', '0')
            log(f"💰 统计：积分 {points} | 趣豆 {dou}")
            
            summary.append(f"【{mark}】{sign_msg}\n   资产: {points}积分 / {dou}趣豆")

        except Exception as e:
            log(f"❌ 账号处理出错")
            summary.append(f"【{mark}】执行失败")
        
        time.sleep(8)

    if summary:
        send("桃色🙋‍♀️趣网商城日报", "\n".join(summary))

if __name__ == "__main__":
    run_task()

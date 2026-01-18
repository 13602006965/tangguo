# -*- coding:utf-8 -*-
"""
【脚本名称】：长虹（#小程序://长虹智慧家居/3mAUsakenataqSB） 每日签到增强版V2.4
【变量名称】：ch_gpt (格式: Token#备注，多账号用 & 或 换行 分割)
【参考定时】cron 26 6 * * * 定时自行修改
"""
import requests
import os
import time
import json

# ========= 推送模块 =========
try:
    from notify import send as ql_send
except Exception:
    def ql_send(title, content):
        print(f"\n🔔 推送通知：\n{title}\n{content}\n")

class ChangHongPro:
    def __init__(self, token, note):
        self.token = token.strip()
        self.note = note.strip()
        self.headers = {
            'token': self.token,
            'smarthome': self.token,
            'content-type': "application/json;charset=UTF-8",
            'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61",
            'Referer': "https://servicewechat.com/wx36c3413e8fe39263/278/page-frame.html",
            'xweb_xhr': '1'
        }

    def get_score(self):
        """参考账本：获取当前积分"""
        url = "https://hongke.changhong.com/gw/applet/homePage/getUserPoint"
        try:
            res = requests.get(url, headers=self.headers, timeout=10).json()
            if str(res.get("code")) == "200":
                return int(res.get("data", 0))
        except Exception as e:
            print(f"❌ 获取积分异常: {e}")
            return 0
        return 0

    def run(self):
        print(f"🚀 开始处理账号：{self.note}")
        
        # 1. 任务前查分
        old_score = self.get_score()
        
        # 2. 执行【新版200成功】的组合动作
        results = []
        
        # 动作A: 模拟开屏 (发现页)
        try:
            url_a = "https://hongke.changhong.com/gw/applet/discover/openWindowInfo"
            res_a = requests.post(url_a, headers=self.headers, json={}, timeout=10).json()
            results.append(res_a.get('message', '未知'))
        except:
            results.append("开屏异常")

        time.sleep(2)

        # 动作B: 模拟进入游戏中心日志
        try:
            url_b = "https://hongke.changhong.com/gw/applet/appletUser/addMenuLog?menuName=%E5%BF%AB%E6%8D%B7%E8%8F%9C%E5%8D%95&menuPath=%E9%A6%96%E9%A1%B5&subName=/pages/gamesMan/games"
            res_b = requests.post(url_b, headers=self.headers, json={}, timeout=10).json()
            results.append(res_b.get('message', '未知'))
        except:
            results.append("日志异常")

        # 3. 延迟查询最终积分
        time.sleep(3) 
        new_score = self.get_score()
        reward = new_score - old_score
        
        # 4. 汇总报告
        status = "✅ 执行成功" if any("成功" in r for r in results) else "⚠️ 检查Token"
        reward_text = f"+{reward}" if reward > 0 else "0 (或今日已领)"
        
        if old_score == 0 and new_score == 0:
            status = "❌ Token可能已失效"

        report = [
            f"--- 👤 {self.note} ---",
            f"📈 任务状态：{status}",
            f"💰 账户余额：{new_score} 积分",
            f"🎁 本次变动：{reward_text}",
            f"🗨️ 动作反馈：{'/'.join(results)}"
        ]
        
        final_report = "\n".join(report)
        print(final_report)
        return final_report

def main():
    raw = os.environ.get("ch_gpt")
    if not raw:
        print("❌ 错误：未在环境变量中找到 ch_gpt")
        return

    # 兼容 & 或 换行 分割
    accounts = raw.replace('&', '\n').strip().splitlines()
    reports = []
    
    for acc in accounts:
        acc = acc.strip()
        if not acc: continue
        if "#" in acc:
            parts = acc.split("#")
            token = parts[0]
            note = parts[1] if len(parts) > 1 else "默认账号"
            reports.append(ChangHongPro(token, note).run())
            time.sleep(5) # 账号间隔
            
    if reports:
        ql_send("📬 长虹智慧家居任务报告", "\n\n".join(reports))

if __name__ == "__main__":
    main()

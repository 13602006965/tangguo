# -*- coding:utf-8 -*-
"""
【脚本名称】：长虹（#小程序://长虹智慧家居/3mAUsakenataqSB） 每日签到增强版V2.4
【变量名称】：ch_gpt (格式: Token#备注，多账号用 & 或 换行 分割)
【参考定时】cron 26 6 * * * 定时自行修改
"""
import requests, os, time, json

# ========= 推送模块 =========
try:
    from notify import send as ql_send
except Exception:
    def ql_send(title, content):
        print(f"\n🔔 推送通知：\n{title}\n{content}\n")

class HongKe:
    def __init__(self, token, note):
        self.token = token.strip()
        self.note = note.strip()
        # 严格对齐你提供的 Header 结构，确保权限通畅
        self.headers = {
            'Token': self.token,
            'smarthome': self.token,
            'Content-Type': "application/json",
            'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15",
            'Referer': "https://servicewechat.com/wx36c3413e8fe39263/278/page-frame.html"
        }

    def get_score(self):
        """对接精准账本接口 getUserPoint"""
        url = "https://hongke.changhong.com/gw/applet/homePage/getUserPoint"
        try:
            res = requests.get(url, headers=self.headers, timeout=10).json()
            if str(res.get("code")) == "200":
                # 返回真实账户积分
                return int(res.get("data", 0))
        except:
            return 0
        return 0

    def run(self):
        print(f"🚀 开始处理账号：{self.note}")
        
        # 1. 签到前查询，用于比对奖励
        old_score = self.get_score()
        
        # 2. 执行签到动作
        status = "未知"
        raw_msg = "无返回"
        try:
            sign_url = "https://hongke.changhong.com/gw/applet/aggr/signin?aggrId=608"
            res = requests.post(sign_url, headers=self.headers, timeout=10)
            res_json = res.json()
            raw_msg = res_json.get('message', '无响应内容')
            
            if res.status_code == 200:
                status = "✅ 签到成功"
            elif res.status_code == 400 or "已签到" in raw_msg:
                status = "🆗 今日已签"
            else:
                status = f"⚠️ 响应:{res.status_code}"
        except Exception as e:
            status = f"❌ 异常: {str(e)}"

        # 3. 延迟 2 秒等待服务器入账，查询最终积分
        time.sleep(2) 
        new_score = self.get_score()
        reward = new_score - old_score
        
        # 4. 汇总审计报告
        reward_text = f"+{reward}" if reward > 0 else "0 (阶梯奖励期)"
        
        # 如果余额是 0 且查不到分数，判定为 Token 失效
        if old_score == 0 and new_score == 0:
            status = "❌ Token失效(请重抓)"

        report = [
            f"--- 👤 {self.note} ---",
            f"📈 任务状态：{status}",
            f"💬 原厂回复：{raw_msg}",
            f"💰 账户余额：{new_score} 积分",
            f"🎁 本次收益：{reward_text}"
        ]
        
        final_report = "\n".join(report)
        print(final_report)
        return final_report

def main():
    # 变量名：ch_gpt
    # 格式：Token#备注 (多账号换行或使用 & 分隔)
    raw = os.environ.get("ch_gpt")
    if not raw:
        print("❌ 错误：未在环境变量中找到 ch_gpt")
        return

    # 兼容多种分隔符，切分账号列表
    accounts = raw.replace('&', '\n').strip().splitlines()
    reports = []
    
    for acc in accounts:
        acc = acc.strip()
        if not acc: continue
        if "#" in acc:
            token, note = acc.split("#", 1)
            reports.append(HongKe(token, note).run())
            time.sleep(3) # 账号间微小延迟
            
    if reports:
        ql_send("📬 长虹智慧家居", "\n\n".join(reports))

if __name__ == "__main__":
    main()

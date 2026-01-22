# -*- coding: utf-8 -*-
#======================================================
#【抓包说明】小程序 浓五的酒馆 V1.3
#【变量名称】nwjg_gpt (格式：token#备注)多账号&分割
#          抓authorization参数不要带Bearer
#【运行简介】签到（抽奖逻辑已经删除只保留签到）
#【定时参考】cron 6 12 * * * 定时参考自行修改
#======================================================
import os, requests, time
push_func = None
try:
    from notify import send
    push_func = send
except:
    pass
class NongWuPerfect:
    def __init__(self, token, remark):
        self.remark = remark
        self.token = token.strip().replace('Bearer ', '')
        self.headers = {
            'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61",
            'content-type': "application/json",
            'authorization': f"Bearer {self.token}",
            'referer': "https://servicewechat.com/wxed3cf95a14b58a26/243/page-frame.html"
        }
        self.report = []
    def log(self, text):
        print(text)
        self.report.append(text)
    def get_user_info(self):
        """获取真实积分和等级"""
        url = "https://stdcrm.dtmiller.com/scrm-promotion-service/mini/wly/user/info"
        try:
            res = requests.get(url, headers=self.headers, timeout=10).json()
            if res.get("code") == 0:
                d = res.get('data', {})
                points = d.get('member', {}).get('points', '0')
                level = d.get('grade', {}).get('level_name', '普通会员')
                return points, level
            return "获取失败", "N/A"
        except:
            return "异常", "N/A"
    def do_task(self):
        """执行签到并获取连续天数及状态"""
        p_id = "PI695342be11a824000ad141da"
        i_url = f"https://stdcrm.dtmiller.com/scrm-promotion-service/promotion/sign/userinfo?promotionId={p_id}"
        s_url = f"https://stdcrm.dtmiller.com/scrm-promotion-service/promotion/sign/today?promotionId={p_id}"
        
        sign_days = "0"
        status_msg = "未知 ❓"
        try:
            # 1. 检查状态
            info = requests.get(i_url, headers=self.headers, timeout=10).json()
            data = info.get('data', {})
            sign_days = data.get('signDays', '0')
            
            if data.get('today') is True:
                status_msg = "今日已完成 ✅"
            else:
                # 2. 执行签到
                res = requests.get(s_url, headers=self.headers, timeout=10).json()
                if res.get('code') == 0:
                    status_msg = "成功 ✨"
                    sign_days = str(int(sign_days) + 1)
                else:
                    status_msg = f"失败({res.get('msg')})"
        except:
            status_msg = "接口异常 ❌"
        return status_msg, sign_days
    def run(self):
        # 这里的顺序严格按照你的要求排列
        status, days = self.do_task()
        pts, lvl = self.get_user_info()
        self.log(f"👤 账号：{self.remark}")
        self.log(f"👑 等级：{lvl}")
        self.log(f"📅 签到：{status}") # 签到状态上移
        self.log(f"💰 积分：{pts}")    # 积分下移
        self.log(f"📈 连签：{days} 天")
        self.log("-" * 25)
        return "\n".join(self.report)
def main():
    env = os.environ.get("nwjg_gpt")
    if not env: return
    reports = []
    for acc in env.replace('&', '\n').strip().splitlines():
        if "#" in acc:
            tk, rem = acc.split("#")[:2]
            res = NongWuPerfect(tk, rem).run()
            reports.append(res)
            time.sleep(2)
    if push_func and reports:
        push_func("🍷 浓五酒馆🙋‍♀️积分", "\n\n".join(reports))
if __name__ == "__main__":
    main()

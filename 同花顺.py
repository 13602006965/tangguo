# -*- coding: utf-8 -*-
import requests
import os
import time
import json
import re
from datetime import datetime

"""
名称：同花顺APP签到 V1.5
变量：ths_gpt （备注#cookie）多账号换行分割
功能：签到＋积分统计＋美化推送
定时：cron 25 8 * * * 每天一次自行修改
"""

# ================= 推送配置 =================
# 在青龙环境变量新建 QYWX_KEY，填入机器人webhook地址里key=后面的那串字符
QYWX_KEY = os.getenv("QYWX_KEY") or ""

def send_msg(title, content):
    """直接使用企业微信机器人推送，不依赖外部sendNotify"""
    print(f"【通知】{title}\n{content}")
    
    if not QYWX_KEY:
        print("⚠️ 提示：未在环境变量配置 QYWX_KEY，跳过通知发送。")
        return

    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"🔔 {title}\n{'-'*20}\n{content}\n\n统计时间：{datetime.now().strftime('%M:%S')}"
        }
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if res.get("errcode") == 0:
            print("🚀 企业微信机器人推送成功！")
        else:
            print(f"❌ 推送失败: {res.get('errmsg')}")
    except Exception as e:
        print(f"💥 推送异常: {str(e)}")

# ================= 核心逻辑 =================

def get_ths_details(ck):
    headers = {"Cookie": ck, "token": "ths", "User-Agent": "Mozilla/5.0"}
    today_str = datetime.now().strftime('%Y-%m-%d')
    total_score, today_score, total_days = 0, 0, 0
    try:
        # 1. 积分明细
        score_url = "https://mams.10jqka.com.cn/assembly/user_component/entity/v1/score_detail/get?activity_id=343&page_no=1&page_size=50"
        s_res = requests.get(score_url, headers=headers, timeout=10).json()
        if s_res.get("status_code") == 0:
            records = s_res.get("data", {}).get("score_record_list", [])
            for item in records:
                score_val = item.get("score", 0)
                total_score += score_val
                if today_str in item.get("create_time", ""):
                    today_score += score_val
        # 2. 签到天数
        record_url = "https://mams.10jqka.com.cn/assembly/user_component/activity/user/game_record/list?activity_id=343&game_instance_id=182"
        r_res = requests.get(record_url, headers=headers, timeout=10).json()
        if r_res.get("status_code") == 0:
            total_days = len(r_res.get("data", []))
        return total_score, today_score, total_days
    except:
        return "未知", 0, "-"

def ths_sign(ck):
    url = "https://mams.10jqka.com.cn/assembly/user_component/activity/behavior/v1/trigger"
    headers = {"Cookie": ck, "token": "ths", "Content-Type": "application/json;charset=utf-8", "User-Agent": "Mozilla/5.0"}
    payload = {"activity_id": "343", "behavior_id": "28", "game_instance_id": "182", "data": {}}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10).json()
        msg = res.get("status_msg", "")
        if res.get("status_code") == 0: return "✅ 签到成功"
        return "✅ 今日已签到" if "已经签到" in msg else f"❌ {msg}"
    except:
        return "💥 接口异常"

def main():
    ck_env = os.getenv("ths_gpt")
    if not ck_env:
        print("❌ 未找到环境变量 ths_gpt")
        return
    
    summary = []
    accounts = ck_env.splitlines()
    for acc in accounts:
        if "#" not in acc: continue
        name, ck = acc.split("#", 1)
        print(f"👤 正在处理: {name}")
        
        sign_status = ths_sign(ck)
        total, today, days = get_ths_details(ck)
        
        summary.append(
            f"👤 {name}\n"
            f"📝 状态：{sign_status}\n"
            f"📅 进度：累计签到 {days} 天\n"
            f"💰 今日：+{today} 积分\n"
            f"📊 总计：{total} 积分"
        )
        time.sleep(2)

    send_msg("同花顺签到🙋‍♀️", "\n\n".join(summary))

if __name__ == "__main__":
    main()

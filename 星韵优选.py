# -*- coding: utf-8 -*-
import os, json, requests, time

# ==========================================
# 【星韵优选 V1.2 - 强力自适应挂机版】
# 修正了冷却逻辑判断，静默运行挂机
# 变量xyyx_gpt（备注#3rdSession1）多账号&分割
# 定时参考 cron 0 8 * * * 每天一次循环十个签到
# 逻辑：签到满额 -> 自动提现 -> 汇总推送
# ==========================================

push_func = None
try:
    import sys
    sys.path.append('/ql/scripts')
    from notify import send
    push_func = send
except: pass

XYYX_GPT = os.getenv("xyyx_gpt")
API_URL = "https://gzpengru.weimbo.com/api/index.php?ackey=GZYTAPPLET"

def get_headers(session):
    return {
        'Host': 'gzpengru.weimbo.com',
        '3rdSession': session,
        'content-type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d39) NetType/WIFI Language/zh_CN',
        'Referer': 'https://servicewechat.com/wxc86c9aecdb67f876/10/page-frame.html'
    }

def main():
    if not XYYX_GPT: return
    accounts = [{"name": x.split("#")[0], "session": x.split("#")[1]} for x in XYYX_GPT.split("&&") if "#" in x]
    summary_list = []

    for acc in accounts:
        headers = get_headers(acc['session'])
        print(f"\n🚀 账号: [{acc['name']}] 启动...")
        total_jf = 0
        
        # 1. 签到逻辑
        while True:
            try:
                res = requests.post(API_URL, json={"action":"userQiandao"}, headers=headers).json()
                msg = str(res.get('Message', '') or res.get('Data', ''))
                
                # 无论成功失败，都查一下进度
                info = requests.post(API_URL, json={"action":"getIntegralInfo","type":"sign"}, headers=headers).json()
                if info.get('Status'):
                    data = info['Data']
                    # 精准提取积分，防止显示为0
                    total_jf = int(float(data.get('user_jf') or data.get('u_money',{}).get('jifen') or 0))
                    progress = data.get('qiands', '未知')
                    print(f"📊 进度: {progress} | 当前积分: {total_jf}")

                    if "10 次" in progress or any(kw in msg for kw in ["用完", "上限", "完成"]):
                        break
                    
                    wait_sec = data.get('sign_time', 560)
                    if wait_sec > 0:
                        print(f"💤 冷却 {wait_sec + 5} 秒...")
                        time.sleep(wait_sec + 5)
                else: break
            except: break

        # 2. 自动提现 (不记账，直接冲)
        withdraw_status = "未达标"
        if total_jf >= 20000:
            print(f"💰 积分 {total_jf} 已满 2 万，尝试提现...")
            try:
                tx = requests.post(API_URL, json={"action":"withdrawalInfo","tx_ty":"jifen"}, headers=headers).json()
                if tx.get('Status'):
                    tx_data = tx.get('Data', {}).get('transfer_result', {})
                    if tx_data.get('state') == 'SUCCESS':
                        amount = tx_data.get('transfer_amount', 0) / 100
                        withdraw_status = f"✅ 提现成功({amount}元)"
                    else:
                        withdraw_status = f"⚠️ {tx_data.get('state', '异常')}"
                else:
                    withdraw_status = f"❌ {tx.get('Message', '报错')}"
            except:
                withdraw_status = "❌ 请求异常"
        
        summary_list.append(f"👤 {acc['name']}\n💎 剩余积分: {total_jf}\n🏧 提现状态: {withdraw_status}")

    if summary_list and push_func:
        push_func("🌟 星韵优选·♻️签到提现 V1.2", "\n\n".join(summary_list))

if __name__ == "__main__":
    main()


 


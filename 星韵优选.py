# -*- coding: utf-8 -*-
import os, json, requests, time

# ==========================================
# 【星韵优选 V2.2 - 自动提现版】
# 1. 恢复任务动作：保留循环签到，带冷却等待检测任务
# 2. 精简探测位：提现新手0.2，后续1元。再往后会不会增加     #    门槛未知，目前提现就写了两个门槛。
# 3. 真实性校验：提现必查余额，防止“假成功”诈骗
# 4. 变量xyyx_gpt（备注#3rdSession1）多账号&分割
# 5. 定时参考 cron 0 8 * * * 每天一次循环十个签到
# 6. 逻辑：签到满额 -> 自动提现 -> 汇总推送
#    如果提现失败可能小程序修改提现金额规则
# ==========================================

push_func = None
try:
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
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61',
        'Referer': 'https://servicewechat.com/wxc86c9aecdb67f876/10/page-frame.html'
    }

def get_balance(headers):
    """提取当前最新积分"""
    try:
        info = requests.post(API_URL, json={"action":"getIntegralInfo","type":"sign"}, headers=headers, timeout=10).json()
        if info.get('Status'):
            return info['Data']
    except: pass
    return None

def main():
    if not XYYX_GPT: return
    raw_accs = XYYX_GPT.replace('&', '\n').strip().splitlines()
    summary_list = []

    for acc_str in raw_accs:
        if "#" not in acc_str: continue
        parts = acc_str.split("#")
        name, session = parts[0].strip(), parts[1].strip() 

        headers = get_headers(session)
        print(f"\n🚀 账号: [{name}] 启动...")
        total_jf = 0
        last_jf = -1
        
        # 1. 【任务动作恢复】循环签到
        print(f"🔄 开始执行签到任务...")
        while True:
            try:
                # 签到
                requests.post(API_URL, json={"action":"userQiandao"}, headers=headers, timeout=10)
                
                # 获取进度和积分
                data = get_balance(headers)
                if data:
                    total_jf = int(float(data.get('user_jf') or data.get('u_money',{}).get('jifen') or 0))
                    progress = data.get('qiands', '未知')
                    print(f"📊 进度: {progress} | 当前积分: {total_jf}")

                    # 收益封顶判断
                    if total_jf <= last_jf and last_jf != -1:
                        print("🔔 积分不再增长，任务封顶。")
                        break
                    last_jf = total_jf

                    if "10 次" in progress: 
                        print("✅ 今日打卡已满 10 次。")
                        break
                        
                    wait_sec = data.get('sign_time', 560)
                    print(f"💤 冷却 {wait_sec + 5} 秒...")
                    time.sleep(wait_sec + 5)
                else:
                    print("❌ 获取进度失败，可能Token失效。")
                    break
            except: break

        # 2. 智能探测提现 [1.0, 0.2]
        withdraw_status = "未达标"
        if total_jf >= 20000:
            print(f"💰 任务结束，开始提现探测 (当前积分:{total_jf})...")
            for amount in [1.0, 0.2]:
                if total_jf < (amount * 100000): continue
                
                try:
                    res = requests.post(API_URL, json={"action":"withdrawalInfo","tx_ty":"jifen", "money": amount}, headers=headers, timeout=10).json()
                    msg = res.get('Message', '')
                    
                    if res.get('Status'):
                        time.sleep(3) # 等待数据库同步
                        data_after = get_balance(headers)
                        new_balance = int(float(data_after.get('user_jf') or 0)) if data_after else total_jf
                        
                        if new_balance < total_jf:
                            withdraw_status = f"✅ 成功({amount}元)"
                            break
                        else:
                            print(f"⚠️ {amount}元 返回成功但未扣分，判定为无效提现。")
                            withdraw_status = "❌ 额度受限(假成功)"
                    elif "小于 1" in msg:
                        withdraw_status = "📉 需满 1 元起提"
                        break 
                    else:
                        withdraw_status = f"❌ {msg[:10]}"
                except:
                    withdraw_status = "❌ 异常"
        
        summary_list.append(f"👤 账号: {name}\n💰 积分: {total_jf}\n🏧 状态: {withdraw_status}")

    if summary_list and push_func:
        push_func("🌟 星韵优选签到提现", "\n\n".join(summary_list))

if __name__ == "__main__":
    main()

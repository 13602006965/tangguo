# -*- coding: utf-8 -*-
import os, json, requests, time
from datetime import datetime
# ======================================================
# 同程旅行 V6 - 容错稳定版
# 1. 自动跳过异常任务 (解决 AI 规划任务 5000 报错)
# 2. 手机号#appToken#device#Security-Token#dp
#    风控很严需要五个参数都在同一请求体
# 3. 变量tc_gpt，多账号用 &分隔
# 4. 账号自动脱敏
# 5. cron 25 8 * * * 定时自行修改======================================================
push_func = None
try:
    import sys
    sys.path.append('/ql/scripts')
    from notify import send
    push_func = send
except: pass
TC_GPT = os.getenv("tc_gpt")
if not TC_GPT:
    print("❌ 环境变量 tc_gpt 缺失"); exit()
def get_headers(acc):
    return {
        'Host': 'app.17u.cn',
        'Accept': 'application/json, text/plain, */*',
        'channel': '1',
        'dp': acc['dp'],
        'appToken': acc['tk'],
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Content-Type': 'application/json',
        'Os-Type': '1',
        'Security-Token': acc['st'],
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 TcTravel/11.0.0 tctype/wk',
        'Referer': 'https://m.17u.cn/',
        'device': acc['dev'],
        'Connection': 'keep-alive'
    }
def main():
    accounts = []
    for item in TC_GPT.split("&&"):
        p = item.strip().split("#")
        if len(p) >= 5:
            accounts.append({"phone": p[0], "tk": p[1], "dev": p[2], "st": p[3], "dp": p[4]})
    summary_list = []
    for acc in accounts:
        mask_phone = f"{acc['phone'][:3]}****{acc['phone'][-4:]}"
        headers = get_headers(acc)
        print(f"\n{'='*15} 🚀 账号: {mask_phone} {'='*15}")
        try:
            # 1. 状态查询 (增加超时保护)
            res = requests.post("https://app.17u.cn/welfarecenter/index/signIndex", json={}, headers=headers, timeout=15).json()
            if res.get('code') != 2200:
                print(f"❌ 访问异常: {res.get('message')}"); continue
            
            data = res['data']
            print(f"📊 资产: {data['mileageBalance']['mileage']} | 今日: {data['mileageBalance']['todayMileage']}")
            # --- 签到补丁模块 (doSign) ---
            if not data.get('todaySign', False):
                print("📝 正在执行每日签到...")
                try:
                    sign_res = requests.post("https://app.17u.cn/welfarecenter/api/sign/doSign", json={}, headers=headers, timeout=15).json()
                    if sign_res.get('code') == 2200:
                        print(f"✅ 签到成功: {sign_res.get('message', '获得里程')}")
                    else:
                        print(f"⚠️ 签到结果: {sign_res.get('message')}")
                except: print("⚠️ 签到请求超时，跳过")
            else:
                print("📅 今日已签到，无需重复操作")
            # 2. 任务收割
            t_res = requests.post("https://app.17u.cn/welfarecenter/task/taskList?version=11.0.0.0", json={}, headers=headers, timeout=15).json()
            done_count = 0
            if t_res.get('code') == 2200:
                tasks = [t for t in t_res.get('data', []) if t.get('state') == 1 and t.get('browserTime', 0) > 0]
                print(f"📝 发现 {len(tasks)} 个可执行任务")
                
                for t in tasks:
                    print(f"📺 正在尝试: {t['title']}")
                    try:
                        s_res = requests.post("https://app.17u.cn/welfarecenter/task/start", json={"taskCode": t['taskCode']}, headers=headers, timeout=15).json()
                        
                        if s_res.get('code') == 2200:
                            task_id = s_res['data']
                            wait_time = t['browserTime'] + 2
                            print(f"⏳ 模拟浏览 {wait_time}s...")
                            time.sleep(wait_time)
                            
                            requests.post("https://app.17u.cn/welfarecenter/task/finish", json={"id": task_id}, headers=headers, timeout=15)
                            r_res = requests.post("https://app.17u.cn/welfarecenter/task/receive", json={"id": task_id}, headers=headers, timeout=15).json()
                            if r_res.get('code') == 2200:
                                print(f"✅ {t['title']} 领取成功")
                                done_count += 1
                        else:
                            print(f"⚠️ 跳过任务 '{t['title']}': {s_res.get('message')}({s_res.get('code')})")
                    except Exception as task_err:
                        print(f"⚠️ 任务执行异常，已自动跳过")
                    time.sleep(1)
            # 3. 最终结果汇总 (增加超时保护)
            time.sleep(2)
            try:
                f_res = requests.post("https://app.17u.cn/welfarecenter/index/signIndex", json={}, headers=headers, timeout=15).json()
                f_d = f_res['data']
                stat = (f"👤 {mask_phone}\n📅 签到: {f_d['cycleSighNum']}天 | 🎁 任务: +{done_count}\n"
                        f"💰 今日: +{f_d['mileageBalance']['todayMileage']} | 💎 总计: {f_d['mileageBalance']['mileage']}")
                print(f"\n📊 总结:\n{stat}")
                summary_list.append(stat)
            except:
                print("\n⚠️ 总结请求超时，里程已到账，请自行查看")
        except Exception as e:
            print(f"💥 账号运行异常: {e}")
    if summary_list and push_func:
        push_func("✈️ 同程旅行里程日报", "\n\n".join(summary_list))
if __name__ == "__main__":
    main()



     



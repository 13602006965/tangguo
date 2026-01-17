# -*- coding:utf-8 -*-
"""
小程序  衣城通 (YCT) V4.7.3
签到积分＋现金，任务是积分兑换实物
变量：yct_gpt ，格式备注@Auth，不需要Bearer 
功能：全任务执行 + 积分统计 + 青龙通知推送
参考定时：cron 25 13 * * * 定时自行修改
"""
import requests, os, time, json
from datetime import datetime

def send_qywx(title, content):
    qy_key = os.environ.get("QYWX_KEY")
    if not qy_key: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qy_key}"
    try: 
        requests.post(url, json={"msgtype": "text", "text": {"content": f"{title}\n{content}"}}, timeout=10)
    except: 
        pass

def run_yct(name, token):
    print(f"\n{'='*10} 🚀 开始处理: {name} {'='*10}")
    report = [f"👤 账号: {name}"]
    
    base_url = "https://api.yctjob.com/client"
    # 处理 Token 格式
    auth_token = f"Bearer {token}" if not token.startswith("Bearer ") else token
    headers = {
        "Authorization": auth_token,
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61",
        "Referer": "https://servicewechat.com/wxc4eaf0fd0c97862f/137/page-frame.html"
    }

    # --- 1. 动态签到模块 (已修复) ---
    print("📅 正在检查签到状态...")
    try:
        # 第一步：访问 signHome 获取今日动态 logId
        home_url = f"{base_url}/user/signHome"
        home_res = requests.get(home_url, headers=headers, timeout=10).json()
        
        if home_res.get("code") == 200:
            configs = home_res.get('data', {}).get('configs', [])
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            # 匹配今天的配置
            today_config = next((d for d in configs if d.get('signDate') == today_str), None)
            
            if today_config:
                if today_config.get('signStatus') == 1:
                    print(f"  ∟ 签到结果: 今日已签到，跳过动作")
                else:
                    # 第二步：使用当天的动态 logId 发起签到
                    target_log_id = today_config.get('logId')
                    sign_res = requests.post(f"{base_url}/user/sign", headers=headers, json={"logId": target_log_id}, timeout=10).json()
                    
                    # 第三步：关键刷新，强制触发后端积分结算
                    time.sleep(2)
                    requests.get(home_url, headers=headers, timeout=10)
                    
                    s_msg = sign_res.get("data", "成功") if sign_res.get("code") == 200 else sign_res.get("msg", "失败")
                    print(f"  ∟ 签到动作: {s_msg} (logId:{target_log_id})")
            else:
                print("  ∟ 错误: 未能在列表中找到今日签到配置")
        else:
            print(f"  ∟ 首页访问失败: {home_res.get('msg')}")
    except Exception as e:
        print(f"  ∟ 签到异常: {e}")

    # --- 2. 任务自动化执行明细  ---
    print("🎯 正在扫描任务中心...")
    try:
        # 原代码任务首页
        task_home_res = requests.get(f"{base_url}/user/taskHome", headers=headers, timeout=15).json()
        if task_home_res.get("code") == 200:
            all_tasks = task_home_res.get("data", {}).get("todayTask", []) + task_home_res.get("data", {}).get("experienceTask", [])
            for t in all_tasks:
                t_name, c_id = t.get("name"), t.get("id")
                # 排除无法自动完成的任务
                if any(x in t_name for x in ["邀请", "工友", "提现"]): continue
                
                todo = t.get("num", 1) - t.get("completeCount", 0)
                if todo > 0:
                    print(f"  🚩 准备执行: {t_name} (剩余{todo}次)")
                    for i in range(todo):
                        wait_sec = t.get("second", 2) + 2
                        time.sleep(wait_sec)
                        sub_res = requests.post(f"{base_url}/user/taskSub", headers=headers, json={"configId": c_id}).json()
                        print(f"    ∟ 第 {i+1} 次: {sub_res.get('msg', '提交成功')}")
                else:
                    print(f"  ✅ 任务已达上限: {t_name}")
    except Exception as e:
        print(f"  ❌ 任务模块运行出错: {e}")

    # --- 3. 资产精算与美化报表 (保持原版) ---
    print("📊 正在精算资产数据...")
    try:
        time.sleep(2)
        cur_month = datetime.now().strftime("%Y-%m")
        asset_url = f"{base_url}/user/integralUserLogList?month={cur_month}&pageNum=1&pageSize=20"
        asset_res = requests.get(asset_url, headers=headers, timeout=10).json()
        
        other_data = asset_res.get("other", {}).get("data", {})
        points = other_data.get("integral", "0")
        cash = other_data.get("amount", "0")

        # 统计今日收益
        today_income = 0
        today_str = datetime.now().strftime("%Y-%m-%d")
        for row in asset_res.get("rows", []):
            if today_str in row.get('createTime', ''):
                today_income += row.get('integral', 0)

        # 组装报表
        report.append(f"🏦 目前余额：{points} 💎")
        report.append(f"📈 今日获得：+{today_income}")
        report.append(f"💵 现金余额：{cash} 元")
        
        final_str = "\n".join(report)
        print(f"\n{'-'*30}\n{final_str}\n{'-'*30}")
        return final_str
    except:
        err = "📊 资产：结算异常"
        print(err)
        return err

def main():
    token_str = os.environ.get("yct_gpt")
    if not token_str: 
        print("❌ 未发现变量 yct_gpt")
        return
    
    # 支持 & 符分隔多账号
    accounts = token_str.replace('&', '\n').strip().split('\n')
    final_results = []
    for acc in accounts:
        if '@' in acc:
            name, tk = acc.split('@', 1)
            final_results.append(run_yct(name.strip(), tk.strip()))
            time.sleep(5) # 账号间停顿
    
    if final_results:
        send_qywx("📦 衣城通运行报告", "\n\n".join(final_results))
    print("\n✨ 所有账号处理完毕")

if __name__ == '__main__':
    main()

"""
飞蚂蚁旧衣服回收脚本 V4.5
功能: 签到 + 3连兑 + 实时余额 + 完整对账明细
变量名: fmy_gpt (备注@Auth)
"""
import requests, os, time

def send_qywx(title, content):
    qy_key = os.environ.get("QYWX_KEY")
    if not qy_key: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qy_key}"
    try: requests.post(url, json={"msgtype": "text", "text": {"content": f"{title}\n{content}"}}, timeout=10)
    except: pass

def run_fmy(name, tk):
    report = [f"--- 👤 {name} ---"]
    print(f"🚀 开始处理账号: {name}") # 日志打印
    
    p_key = "F2EE24892FBF66F0AFF8C0EB532A9394"
    headers = {
        "device-model": "iPhone 14 Pro",
        "content-type": "application/json;charset=utf8",
        "Authorization": f"bearer {tk}",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": "https://servicewechat.com/wx501990400906c9ff/483/page-frame.html"
    }

    # 1. 签到
    try:
        r = requests.post("https://openapp.fmy90.com/sign/new/do", headers=headers, json={"platformKey": p_key, "version": "V2.00.01"}, timeout=10).json()
        msg = f"📅 签到：{r.get('message', '已执行')}"
        report.append(msg)
        print(msg) # 同步到日志
    except Exception as e:
        print(f"❌ 签到异常: {e}")

    # 2. 步数兑换
    report.append("🏃 步数兑换：")
    step_data = {"platformKey": p_key, "mini_scene": 1089, "steps": 50000, "version": "V2.00.01"}
    for i in range(1, 4):
        try:
            res = requests.post("https://openapp.fmy90.com/step/exchange", headers=headers, json=step_data, timeout=10).json()
            if res.get("code") == 200:
                msg = f"  第{i}次: ✅成功(余{res['data'].get('leftSteps', 0)})"
            else:
                msg = f"  第{i}次: ❌{res.get('message')}"
            report.append(msg)
            print(msg) # 同步到日志
            if "最多兑换3次" in msg or "上限" in msg: break
            time.sleep(1)
        except: break

    # 3. 获取余额与明细
    try:
        u_info = requests.get("https://openapp.fmy90.com/api/user/info", headers=headers, timeout=10).json()
        real_beans = u_info['data'].get('beans', 0) if u_info.get("code") == 200 else "未知"
        
        income, expense, logs_list = 0, 0, []
        for t in [1, 2]:
            r_log = requests.get("https://openapp.fmy90.com/user/beans/log", headers=headers, params={"pageSize": 20, "type": t, "platformKey": p_key}).json()
            logs = r_log.get("data", {}).get("data", []) if isinstance(r_log.get("data"), dict) else []
            for i in logs:
                val = abs(int(i.get("beanNum", 0)))
                if t == 1: income += val
                else: expense += val
                logs_list.append({"date": str(i.get("addTime", "00-00"))[5:10], "msg": f"{'➕' if t==1 else '➖'} {val} 豆 ({i.get('beanInfo')})", "time": i.get("addTime")})
        
        logs_list.sort(key=lambda x: x["time"], reverse=True)
        
        summary = f"💰 **当前总积分：{real_beans} 颗 💎**\n📈 近期收入：{income} | 📉 近期支出：{expense}"
        report.append(summary)
        print(summary.replace("**", "")) # 打印不带Markdown格式的日志
        
        report.append("\n--- 📆 最近7条明细 ---")
        for l in logs_list[:7]:
            line = f"  {l['date']} {l['msg']}"
            report.append(line)
            print(line)
    except Exception as e:
        print(f"⚠️ 数据对账异常: {e}")
    
    return "\n".join(report)

def main():
    token_str = os.environ.get("fmy_gpt")
    if not token_str: 
        print("❌ 错误: 未找到环境变量 fmy_gpt")
        return
    
    final_msgs = []
    for line in token_str.split('\n'):
        if not line.strip(): continue
        name, tk = line.split('@', 1) if '@' in line else ("糖果块儿", line)
        final_msgs.append(run_fmy(name.strip(), tk.strip()))
    
    print("\n📤 正在发送企业微信推送...")
    send_qywx("🐜 飞蚂蚁报告 V4.5", "\n\n".join(final_msgs))
    print("✨ 执行完毕")

if __name__ == '__main__':
    main()

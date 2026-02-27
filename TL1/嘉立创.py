import os, requests, time

# ================= 配置区 =================
# 名称：小程序  嘉立创签到 V1.0
# 变量：jlc_gpt（备注#X-JLC-AccessToken#secretkey）多账号&分割或换行分割
# 功能：签到＋积分统计＋美化推送
# 定时：cron 45 5 * * * 每天一次自行修改
# ==========================================

def push_msg(title, content):
    """双保险推送逻辑"""
    log("🚀 正在尝试推送...")
    pushed = False
    
    # 1. 尝试青龙标准脚本推送
    for module_name in ["sendNotify", "notify"]:
        try:
            m = __import__(module_name)
            if hasattr(m, "send"):
                m.send(title, content)
                log(f"✅ 通过 {module_name} 推送成功")
                pushed = True
                break
        except: continue
    
    # 2. 如果标准推送失败，尝试企业微信直连
    if not pushed:
        qy_key = os.getenv("QYWX_KEY")
        if qy_key:
            try:
                url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qy_key}"
                payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
                requests.post(url, json=payload, timeout=10)
                log("✅ 标准推送失效，已通过 QYWX_KEY 直连成功")
            except: pass

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def start():
    env = os.getenv("jlc_gpt")
    if not env:
        log("❌ 未找到变量: jlc_gpt")
        return

    summary = []
    for account in env.split("&"):
        if "#" not in account: continue
        parts = account.split("#")
        if len(parts) < 3: continue
        name, token, secret = parts[0], parts[1], parts[2]
        
        headers = {
            "x-jlc-accesstoken": token,
            "secretkey": secret,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Content-Type": "application/json;charset=UTF-8"
        }

        try:
            # 1. 签到状态
            st = requests.get("https://m.jlc.com/api/activity/sign/getCurrentUserSignInConfig?platformType=MP-WEIXIN", headers=headers, timeout=10).json()
            if st.get("data", {}).get("haveSignIn"):
                res_msg = "⚠️今日已签"
            else:
                # 2. 执行签到
                si = requests.get("https://m.jlc.com/api/activity/sign/signIn?platformType=MP-WEIXIN&source=2", headers=headers, timeout=10).json()
                res_msg = f"✅成功(+{si.get('data', {}).get('gainNum', 0)})" if si.get("success") else f"❌失败:{si.get('message')}"

            # 3. 查资产
            asset = requests.get("https://m.jlc.com/api/activity/front/getCustomerIntegral", headers=headers, timeout=10).json()
            total = asset.get("data", {}).get("integralVoucher", "未知")
            
            info = f"👤 {name} | {res_msg} | 💰豆豆: {total}"
            log(info)
            summary.append(info)
            
        except Exception as e:
            err = f"👤 {name} | 💥 异常: {e}"
            log(err)
            summary.append(err)

    if summary:
        push_msg("嘉立创🙋‍♀️报告", "\n".join(summary))

if __name__ == "__main__":
    start()

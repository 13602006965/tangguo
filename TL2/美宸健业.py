######################################
# 小程序：美宸健业
# 变量名：mcjyck='账号#密码'
# 多号换行
# 更新日期:2025-04-18
# version:1.0.1 (修复版)
# by:不靠谱的AI
######################################
import requests
import json
import os
import sys
import time

# ----------------- 核心功能区 -----------------

def login(account, password):
    """执行登录"""
    url = "https://api.mcjy.com/api/auth/login"
    headers = {
        "Device-Brand": "xiaomi",
        "Form-type": "app",
        "type": "0",
        "version": "3.0.9",
        "Form-drive": "android",
        "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
    }
    
    payload = {
        "placeCode": "+86",
        "auth_token": "",
        "account": account,
        "password": password
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return response.json()
    except Exception as e:
        print(f"登录请求异常: {e}")
        return {"status": 0, "message": str(e)}

def sign_in(token):
    """执行签到"""
    url = "https://api.mcjy.com/api/user/sign"
    headers = {
        "Device-Brand": "xiaomi",
        "Form-type": "app",
        "X-Token": f"Bearer {token}",
        "type": "0",
        "version": "3.0.9",
        "Form-drive": "android",
        "Content-Type": "application/json",
        "user-agent": "Mozilla/5.0 (Linux; Android 12; 22041211AC Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.39 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/29.714285)",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        return {"status": 0, "message": str(e)}

def get_user_info(token):
    """获取用户信息"""
    url = "https://api.mcjy.com/api/user"
    headers = {
        "Device-Brand": "xiaomi",
        "Form-type": "app",
        "X-Token": f"Bearer {token}",
        "type": "0",
        "version": "3.0.9",
        "Form-drive": "android",
        "Content-Type": "application/json",
        "user-agent": "Mozilla/5.0 (Linux; Android 12; 22041211AC Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.39 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/29.714285)",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        return {"status": 0, "message": str(e)}

# ----------------- 辅助功能区 -----------------

def get_accounts_from_env():
    """解析环境变量，增加容错"""
    accounts_str = os.getenv("mcjyck", "")
    accounts = {}
    
    if not accounts_str:
        print("⚠️ 未找到环境变量 mcjyck，请检查配置。")
        return accounts

    for line in accounts_str.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "#" not in line:
            print(f"🚫 账号格式错误 (缺少#): {line}")
            continue
            
        try:
            # 只分割第一个#，防止密码里也有#
            parts = line.split("#", 1)
            account = parts[0].strip()
            password = parts[1].strip()
            accounts[account] = password
        except Exception as e:
            print(f"🚫 账号解析异常: {line}, 错误: {e}")
            
    return accounts

def notify_send(text):
    """统一推送通知 (修复了 await 错误)"""
    try:
        notify_path = ''
        if os.path.exists('/ql/data/scripts/notify.py'):
            notify_path = '/ql/data/scripts/notify.py'
        elif os.path.exists('./notify.py'):
            notify_path = './notify.py'
        
        if not notify_path:
            print("🔕 未找到 notify.py 文件，跳过推送")
            return
        
        # 动态导入
        sys.path.append(os.path.dirname(notify_path))
        from notify import send
        
        # 这里的 send 是同步函数，不能用 await
        print("📨 开始执行推送...")
        send("美宸健业通知", text)
        
    except Exception as e:
        print(f"❌ 推送通知异常: {str(e)}")

# ----------------- 主程序 -----------------

def main():
    print("🚀 任务启动...")
    accounts = get_accounts_from_env()
    
    if not accounts:
        print("❌ 无有效账号，任务结束。")
        return

    notifications = []
    
    for account, password in accounts.items():
        print(f"\n👤 正在处理账号: {account}")
        
        # 1. 登录
        login_res = login(account, password)
        
        if login_res.get('status') == 200:
            token = login_res.get('data', {}).get('token')
            if not token:
                print("❌ 登录成功但未获取到Token")
                continue
                
            print("✅ 登录成功，准备签到...")
            
            # 2. 签到
            sign_res = sign_in(token)
            msg_line = ""
            
            if sign_res.get('status') == 200:
                print("🎉 签到成功")
                msg_line += f"账号: {account}\n状态: ✅ 签到成功\n"
            else:
                fail_msg = sign_res.get('message', '未知错误')
                print(f"🥀 签到失败: {fail_msg}")
                msg_line += f"账号: {account}\n状态: ❌ {fail_msg}\n"
            
            # 3. 获取积分
            user_res = get_user_info(token)
            if user_res.get('status') == 200:
                integral = user_res.get('data', {}).get('integral', '未知')
                print(f"💰 当前积分: {integral}")
                msg_line += f"积分: {integral}\n"
            else:
                msg_line += f"积分: 获取失败\n"
                
            notifications.append(msg_line + "-"*15)
            
        else:
            err_msg = login_res.get('message', '登录接口异常')
            print(f"❌ 登录失败: {err_msg}")
            notifications.append(f"账号: {account}\n状态: ❌ 登录失败 ({err_msg})\n" + "-"*15)
        
        # 账号间随机延迟，防风控
        time.sleep(2)

    # 统一推送
    if notifications:
        notify_content = "\n".join(notifications)
        notify_send(notify_content)

    print("\n🏁 任务执行结束。")

if __name__ == "__main__":
    main()
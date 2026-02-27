# 当前脚本来自于 http://script.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cc 脚本库下载！
# 脚本库官方QQ群1群: 429274456
# 脚本库官方QQ群2群: 1077801222
# 脚本库官方QQ群3群: 433030897
# 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# 您在使用脚本库下载的脚本时自行检查判断风险。
# 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

"""
牛卡福货主端 - 青龙面板脚本（无卡密版本）
功能: TOKEN登录 + 每日签到 + 动态代理
环境变量: 
  - NKF_TOKENS: TOKEN (多账号用&或换行分隔)
  - NKF_PROXY_API: 代理API地址 (可选)
  - NKF_PROXY_REFRESH_INTERVAL: 代理切换最小间隔秒数 (默认8秒)
cron: 0 8 * * *
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

class WxPusher:
    """WxPusher推送类"""
    def __init__(self, uid, token):
        self.uid = uid
        self.token = token
        self.api_url = "http://wxpusher.zjiecode.com/api/send/message"
    
    def send(self, title, content):
        """发送推送消息"""
        if not self.uid or not self.token:
            return False
        
        try:
            data = {
                "appToken": self.token,
                "content": content,
                "summary": title,
                "contentType": 1,
                "uids": [self.uid]
            }
            response = requests.post(self.api_url, json=data, timeout=10)
            result = response.json()
            return result.get("code") == 1000
        except Exception as e:
            return False

class ProxyManager:
    """动态代理管理器"""
    def __init__(self, proxy_api=None, refresh_interval=8):
        self.proxy_api = proxy_api
        self.refresh_interval = refresh_interval  # 切换间隔（秒）
        self.current_proxy = None
        self.last_refresh_time = 0  # 上次切换代理的时间
        
    def get_proxy(self):
        """获取代理IP（仅在没有代理时获取）"""
        if not self.proxy_api:
            return None
        
        # 如果已有代理，直接返回（不再自动切换）
        if self.current_proxy:
            return self.current_proxy
        
        try:
            response = requests.get(self.proxy_api, timeout=10)
            if response.status_code == 200:
                proxy_text = response.text.strip()
                if proxy_text:
                    parts = proxy_text.split()
                    
                    if len(parts) == 3:
                        ip_port, username, password = parts
                        proxy_url = f'socks5://{username}:{password}@{ip_port}'
                        self.current_proxy = {
                            'http': proxy_url,
                            'https': proxy_url
                        }
                        print(f"[代理] 获取新代理: {ip_port} (用户: {username})")
                    elif len(parts) == 1:
                        proxy_url = f'socks5://{parts[0]}'
                        self.current_proxy = {
                            'http': proxy_url,
                            'https': proxy_url
                        }
                        print(f"[代理] 获取新代理: {parts[0]}")
                    else:
                        print(f"[代理] 代理格式不支持: {proxy_text}")
                        return None
                    
                    return self.current_proxy
        except Exception as e:
            print(f"[代理] 获取代理失败: {str(e)}")
        
        return None
    
    def refresh_proxy(self):
        """刷新代理（检查间隔限制）"""
        if not self.proxy_api:
            return None
        
        current_time = time.time()
        time_since_last_refresh = current_time - self.last_refresh_time
        
        # 检查是否满足切换间隔
        if self.last_refresh_time > 0 and time_since_last_refresh < self.refresh_interval:
            remaining_time = int(self.refresh_interval - time_since_last_refresh)
            print(f"[代理] 距离上次切换仅{int(time_since_last_refresh)}秒，需等待{remaining_time}秒后才能切换")
            return self.current_proxy  # 返回当前代理，不切换
        
        print(f"[代理] 强制刷新代理...")
        self.current_proxy = None  # 清空当前代理
        new_proxy = self.get_proxy()
        
        if new_proxy:
            self.last_refresh_time = current_time  # 更新切换时间
        
        return new_proxy

class NiuKaFu:
    def __init__(self, token, proxy_manager=None):
        self.token = token
        self.session = requests.Session()
        self.base_url = "https://shippers.nucarf.net"
        self.proxy_manager = proxy_manager
        
        import uuid
        import hashlib
        device_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16]
        
        self.headers = {
            "content-type": "application/json",
            "user-agent": "okhttp/3.14.9",
            "x-access-token": token,
            "oss-token": token,
            "x-apptype": "APP",
            "x-device-type": "ANDROID",
            "x-device-id": device_id,
            "x-device-name": "Android",
            "x-appversion": "2.4.7",
            "x-term-id": "30971511",
            "request-source": "ONE_STOP_WX_DISPATCH",
            "accept-encoding": "gzip"
        }
        
    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def request_with_retry(self, method, url, max_retries=3, **kwargs):
        """带重试的请求方法"""
        for attempt in range(1, max_retries + 1):
            try:
                if self.proxy_manager:
                    # 首次使用当前代理，失败后尝试切换
                    if attempt > 1:
                        proxies = self.proxy_manager.refresh_proxy()
                    else:
                        proxies = self.proxy_manager.get_proxy()
                    kwargs['proxies'] = proxies
                
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
                
                return response
            except Exception as e:
                if attempt < max_retries:
                    self.log(f"  请求失败(第{attempt}次),{max_retries-attempt}秒后重试... 错误: {str(e)[:50]}")
                    time.sleep(max_retries - attempt)
                else:
                    raise e
        
    def get_user_info(self):
        """获取用户信息"""
        try:
            url = f"{self.base_url}/api/shippers/user/mine"
            response = self.request_with_retry('GET', url, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 200:
                user_info = data.get("data", {}).get("userInfo", {})
                phone = user_info.get("phoneNo", "未知")
                username = user_info.get("userName", "未知")
                wallet = data.get("data", {}).get("walletAmount", "0")
                points = data.get("data", {}).get("pointAmount", 0)
                
                self.log(f"✓ 用户: {username} ({phone})")
                self.log(f"  钱包余额: {wallet}元 | 积分: {points}")
                return True
            else:
                self.log(f"✗ 获取用户信息失败: {data.get('message', '未知错误')}")
                return False
        except Exception as e:
            self.log(f"✗ 获取用户信息异常: {str(e)}")
            return False
    
    def check_sign_status(self):
        """检查签到状态"""
        try:
            url = f"{self.base_url}/api/campaign/dailySignIn"
            response = self.request_with_retry('GET', url, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 200:
                sign_data = data.get("data", {})
                sign_count = sign_data.get("signInCount", 0)
                sign_status = sign_data.get("signInStatus", False)
                
                self.log(f"  已连续签到: {sign_count}天")
                
                if sign_status:
                    self.log(f"  今日已签到 ✓")
                    return True
                else:
                    self.log(f"  今日未签到,准备签到...")
                    return False
            else:
                self.log(f"✗ 查询签到状态失败: {data.get('message', '未知错误')}")
                return None
        except Exception as e:
            self.log(f"✗ 查询签到状态异常: {str(e)}")
            return None
    
    def do_sign_in(self):
        """执行签到"""
        try:
            url = f"{self.base_url}/api/campaign/signIn"
            response = self.request_with_retry('POST', url, headers=self.headers, json={}, timeout=10)
            data = response.json()
            
            if data.get("code") == 200:
                result = data.get("data", {})
                points = result.get("pointAmount", 0)
                day = result.get("day", 0)
                
                self.log(f"✓ 签到成功! 获得 {points} 积分 (第{day}天)")
                return True
            else:
                self.log(f"✗ 签到失败: {data.get('message', '未知错误')}")
                return False
        except Exception as e:
            self.log(f"✗ 签到异常: {str(e)}")
            return False
    
    def get_points_info(self):
        """获取积分信息"""
        try:
            url = f"{self.base_url}/api/campaign/pointList"
            response = self.request_with_retry('GET', url, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 200:
                self.log(f"✓ 积分详情获取成功")
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def run(self):
        """主流程,返回: True=成功, False=失败, None=TOKEN失效"""
        self.log("=" * 50)
        self.log("开始执行牛卡福货主端任务")
        
        if not self.get_user_info():
            self.log("✗ TOKEN无效或已过期")
            return None  # TOKEN失效
        
        sign_status = self.check_sign_status()
        
        if sign_status is None:
            self.log("✗ 无法获取签到状态")
            return False
        elif sign_status:
            self.log("✓ 今日已完成签到")
        else:
            time.sleep(2)
            if self.do_sign_in():
                self.log("✓ 签到任务完成")
            else:
                self.log("✗ 签到任务失败")
                return False
        
        self.get_points_info()
        self.log("=" * 50)
        return True


def main():
    print("\n" + "=" * 50)
    print("牛卡福货主端 - 青龙面板脚本（无卡密版本）")
    print("=" * 50)
    print("功能: TOKEN登录 + 每日签到 + 动态代理")
    print("=" * 50)
    print("环境变量:")
    print("  - NKF_TOKENS: TOKEN (多账号用&或换行分隔)")
    print("  - NKF_PROXY_API: 代理API地址 (可选)")
    print("  - NKF_PROXY_REFRESH_INTERVAL: 代理切换最小间隔秒数 (默认8秒)")
    print("=" * 50)
    print("定时: 0 8 * * *")
    print("=" * 50 + "\n")
    
    # 读取环境变量
    tokens = os.getenv("NKF_TOKENS", "")
    proxy_api = os.getenv("NKF_PROXY_API", "")
    proxy_refresh_interval = int(os.getenv("NKF_PROXY_REFRESH_INTERVAL", "8"))
    
    # 内置WXPUSHER配置
    wxpusher_uid = "UID_wKMNDiMz6JQDgjQj1aDoPPRakrci"
    wxpusher_token = "AT_628wlqjF9AefIpWMrW3f0qEhZgi6F7wS"
    
    # 初始化WxPusher
    wx_pusher = WxPusher(wxpusher_uid, wxpusher_token)
    
    # 检查是否启用代理
    use_proxy = bool(proxy_api)
    if use_proxy:
        print(f"✓ 已启用动态代理")
        print(f"  代理API: {proxy_api[:50]}...")
        print(f"  切换间隔: {proxy_refresh_interval}秒")
        print(f"  策略: 每个账号使用独立IP，仅在请求失败时切换代理\n")
    else:
        print("未配置代理,直连模式\n")
    
    if not tokens:
        print("✗ 未配置环境变量 NKF_TOKENS")
        print("请在青龙面板添加环境变量:")
        print("变量名: NKF_TOKENS")
        print("变量值: 你的token (多账号用&或换行分隔)")
        return
    
    token_list = []
    if "&" in tokens:
        token_list = tokens.split("&")
    elif "\n" in tokens:
        token_list = tokens.split("\n")
    else:
        token_list = [tokens]
    
    token_list = [t.strip() for t in token_list if t.strip()]
    
    print(f"共找到 {len(token_list)} 个账号\n")
    
    success_count = 0
    fail_count = 0
    token_invalid_count = 0
    
    for i, token in enumerate(token_list, 1):
        print(f"\n【账号 {i}】")
        
        # 为每个账号创建独立的代理管理器，确保每个账号使用不同的IP
        account_proxy_manager = None
        if use_proxy:
            account_proxy_manager = ProxyManager(proxy_api, proxy_refresh_interval)
            print(f"  为账号 {i} 分配独立代理...")
        
        nkf = NiuKaFu(token, account_proxy_manager)
        
        try:
            result = nkf.run()
            if result is True:
                success_count += 1
            elif result is None:
                token_invalid_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"✗ 账号 {i} 执行异常: {str(e)}")
            fail_count += 1
        
        if i < len(token_list):
            time.sleep(10)
    
    # 总结信息
    total = len(token_list)
    summary = f"""
========================================
📊 执行总结
========================================
总账号数: {total}
✅ 签到成功: {success_count}
❌ 签到失败: {fail_count}
🔒 TOKEN失效: {token_invalid_count}
========================================
"""
    
    print(summary)
    
    # 发送推送(静默)
    if wx_pusher:
        push_content = f"""牛卡福货主端签到完成
        
总账号: {total}
签到成功: {success_count}
签到失败: {fail_count}
TOKEN失效: {token_invalid_count}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        try:
            wx_pusher.send("牛卡福货主端签到通知", push_content)
        except:
            pass


if __name__ == "__main__":
    main()


# 当前脚本来自于 http://script.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cn 脚本库下载！
# 当前脚本来自于 http://2.345yun.cc 脚本库下载！
# 脚本库官方QQ群1群: 429274456
# 脚本库官方QQ群2群: 1077801222
# 脚本库官方QQ群3群: 433030897
# 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# 您在使用脚本库下载的脚本时自行检查判断风险。
# 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。
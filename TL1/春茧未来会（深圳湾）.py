# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# 【使用说明】
# 1. 小程序  春茧未来会（深圳湾）签到V2.0
# 2. 账号变量名: szw_gpt
#    格式: 备注#Cookie (多个账号用 & 或 换行 分隔)
# 3. 功能特性: 
#    - 日常战报: 发送至青龙面板配置的微信/钉钉通道 (notify.py)。
#    - 失效告警: 仅在 Cookie 失效时，通过下方配置的 PushPlus 发送提醒。
# 4.定时参考 cron 15 5 * * * 每天一次自行修改
# -------------------------------------------------------------------------

import requests
import re
import os
import time
import ssl
from datetime import datetime
from requests.adapters import HTTPAdapter

# ==================== 【配置区 - 方便修改】 ====================

# 在这里填入你的 PushPlus Token (用于失效告警)
PUSHPLUS_TOKEN = "e2ea7eeb14be40e5a9971f4f3664d291" 

# =============================================================

try:
    from notify import send as ql_send
except ImportError:
    ql_send = None

# 精准还原：核心 SSL 适配器，开启 0x4 模式
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4  # 核心： legacy_server_connect，解决老服务器连接问题
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

class SpringCocoon:
    def __init__(self, remark, cookie):
        self.remark = remark
        self.cookie = cookie.strip()
        self.session = requests.Session()
        self.session.mount("https://", TLSAdapter())
        self.is_expired = False

    def run(self):
        token_match = re.search(r'XSRF-TOKEN=([^;]+)', self.cookie)
        if not token_match:
            self.is_expired = True
            return 0, "❌ Cookie 缺失 XSRF 字段"

        url = "https://program.springcocoon.com/szbay/api/services/app/SignInRecord/SignInAsync"
        
        # 严格对齐老脚本的请求头
        headers = {
            'Host': 'program.springcocoon.com',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-XSRF-TOKEN': token_match.group(1),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://program.springcocoon.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781 NetType/WIFI MiniProgramEnv/Windows',
            'Referer': 'https://program.springcocoon.com/szbay/AppInteract/SignIn/Index?isWeixinRegister=true',
            'Connection': 'keep-alive',
            'Cookie': self.cookie
        }

        # 还原老脚本的 DATA 负载
        payload = "id=6c3a00f6-b9f0-44a3-b8a0-d5d709de627d&webApiUniqueID=f2cca2a7-c327-1d76-d375-ec92cdd296cd"
        
        try:
            # 使用二进制编码发送，增加稳定性
            data_bytes = payload.encode('utf-8')
            headers["Content-Length"] = str(len(data_bytes))
            
            res = self.session.post(url, headers=headers, data=data_bytes, timeout=30)
            
            # --- 智能解析区 ---
            # 情况1: 正常成功 (200)
            if res.status_code == 200:
                result = res.json()
                if result.get("success"):
                    point = result["result"]["listSignInRuleData"][0]["point"]
                    return int(point), f"✅ 签到成功 (+{point}星)"
            
            # 情况2: 业务判定 (无论 200 还是 500)
            # 该服务器会将“重复签到”抛出 500 错误，需要捕获内容
            if "不可重复签到" in res.text:
                return 0, "📅 今日已签到 ✅"
            
            # 情况3: 账号失效 (401 或 403)
            if res.status_code in [401, 403]:
                self.is_expired = True
                return 0, "❌ 登录已失效 (请更新Cookie)"
            
            # 情况4: 真正的服务器报错
            return 0, f"⚠️ 服务器响应异常 ({res.status_code})"

        except Exception as e:
            return 0, f"🌐 请求异常: 网络不稳定"

def main():
    raw_env = os.getenv("szw_gpt")
    if not raw_env:
        print("❌ 未设置环境变量 szw_gpt")
        return
    
    # 解析多账号
    accounts = raw_env.replace('&', '\n').strip().splitlines()
    summary = []     # 日常战报
    expired_log = [] # 紧急告警
    total_star = 0
    
    print(f"🚀 春茧未来荟启动 | 强力模拟模式 | 账号数: {len(accounts)}\n")

    for i, acc in enumerate(accounts, 1):
        # 备注识别
        if "#" in acc:
            remark, ck = acc.split("#")[:2]
        else:
            remark, ck = f"账号{i}", acc
            
        worker = SpringCocoon(remark, ck)
        points, status = worker.run()
        
        total_star += points
        summary.append(f"👤 【{remark}】: {status}")
        
        # 记录失效账号
        if "失效" in status or "缺失" in status:
            expired_log.append(f"🔴 {remark}: {status}")
            
        time.sleep(3) # 账号间隔，保护频率

    # 1. 发送日常战报 (面板 notify.py 渠道)
    report_title = "🌸 春茧未来荟🙋‍♀️"
    report_content = "\n".join(summary)
    report_content += f"\n\n✨ 今日总计获得: {total_star} 万象星"
    report_content += f"\n⏰ 执行时间: {datetime.now().strftime('%m-%d %H:%M')}"
    
    if ql_send:
        ql_send(report_title, report_content)
    else:
        print(f"\n{report_title}\n{report_content}")

    # 2. 发送失效告警 (PushPlus 渠道)
    if expired_log and PUSHPLUS_TOKEN and "填入" not in PUSHPLUS_TOKEN:
        alert_msg = "检测到以下账号 Cookie 失效，请及时更新：\n\n" + "\n".join(expired_log)
        url = "http://www.pushplus.plus/send"
        data = {
            "token": PUSHPLUS_TOKEN,
            "title": "⚠️ 春茧账号失效告警",
            "content": alert_msg.replace("\n", "<br>"),
            "template": "html"
        }
        try:
            requests.post(url, json=data, timeout=15)
            print("📢 已发送 PushPlus 紧急失效告警")
        except:
            print("❌ PushPlus 告警发送失败")

if __name__ == "__main__":
    main()


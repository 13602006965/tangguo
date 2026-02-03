# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------
# AVALON挖矿，每个币目前1R
# 下载注册地址:https://urlab.oss-rg-china-mainland.aliyuncs.com/avs?code=37350977
# 变量名: awl_gpt (格式: 备注#token#机型, 多个用&或换行)
#        账号1#eyfr……#苹果8p（机型是为了生成自己的UA）内嵌：苹果，华为，小米，OPPO，VIVO
# 定时设置 cron 0 0 */8 * * （自行修改每天三到四次）
#------------------------------------------------------------------------------------
import requests
import os
import time
import hashlib
from datetime import datetime

# ==================== 推送配置 ====================
send = None
try:
    from notify import send
except ImportError:
    def send(title, content):
        print("\n[推送通知未配置或找不到notify.py]")
# =================================================

class AvalonPro:
    def __init__(self, remark, token, model_name):
        self.remark = remark
        self.token = token.strip()
        if not self.token.startswith('Bearer '):
            self.token = f"Bearer {self.token}"
        
        # 1. 环境构建
        self.device_id, self.ua = self.build_env(remark, model_name)
        
        self.headers = {
            "Host": "app.avalonavs.com",
            "Authorization": self.token,
            "User-Agent": self.ua,
            "X-Device-ID": self.device_id,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "com.avalonavs.app",
            "Referer": "http://app.avalonavs.com/",
        }
        
        self.info_str = ""  # 单账号日志汇总
        self.success_count = 0 # 收取成功数

    def build_env(self, remark, model_name):
        seed = hashlib.md5(remark.encode()).hexdigest()
        dev_id = f"0.{seed[:11]}"
        model_map = {
            "苹果": "iPhone; CPU iPhone OS 17_2 like Mac OS X",
            "小米": "Linux; Android 13; 23127PN0CC Build/UKQ1.230804.001",
            "华为": "Linux; Android 12; NOH-AN00 Build/HUAWEINOH-AN00",
            "OPPO": "Linux; Android 14; PHN110 Build/UKQ1.230917.001",
            "vivo": "Linux; Android 13; V2324A Build/TP1A.220624.014"
        }
        platform = model_map.get("小米")
        for k, v in model_map.items():
            if k in model_name: platform = v; break
            
        ua = f"Mozilla/5.0 ({platform}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.178 Mobile Safari/537.36 Xweb/1310043 MMWEBSDK/20241201"
        return dev_id, ua

    def log(self, msg):
        print(f"[{self.remark}] {msg}")
        self.info_str += f"{msg}\n"

    def run_task(self):
        try:
            # 1. 基本信息
            res = requests.get("https://app.avalonavs.com/api/app/api/customer_ext/personalDetails", headers=self.headers, timeout=15).json()
            if res.get('code') != 0:
                self.log(f"❌ Token失效: {res.get('msg')}")
                return None
            
            d = res['data']
            coin = d.get('coin', '0')
            hash_rate = d.get('hashRate', '0')
            self.log(f"💰 账户余额: {coin} AVS")
            self.log(f"⚡️ 当前算力: {hash_rate}")

            # 2. 签到
            s_res = requests.post("https://app.avalonavs.com/api/app/api/signIn/keepSignIn", headers=self.headers, data="", timeout=15).json()
            sign_msg = "成功 ✅" if s_res.get('code') == 0 else s_res.get('msg', '已签')
            self.log(f"📅 签到反馈: {sign_msg}")

            # 3. 收取
            time.sleep(1)
            l_res = requests.get("https://app.avalonavs.com/api/app/api/income/incomeList?balanceCapitalTyp=coin", headers=self.headers, timeout=15).json()
            items = l_res.get('data', [])
            if items:
                for item in items:
                    i_id = item.get('id')
                    r_res = requests.post(f"https://app.avalonavs.com/api/app/api/income/receiveIncome/{i_id}", headers=self.headers, data=f"id={i_id}", timeout=15).json()
                    if r_res.get('code') == 0: self.success_count += 1
                self.log(f"⛏️ 收取反馈: 成功采矿 {self.success_count} 枚")
            else:
                self.log(f"⛏️ 收取反馈: 暂无待收收益")
            
            return float(coin)
        except Exception as e:
            self.log(f"⚠️ 运行异常")
            return None

def main():
    raw_env = os.getenv("awl_gpt")
    if not raw_env:
        print("❌ 未设置变量 awl_gpt"); return
    
    accounts = raw_env.replace('&', '\n').strip().splitlines()
    summary_list = []
    total_assets = 0.0
    
    print(f"🔔 开始执行 AVALON 自动化任务 (共 {len(accounts)} 个账号)\n")
    
    for acc in accounts:
        parts = acc.split("#")
        if len(parts) < 3: continue
        
        remark, token, model = parts[0], parts[1], parts[2]
        worker = AvalonPro(remark, token, model)
        balance = worker.run_task()
        
        if balance is not None:
            total_assets += balance
            summary_list.append(f"👤 【{remark}】\n{worker.info_str}")
        
        time.sleep(3) # 账号间隔

    # 汇总推送
    if summary_list:
        push_content = "\n".join(summary_list)
        push_content += f"\n-------------------------\n"
        push_content += f"📊 总账户预估收益: {round(total_assets, 2)} AVS\n"
        push_content += f"⏰ 执行时间: {datetime.now().strftime('%m-%d %H:%M')}"
        
        send("🚀 AVALON 自动挖矿战报", push_content)

if __name__ == "__main__":
    main()

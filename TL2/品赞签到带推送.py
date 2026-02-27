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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品赞代理签到脚本 - 青龙面板版

更新:
1. 添加青龙消息推送功能
2. 手机号脱敏处理（显示后4位）
3. 优化签到结果汇总

说明:
品赞是一个HTTP优质代理IP服务供应商。每周签到得3金币（1金币约等于1块钱）
环境变量: export IPZAN_ACCOUNT="phone=手机号;pwd=密码
多账号使用换行或&分割
注册地址: https://www.ipzan.com?pid=vtl1ai9mo
cron: 10 0 * * 0
"""

import os
import re
import json
import time
import base64
import random
import requests
from datetime import datetime

class IPZanSign:
    def __init__(self):
        self.BASE_URL = "https://service.ipzan.com"
        self.accounts = []
        self.results = []
        self.push_messages = []  # 存储推送消息
        self.start_time = datetime.now()
        self.load_accounts()
        
        # 初始化推送标题
        self.push_title = "品赞代理签到结果"

    def load_accounts(self):
        """从环境变量加载账号信息"""
        account_var = os.getenv('IPZAN_ACCOUNT', '')
        if not account_var:
            print("❌ 未找到环境变量 IPZAN_ACCOUNT")
            return False
        
        # 分割多账号
        accounts = re.split(r'[\n&]', account_var)
        for acc in accounts:
            if not acc:
                continue
                
            account_info = {}
            for pair in acc.split(';'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    account_info[key.strip()] = value.strip()
            
            if account_info.get('phone') or account_info.get('token'):
                self.accounts.append(account_info)
        
        print(f"✅ 成功加载 {len(self.accounts)} 个账号")
        return True

    def mask_phone(self, phone):
        """手机号脱敏处理（隐藏前7位）"""
        if not phone or len(phone) < 4:
            return "未知用户"
        return f"******{phone[-4:]}" if len(phone) == 11 else phone

    def custom_base64_encode(self, text):
        """自定义Base64编码函数"""
        table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        result = []
        padding = 0
        
        # 转换为字节
        byte_text = text.encode('utf-8')
        length = len(byte_text)
        
        for i in range(0, length, 3):
            chunk = byte_text[i:i+3]
            
            # 处理不足3字节的情况
            if len(chunk) < 3:
                padding = 3 - len(chunk)
                chunk += b'\x00' * padding
            
            # 将3字节转换为4个6位组
            n = (chunk[0] << 16) | (chunk[1] << 8) | chunk[2]
            
            idx1 = (n >> 18) & 0x3F
            idx2 = (n >> 12) & 0x3F
            idx3 = (n >> 6) & 0x3F
            idx4 = n & 0x3F
            
            result.append(table[idx1])
            result.append(table[idx2])
            result.append(table[idx3] if padding < 2 else '=')
            result.append(table[idx4] if padding < 1 else '=')
        
        return ''.join(result)

    def login(self, phone, password):
        """登录获取token"""
        try:
            salt = "QWERIPZAN1290QWER"
            plain_text = phone + salt + password
            encoded = self.custom_base64_encode(plain_text)
            
            # 生成400字符随机字符串
            t = ''.join(random.choices('0123456789abcdef', k=400))
            
            # 构建account参数
            account = (
                t[:100] + 
                encoded[:8] + 
                t[100:200] + 
                encoded[8:20] + 
                t[200:300] + 
                encoded[20:] + 
                t[300:400]
            )
            
            payload = {
                "account": account,
                "source": "ipzan-home-one"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/users-login",
                json=payload,
                timeout=15
            )
            
            data = response.json()
            if data.get('code') == 0 and data.get('data', {}).get('token'):
                masked_phone = self.mask_phone(phone)
                print(f"✅ {masked_phone} 登录成功")
                return data['data']['token']
            else:
                masked_phone = self.mask_phone(phone)
                error_msg = data.get('message', '未知错误')
                print(f"❌ {masked_phone} 登录失败: {error_msg}")
                self.push_messages.append(f"❌ {masked_phone} 登录失败: {error_msg}")
        except Exception as e:
            masked_phone = self.mask_phone(phone)
            error_msg = str(e)
            print(f"❌ {masked_phone} 登录异常: {error_msg}")
            self.push_messages.append(f"❌ {masked_phone} 登录异常: {error_msg}")
        
        return None

    def sign_check_in(self, account_info):
        """执行签到操作"""
        phone = account_info.get('phone', '')
        token = account_info.get('token')
        masked_phone = self.mask_phone(phone) if phone else "Token用户"
        
        # 如果没有token但有账号密码，则先登录
        if not token and 'phone' in account_info and 'pwd' in account_info:
            token = self.login(account_info['phone'], account_info['pwd'])
            if token:
                account_info['token'] = token
            else:
                return False
        
        if not token:
            print(f"❌ {masked_phone} 缺少有效token")
            self.push_messages.append(f"❌ {masked_phone} 缺少有效token")
            return False
        
        headers = {
            "Authorization": f"Bearer {token.replace('Bearer ', '')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/home/userWallet-receive",
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            if data.get('code') == 0:
                msg = f"🎉 {masked_phone} 签到成功: {data.get('message', '')}"
                print(msg)
                self.push_messages.append(msg)
                return True
            elif data.get('message', '').find('已领取') != -1:
                msg = f"⏳ {masked_phone} 本周已领取"
                print(msg)
                self.push_messages.append(msg)
                return True
            elif data.get('message') == '登录已过期' and 'phone' in account_info and 'pwd' in account_info:
                msg = f"🔄 {masked_phone} token过期，尝试重新登录"
                print(msg)
                self.push_messages.append(msg)
                new_token = self.login(account_info['phone'], account_info['pwd'])
                if new_token:
                    account_info['token'] = new_token
                    return self.sign_check_in(account_info)
            else:
                error_msg = data.get('message', '未知错误')
                msg = f"❌ {masked_phone} 签到失败: {error_msg}"
                print(msg)
                self.push_messages.append(msg)
        except Exception as e:
            error_msg = str(e)
            msg = f"❌ {masked_phone} 签到异常: {error_msg}"
            print(msg)
            self.push_messages.append(msg)
        
        return False

    def send_notification(self):
        """发送青龙通知"""
        if not self.push_messages:
            return
            
        duration = (datetime.now() - self.start_time).total_seconds()
        success_count = sum(1 for r in self.results if r)
        
        # 构建推送内容
        push_content = "\n".join(self.push_messages)
        push_content += f"\n\n💎 签到结果: {success_count}成功/{len(self.accounts)}总账号"
        push_content += f"\n⏱️ 执行耗时: {duration:.2f}秒"
        push_content += f"\n🕒 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 尝试发送通知（青龙面板环境）
        try:
            # 青龙面板通知功能
            from notify import send
            send(self.push_title, push_content)
            print("✅ 签到结果已推送")
        except ImportError:
            # 非青龙环境，打印到控制台
            print("\n" + "=" * 50)
            print(f"【{self.push_title}】")
            print(push_content)
            print("=" * 50)
        except Exception as e:
            print(f"❌ 推送失败: {str(e)}")

    def run(self):
        """主运行函数"""
        if not self.accounts:
            print("❌ 没有可用的账号信息")
            self.push_messages.append("❌ 没有可用的账号信息")
            self.send_notification()
            return
        
        print(f"\n{'='*40}")
        print(f"品赞代理签到开始 - {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*40}\n")
        
        for i, account in enumerate(self.accounts, 1):
            phone = account.get('phone', '')
            masked_phone = self.mask_phone(phone) if phone else "Token用户"
            print(f"\n🔍 处理账号 {i}/{len(self.accounts)}: {masked_phone}")
            result = self.sign_check_in(account)
            self.results.append(result)
            time.sleep(1)  # 请求间延迟
        
        success_count = sum(1 for r in self.results if r)
        print(f"\n{'='*40}")
        print(f"签到完成: 成功 {success_count}/{len(self.accounts)}")
        print(f"{'='*40}")
        
        # 添加汇总信息
        self.push_messages.insert(0, f"📊 品赞代理签到汇总")
        self.push_messages.insert(1, f"✅ 成功: {success_count}个")
        self.push_messages.insert(2, f"❌ 失败: {len(self.accounts) - success_count}个")
        self.push_messages.insert(3, "")
        
        # 发送通知
        self.send_notification()

if __name__ == "__main__":
    signer = IPZanSign()
    signer.run()

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
# -*- coding:utf-8 -*-
"""
小程序 众安健康 签到V1.6
本子只执行签到，任务是一次性的自己手动刷吧
变量名称：za_gpt （抓Access-Token）
格式: Token#备注，多账号用 & 或 换行 分割
定时参考：cron: 15 7 * * * 一天一次自行修改
za_balance.json是对账数据请勿删除，第一次运行提示收益总额都是0属于正常初始化数据。
"""
import requests, os, time

# --- 企业微信推送函数 ---
def send_qywx(title, content):
    qy_key = os.environ.get("QYWX_KEY")
    if not qy_key: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={qy_key}"
    try:
        requests.post(url, json={"msgtype": "text", "text": {"content": f"【{title}】\n{content}"}}, timeout=10)
    except: pass

# --- 核心逻辑：众安健康收割 ---
def run_za_lemon(name, token):
    print(f"\n{'='*10} 🚀 正在处理账号: {name} {'='*10}")
    headers = {
        "Access-Token": token.strip(),
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": "https://servicewechat.com/wxbac45cc1588a5a75/453/page-frame.html"
    }
    payload = {"channelCode":"c20195660470001","activityCode":"ONA20220411001"}
    report = [f"👤 账号: {name}"]

    try:
        # 1. 运行前资产扫描
        pre_res = requests.post("https://ihealth.zhongan.com/api/lemon/v1/common/activity/homePage", headers=headers, json=payload, timeout=10).json()
        start_score = pre_res.get("result", {}).get("sumAward", 0)
        start_yuan = start_score / 100.0
        print(f"📊 运行前余额: {start_yuan} 元")

        # 2. 执行签到
        print("📡 正在发送签到指令...")
        s_res = requests.post("https://ihealth.zhongan.com/api/lemon/v1/common/activity/signIn", headers=headers, json=payload, timeout=10).json()
        s_msg = s_res.get('message') or ('成功' if s_res.get('code')=='0' else '失败')
        print(f"📝 签到详情: {s_msg}")
        report.append(f"📝 签到状态: {s_msg}")

        # 3. 扫描红包并执行收割
        time.sleep(2)
        h_res = requests.post("https://ihealth.zhongan.com/api/lemon/v1/common/activity/homePage", headers=headers, json=payload, timeout=10).json()
        rewards = h_res.get("result", {}).get("valuableRewardList", [])
        
        if not rewards:
            print("💡 领取详情: 首页无红包可领")
            report.append("🎁 领取明细: 暂无待领奖励")
        else:
            for item in rewards:
                aid = item.get("awardDetailId")
                amt = item.get("amount", "0")
                lot_data = {
                    **payload, "id": aid, "envSource": "miniprogram", 
                    "infernalWallParams": {
                        "did": "d4ff8ff93a497607d16b594b6c594f999d5f6fe2:131:02138365152416cb33df12845d3e678b6046a12a",
                        "token": "2:12:1768616623921:fa339ec6a687#prd#support::81.n0yh0:5371:0003c0991b706f5da902183f2758aed42704fbd9:218",
                        "s": "fa339ec6a687#prd#support", "scene": "fa339ec6a687#prd#support"
                    }
                }
                r = requests.post("https://ihealth.zhongan.com/api/lemon/v1/common/activity/lottery", headers=headers, json=lot_data, timeout=10).json()
                status = "成功" if r.get('code')=='0' else f"失败({r.get('message')})"
                print(f"💰 领取动作: {amt}元 {status}")
                report.append(f"🎁 领取奖励: {amt}元 ({status})")

        # 4. 最终资产精算
        time.sleep(1)
        final_res = requests.post("https://ihealth.zhongan.com/api/lemon/v1/common/activity/homePage", headers=headers, json=payload, timeout=10).json()
        end_score = final_res.get("result", {}).get("sumAward", 0)
        end_yuan = end_score / 100.0
        gain_yuan = round(end_yuan - start_yuan, 2)
        
        report.append(f"💵 今日净赚: +{gain_yuan} 元")
        report.append(f"💰 累计总额: {end_yuan} 元")
        print(f"✅ 处理完毕: {start_yuan} -> {end_yuan}")

    except Exception as e:
        print(f"⚠️ 出错: {e}")
        report.append(f"⚠️ 异常: {str(e)}")
    
    return "\n".join(report)

# --- 标准结尾：Main 函数 ---
if __name__ == '__main__':
    # 获取环境变量
    token_str = os.environ.get("za_gpt")
    
    if not token_str:
        print("❌ 错误: 未发现环境变量 za_gpt")
    else:
        # 支持多种分隔符
        accounts = token_str.replace('&', '\n').split('\n')
        all_reports = []
        
        for acc in accounts:
            acc = acc.strip()
            if not acc: continue
            
            # 兼容 Token#备注 格式
            if '#' in acc:
                tk, name = acc.split('#', 1)
            elif '@' in acc:
                name, tk = acc.split('@', 1)
            else:
                tk, name = acc, "默认账号"
                
            # 执行并收集结果
            res_msg = run_za_lemon(name.strip(), tk.strip())
            all_reports.append(res_msg)
            time.sleep(2)
        
        # 发送汇总报告
        if all_reports:
            send_qywx("众安健康运行报告", "\n\n".join(all_reports))

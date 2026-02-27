# -*- coding: utf-8 -*-
"""
------------------------------------------------------------
小程序 布小派 V1
使用说明：
1. 青龙面板新建环境变量：
   - 变量名：bxp_gpt
   - 变量值：Authorization#备注 (例如：eyJhbGci...bJTf#备注)
   - 多账号：用 & 或 换行 分隔
   
2. 定时设置：
   - 建议：cron 0 9 * * * (每天早上9点运行)

3. 功能：
   - 自动签到、获取积分明细、查询总分、美化推送通知
------------------------------------------------------------
"""
import os, requests, json

# 变量获取
VAR_NAME = "bxp_gpt"
ENV_DATA = os.getenv(VAR_NAME)

# 推送功能载入
try:
    from notify import send
except ImportError:
    def send(title, content):
        print(f"\n📣 推送预览\n【{title}】\n{content}")

def main():
    if not ENV_DATA:
        print(f"❌ 错误: 未找到环境变量 {VAR_NAME}，请检查配置。")
        return

    # 处理多账号
    accounts = ENV_DATA.replace('&', '\n').splitlines()
    summary_list = []

    for acc in accounts:
        if "#" not in acc: continue
        # 拆分 Authorization 和 备注
        auth, name = acc.split("#")[0], acc.split("#")[1]
        
        headers = {
            "Host": "lm.api.sujh.net",
            "Appid": "buxiaopai",
            "Authorization": auth,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }
        
        print(f"\n--- 👤 正在处理账号: {name} ---")
        
        try:
            # 1. 自动签到
            sign_url = "https://lm.api.sujh.net/app/score/sign"
            payload = {
                "tmplIds": ["LvHPlhNTV3g-Do8X7NY-a1DZGpnhc_r6yy1FJqCCN-8"],
                "platform": 1
            }
            r_sign = requests.post(sign_url, headers=headers, json=payload).json()
            sign_msg = r_sign.get('msg', '未知')

            # 2. 查询总分
            total_score = "未知"
            user_url = "https://lm.api.sujh.net/app/user/index?platform=1"
            r_user = requests.get(user_url, headers=headers).json()
            if r_user.get('code') == 200:
                total_score = r_user.get('data', {}).get('score', '未知')

            # 3. 查询积分明细
            list_url = "https://lm.api.sujh.net/app/score/list?pageNum=1&platform=1"
            r_list = requests.get(list_url, headers=headers).json()
            detail_info = "无记录"
            if r_list.get('code') == 200 and r_list.get('rows'):
                detail_info = r_list['rows'][0].get('title2', '积分变动')
            
            # 4. 构建精简美化推送 (去掉绿色勾钩和星号)
            res_line = f"👤 账号: {name}\n   📝 签到: {sign_msg}\n   📈 明细: {detail_info}\n   💰 总分: {total_score}"
            print(res_line)
            summary_list.append(res_line)

        except Exception as e:
            err_line = f"⚠️ 账号: {name} 运行异常"
            print(f"{err_line}: {str(e)}")
            summary_list.append(err_line)

    # 发送最终报表
    if summary_list:
        send("🌾 布小派签到🙋‍♀️", "\n".join(summary_list))

if __name__ == "__main__":
    main()

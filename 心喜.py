# -*- coding: utf-8 -*-
# ------------------------------------------------------
# 小程序 心喜 V3.6
# 变量名：xx_gpt
# 格式：备注1@Sso1，多账号#分割
# cron: 16 8 * * * 定时自行修改
# [任务清单说明]
# 1. 每天必做 (全勤)：
#    - 自动签到
#    - 三连点赞 (社区动态)
#    - 会员权益浏览 (模拟点击)
#    - 积分商城浏览 (模拟点击)
#    - 自动随机评论 (一言内容，防复读)
# 2. 随机任务 (每周约4次)：
#    - 动态发帖 (58% 概率触发，内容取自一言)
# ------------------------------------------------------

import requests
import json, os, sys, time, random
from notify import send

msg = []

def pr(t):
    msg.append(str(t) + "\n")
    print(t)

def get_sign_flag(sso):
    url = "https://api.xinc818.com/mini/sign/info"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=header, timeout=10).json()
        return res.get("data", {}).get("flag", False)
    except:
        return False

def xy_qiandao(sso):
    url = "https://api.xinc818.com/mini/sign/in?dailyTaskId"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    try:
        requests.get(url, headers=header, timeout=10)
        pr("🎉 签到动作完成")
    except: pass

def xy_dzlist(sso):
    url = "https://api.xinc818.com/mini/community/home/posts?pageNum=1&pageSize=10&queryType=1&position=2"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    try:
        j = requests.get(url, headers=header, timeout=10).json()
        lst = j.get("data", {}).get("list", [])
        return [item["id"] for item in lst[:3]]
    except: return []

def xy_dz(sso):
    url = "https://api.xinc818.com/mini/posts/like"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    ids = xy_dzlist(sso)
    for pid in ids:
        requests.put(url, headers=header, json={"postsId": pid, "decision": True}, timeout=10)
        time.sleep(1)
    pr(f"👍 三连点赞完成")

def xy_sc_ll(sso):
    url = "https://api.xinc818.com/mini/dailyTask/browseGoods/22"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    requests.get(url, headers=header, timeout=10)
    pr("🛒 浏览商城完成")

def xy_vip(sso):
    url = "https://api.xinc818.com/mini/dailyTask/benefits/2"
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    requests.get(url, headers=header, timeout=10)
    pr("👑 会员权益浏览完成")

def xy_pinglun(sso):
    ids = xy_dzlist(sso)
    header = {"sso": sso, "user-agent": "Mozilla/5.0"}
    for pid in ids:
        try:
            txt = requests.get("https://v1.hitokoto.cn/?encode=text", timeout=5).text.strip()
            requests.post("https://api.xinc818.com/mini/postsComments", headers=header, json={"postsId": pid, "content": f"💬 {txt[:20]}"}, timeout=10)
            time.sleep(2)
        except: pass
    pr("💬 自动评论完成")

def xy_fatie(sso):
    try:
        text = requests.get("https://v1.hitokoto.cn/?encode=text", timeout=5).text.strip()
        url = "https://api.xinc818.com/mini/posts"
        header = {"sso": sso, "user-agent": "Mozilla/5.0"}
        data = {"topicNames": ["心情树洞"],"content": f"🌿 {text}","attachments": [],"voteType": 0,"commentType": "0","sid": int(time.time() * 1000)}
        requests.post(url, headers=header, json=data, timeout=10)
        pr("📝 随机动态发帖成功")
    except: pass

def index(remark, sso):
    try:
        pr(f"===== 执行账号：{remark} =====")
        header = {"sso": sso, "user-agent": "Mozilla/5.0"}
        user_url = "https://api.xinc818.com/mini/user"
        
        login_res = requests.get(user_url, headers=header, timeout=10).json()
        if login_res.get("code") != 0:
            pr("❌ Sso失效，请重新抓包")
            return
        
        start_pts = login_res["data"]["integral"]
        pr(f"💰 起始积分：{start_pts}")

        if not get_sign_flag(sso):
            xy_qiandao(sso)
            time.sleep(2)
        else:
            pr("📅 今日已签到")

        # 必做全勤任务
        xy_dz(sso)
        xy_vip(sso)
        xy_sc_ll(sso)
        xy_pinglun(sso)
        
        # 随机发帖 (每周约4次)
        if random.randint(1, 100) <= 58:
            xy_fatie(sso)
        else:
            pr("🎲 随机概率未触发发帖")

        # 统计分行显示
        final_res = requests.get(user_url, headers=header, timeout=10).json()
        end_pts = final_res["data"]["integral"]
        pr(f"💰 最终积分：{end_pts}")
        pr(f"📈 今日收益：+{end_pts - start_pts}")
        pr("🎉 任务全部运行完毕")

    except Exception as e:
        pr(f"❌ 运行错误: {str(e)}")

def main():
    env = os.environ.get("xx_gpt")
    if not env:
        print("未设置变量 xx_gpt")
        return

    accounts = [i for i in env.split("#") if i.strip()]
    for acc in accounts:
        if "@" in acc:
            remark, sso = acc.split("@", 1)
            index(remark.strip(), sso.strip())
            send(f"心喜日报-{remark}", "".join(msg))
            msg.clear()
            time.sleep(3)

if __name__ == "__main__":
    main()

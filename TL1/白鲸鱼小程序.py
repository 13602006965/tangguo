"""
白鲸回收-微信模式 (备注#username#auth) 脚本
APP和小程序本子分别单独跑
本项目支持双端签到，答题，盲盒抽奖，幸运抽奖，云宠物
切记小程序登录抓包即可不要绑定和APP同一个手机号
环境变量名: bjhs_wx
cron 30 7 * * * 定时自行修改
"""
import requests,json,re,os,sys,time,random,datetime,threading,execjs,hashlib,base64,urllib3,certifi
from urllib.parse import quote

# --- 推送兼容性代码 ---
# 尝试引入青龙面板的统一推送函数 send
try:
    if os.path.exists('sendNotify.py'):
        from sendNotify import send # 兼容旧版
    else:
        # 兼容新版或不同环境
        sys.path.append(os.path.abspath('.'))
        sys.path.append(os.path.abspath('..'))
        if os.path.exists('notify.py'):
            from notify import send
        else:
            def send(title, content):
                print(f"\n【推送】{title}\n{content}") # 如果引入失败，则打印到日志

except Exception as e:
    def send(title, content):
        print(f"\n【推送】{title}\n{content}")
    print(f"推送功能加载失败: {e}，将直接打印日志。")

# --- 配置区 ---
retrycount = 1
environ = "bjhs_wx" # 青龙面板环境变量名
name = "꧁༺ 白鲸༒回收-WX ༻꧂"
session = requests.session()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
messages = [] # 用于存储推送消息

#---------------------主代码区块---------------------
def getparm(parm):
    # Secret 在 run() 函数的 WX 模式中被设置
    sign = hashlib.md5((parm + Secret).encode('utf-8')).hexdigest()
    return parm + "&sign=" + sign

def run(arg1,arg2,arg3,arg4,arg5):
    global Secret
    # 微信模式密钥
    app = 'wx'
    appkey = '1f70a57fdf4061a7'
    Secret = 'eBRaFLkuJ5' # <-- 固定的微信 Secret
    apk = f"&appkey={appkey}"
    
    header = {
        "Host": "www.52bjy.com",
        "Connection": "keep-alive",
        "Content-Length": "",
        "Content-Type": "application/x-www-form-urlencoded",
        "EnvConnection": "test",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/32.363636)",
    }
    
    # 1. 使用抓取的 username 和 auth
    # arg1 是 username，arg2 是 auth
    auth = arg2 # <-- 直接使用 auth

    # 2. 任务执行循环 (后续逻辑保持不变)
    for retry in range(int(retrycount)):
            ctime = int(time.time())
        
            # 使用 try/except 块包裹所有任务，增强健壮性
            try:
                # 获取用户信息和 token
                userinfo_url = f'https://www.52bjy.com/api/app/user.php?' + getparm(f"action=userinfo&appkey={appkey}&auth={auth}&username={arg1}")
                userinfo_response = session.get(url=userinfo_url).json()
                
                # 检查 auth 是否有效
                if not userinfo_response.get("isSucess"):
                    messages.append(f"【{mark}】Auth已失效或网络错误")
                    print(f"❌Auth已失效或网络错误: {userinfo_response.get('message', '未知错误')}")
                    return

                token = userinfo_response['data']['token']            

                # 签到
                del header['Content-Length']
                urlsign = f'https://www.52bjy.com/api/app/user.php?action=qiandao&app={app}&auth={auth}&username={arg1}'
                responsesign = session.get(url=urlsign, headers=header).json()
                
                if "签到成功" in responsesign.get("message","") or "已经签到" in responsesign.get("message",""):
                    messages.append("☁️签到状态：成功")
                    print(f"☁️签到状态：成功")

                # 获取连签天数
                urlday = f"https://www.52bjy.com/api/app/user.php?action=getsigninfo&auth={auth}&username={arg1}"
                responseday = session.get(url=urlday, headers=header).json()
                thisturn = responseday['data']["thisturn"]
                messages.append(f"☁️本周连签：{thisturn} 天")
                print(f"☁️本周连签：{thisturn} 天")
                
                # 连签7天抽奖
                arg4 = f'https://www.52bjy.com/api/app/user.php?' + getparm(f"action=qiandaobox&app={app}{apk}&auth={auth}&merchant_id=1&username={arg1}")
                if thisturn == 7 and arg4:
                    responsebox = session.get(url=arg4, headers=header).json()
                    
                    if responsebox["isSucess"]:
                        if responsebox['data']['type'] == "money":
                            messages.append(f"🌈连签盲盒：{responsebox['data']['data']} 红包")
                            print(f"🌈连签盲盒：{responsebox['data']['data']} 红包")
                        elif responsebox['data']['type'] == "credit":
                            messages.append(f"☁️连签盲盒：+{responsebox['data']['data']} 鲸鱼币")
                            print(f"☁️连签盲盒：+{responsebox['data']['data']} 鲸鱼币")
                        else:
                            messages.append(f"☁️连签盲盒：{responsebox['data']}")
                            print(f"☁️连签盲盒：{responsebox['data']}")
                    else:
                        messages.append(f"☁️连签盲盒：{responsebox.get('message', '已领取')}")
                        print(f"☁️连签盲盒：{responsebox.get('message', '已领取')}")
                    
                    # 微信模式下没有额外的连签红包，跳过 APP 的红包逻辑

                print("☼ ――――  任  务  ―――― ☼")
                
                # 答题 (完整逻辑不变)
                dt_status = ""
                for i in range(7):
                    dt_response = session.get(url=f'https://www.52bjy.com/api/app/question.php?'+ getparm(f"action=list&appkey={appkey}&username={arg1}&version=1"), headers=header).json()
                    if dt_response['isSucess']:
                        dt_id = dt_response['data'][0]['id']
                        answer = 0
                        for index, value in enumerate(dt_response['data'][0]['answer']):
                            if value['isright'] == "1":
                                answer = index
                        #print(f"☁️第 {dt_response['data'][0]['index']} 题id: {dt_id}，答案：{answer}")
                        tj_response = session.get(url=f'https://www.52bjy.com/api/app/question.php?'+ getparm(f"action=addcount&answer={answer}&appkey={appkey}&id={dt_id}&merchant_id=1&username={arg1}&version=2"), headers=header).json()
                        if tj_response['isSucess']:
                            #print(f'☁️答对: {tj_response["data"]["right"]}，答错: {tj_response["data"]["wrong"]}')
                            dt_status = f'答对: {tj_response["data"]["right"]}，答错: {tj_response["data"]["wrong"]}'
                            time.sleep(random.randint(1, 2))
                        else:
                            print(f"⭕提交答案错误: {tj_response}")
                            break
                    else:
                        dt_status = dt_response['message']
                        print(f"☁️答题结束: {dt_response['message']}")
                        break
                messages.append(f"☁️答题状态：{dt_status}")


                print("☼ ――――  信  息  ―――― ☼")  
                
                # 今日获取
                now= datetime.datetime.now()
                urlinfo = f'https://www.52bjy.com/api/app/user.php?action=creditrecord&auth={auth}&month={now.month}&page=1&type=0&username={arg1}&year={now.year}'
                responseinfo = session.get(url=urlinfo, headers=header).json()
                amountall = 0
                for i in responseinfo["data"]:
                    amount = int(i["amount"])
                    if datetime.datetime.strptime(i["addtime"], "%Y-%m-%d %H:%M:%S").date() == now.date():
                        amountall = amountall + amount
                messages.append(f"☁️今日获：{amountall} 鲸鱼币")
                print(f"☁️今日获：{amountall} 鲸鱼币")
                
                # 余额信息
                urlinfo = f'https://www.52bjy.com/api/app/user.php?' + getparm(f"action=userinfo&appkey={appkey}&auth={auth}&username={arg1}")
                responseinfo = session.get(url=urlinfo, headers=header).json()
                messages.append(f"☁️鲸鱼币：{responseinfo['data']['credit']} 鲸鱼币")
                messages.append(f"☁️成长值：{responseinfo['data']['growths']} 成长值")
                print(f"☁️鲸鱼币：{responseinfo['data']['credit']} 鲸鱼币")
                print(f"☁️成长值：{responseinfo['data']['growths']} 成长值")

                print("☼ ――――  宠物  ―――― ☼")  
                
                # 云宠物 (完整逻辑不变)
                pet_status = ""
                for i in range(3):
                    responseym = session.get(url=f'https://www.52bjy.com/api/app/promotionanimal.php?' + getparm(f"action=adoptanimalshow&appkey={appkey}&username={arg1}"), headers=header).json()
                    if responseym['data'].get("exist_pet") > 0:
                        pet_status += f"等级：{responseym['data']['level']} 级 | "
                        # 执行互动任务 (喂养, 喝水, 铲屎)
                        ywtype = {1:"喂养",2:"喝水",3:"铲屎"}
                        for key, value in ywtype.items():
                            responseym_interact = session.get(url=f'https://www.52bjy.com/api/app/promotionanimal.php?' + getparm(f"action=adoptinteract&appkey={appkey}&type={key}&username={arg1}"), headers=header).json()
                            if responseym_interact["isSucess"]:
                                pet_status += f"{value}：完成 | "
                            else:
                                pet_status += f"{value}：{responseym_interact['message'][:4]}... | "
                            time.sleep(1)
                        break
                    else:
                        pet_status += "未领养 | "
                        # 尝试领养
                        responseym_adopt = session.get(url=f'https://www.52bjy.com/api/app/promotionanimal.php?' + getparm(f"action=adoptanimal&appkey={appkey}&type=2&username={arg1}"), headers=header).json()
                        pet_status += f"领养状态：{responseym_adopt.get('message', '失败')}"
                        break
                messages.append(f"☁️宠物状态：{pet_status.strip('| ')}")
                print(f"☁️宠物状态：{pet_status.strip('| ')}")

                print("☼ ――――  幸  运  ―――― ☼")  
                
                # 幸运抽奖 (完整逻辑不变)
                cj_count = 0
                for i in range(5):
                    responsecj = session.get(url=f'https://www.52bjy.com/api/app/promotionjgg.php?' + getparm(f"action=prize_draw&app={app}&appkey={appkey}&merchant_id=1&username={arg1}"), headers=header).json()
                    if responsecj["isSucess"]:
                        coupon_id = responsecj['data']['coupon_id']
                        introduce = responsecj['data']['introduce']
                        responsecjlq = session.get(url=f'https://www.52bjy.com/api/app/promotioncoupon.php?' + getparm(f"action=get&appkey={appkey}&cid={introduce}&did={coupon_id}&type=promotion_coupun&username={arg1}"), headers=header).json()
                        if "成功" in responsecjlq["message"] or "已" in responsecjlq["message"]:
                            #print(f"☁️抽奖：{responsecj['data']['title']}")
                            cj_count += 1
                            time.sleep(2)
                    elif "已用完" in responsecj["message"]:
                        #print(f"☁️抽奖：次数用完")
                        break
                    else:
                        print(f"☁️{responsecj}")
                        break
                messages.append(f"☁️抽奖结果：抽奖 {cj_count} 次")
                print(f"☁️抽奖结果：抽奖 {cj_count} 次")


                break # 任务成功，跳出重试循环
            
            except Exception as e:
                # 任务执行中途失败，尝试重试
                messages.append(f"【{mark}】任务执行异常: {e}")
                print(f"❌任务执行异常: {e}")
                if retry >= int(retrycount)-1:
                    break # 达到最大重试次数，退出

def main():
    global id, messages, mark # 声明 mark 为 global，以便在 run 中捕获异常时使用
    if os.environ.get(environ):
        ck = os.environ.get(environ)
    else:
        ck = ""
        if ck == "":
            print(f"⭕请设置环境变量：{environ}")
            send(f"{name}执行失败", f"请设置环境变量：{environ}")
            sys.exit()
            
    ck_run = ck.split('\n')
    ck_run = [item for item in ck_run if item]
    all_messages = [f"{' ' * 7}{name}\n"]
    print(f"{' ' * 7}{name}\n\n")
    print(f"-------- ☁️ 开 始  执 行 ☁️ --------")
    
    for i, ck_run_n in enumerate(ck_run):
        # 初始化变量，防止 UnboundLocalError
        mark = f"格式异常-{i+1}" 
        acc = None
        paw = None
        
        parts = ck_run_n.split('#')
        # 仅处理 3 个字段：备注#username#auth
        if len(parts) == 3:
            mark, acc, paw = parts
            ques = "" 
            qdbox = ""
            qdhb = ""
        else:
            print(f"⭕当前账号：{mark} - 格式错误，微信模式应为：备注#username#auth，跳过！")
            continue
            
        print(f"\n>>>>>  账号 [{i + 1}/{len(ck_run)}]")
        print(f"☁️当前账号：{mark}")
        
        # 运行任务
        messages.clear()
        messages.append(f"\n【账号 {i+1}：{mark}】")
        if acc and paw:
            run(acc,paw,ques,qdbox,qdhb)
        else:
            messages.append(f"⭕账号 {mark} 解析失败，跳过运行。")

        # 收集当前账号的推送消息
        all_messages.extend(messages)
        
        time.sleep(random.randint(1, 2))
        
    print(f"\n\n-------- ☁️ 执 行  结 束 ☁️ --------\n\n")
    send(f"{name}执行结果", "\n".join(all_messages)) # 使用 send 函数推送所有账号结果

if __name__ == '__main__':
    main()

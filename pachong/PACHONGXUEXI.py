import requests

# url = 'https://www.baidu.com/' # 百度首页
# requests=requests.get(url)
# print(requests.text) # 输出网页内容
# print(len(requests.content.decode()))# 输出网页内容,解码方式为utf-8

# 使用requests保存图片

# URL ='https://ts1.tc.mm.bing.net/th/id/R-C.987f582c510be58755c4933cda68d525?rik=C0D21hJDYvXosw&riu=http%3a%2f%2fimg.pconline.com.cn%2fimages%2fupload%2fupc%2ftx%2fwallpaper%2f1305%2f16%2fc4%2f20990657_1368686545122.jpg&ehk=netN2qzcCVS4ALUQfDOwxAwFcy41oxC%2b0xTFvOYy5ds%3d&risl=&pid=ImgRaw&r=0'
# res = requests.get(URL)
# with open('1.jpg','wb') as f:
#     f.write(res.content)
# requests.text requests.content # text返回的是字符串形式，content返回的是二进制形式

# url = 'https://www.baidu.com/' # 百度首页
# headers={
#     'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
# } # 模拟浏览器请求 字典
# requests=requests.get(url, headers=headers)
# # print(requests.text) # 输出网页内容
# print(len(requests.content.decode())) # 输出网页内容,解码方式为utf-8

# 2.user-agent池，防止反爬
# 第一种方法：自己找
# import random
# user_agent_list = [
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
#     'Mozilla/5.0 (Windows NT 10.0; Win64; x4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
# ]
# print(random.choice(user_agent_list)) # 随机选择一个user-agent

# 第二种方法：fake_useragent库
# from fake_useragent import UserAgent
# print(UserAgent().random) # 随机选择一个user-agent``

# 3.url 传参
# from urllib.parse import quote,unquote
# quote() 对中文进行编码
# unquote() 对编码进行解码
# print(quote('你好')) # %E4%BD%A0%E5%A5%BD
# print(unquote('%E4%BD%A0%E5%A5%BD')) # 你好

# 通过params携带参数字典
# url = 'https://www.baidu.com/s'
# kw = input('请输入搜索内容：')
# params = {'wd':kw}
# headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/}
# res = requests.get(url,params=params,headers=headers)
# print(res.url) # 输出完整url

# url = 'https://tieba.baidu.com/f?'
# headers={
#     'user-agent':'MMozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
# }
# word= input('请输入贴吧名称：')
# page = int(input('请输入页码：'))
# for i in range(page):
#     params = {
#         'kw':word,
#         'pn':i*50
#     }
#     res = requests.get(url,params=params,headers=headers)
#     with open(f'{word}-{i+1}.html','w',encoding='utf-8') as f:
#         f.write(res.text)



# 4.爬取贴吧，防止反爬
# import time
# url = 'https://tieba.baidu.com/f?'
# headers = {
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0',
#     'cookie': 'BAIDUID_BFESS=8B4DE33732FA594A1EE7B97F1B20B176:FG=1; __bid_n=198cba6d2623728f97c23f; BIDUPSID=8B4DE33732FA594A1EE7B97F1B20B176; PSTM=1756114639; H_PS_PSSID=63140_63325_63948_64561_64643_64701_64893_64841_64909_64924_64953_64942_64978_65046_65076_65084_65123_65141_65138_65139_65189_65204_65167_65226_65247_65262_65254_65144; PSINO=3; delPer=0; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; H_WISE_SIDS=63140_63325_63948_64561_64643_64701_64893_64841_64909_64924_64953_64942_64978_65046_65076_65084_65123_65141_65138_65139_65189_65204_65167_65226_65247_65262_65254_65144; BCLID=8467589992226451912; BCLID_BFESS=8467589992226451912; BDSFRCVID=zk-OJeC62riIKUJsvABRJg8mJKDEp4OTH6aojeFnV2NTJJg_5LzjEG0P9M8g0K4-S2-HogKKLgOTHULF_2uxOjjg8UtVJeC6EG0Ptf8g0f5; BDSFRCVID_BFESS=zk-OJeC62riIKUJsvABRJg8mJKDEp4OTH6aojeFnV2NTJJg_5LzjEG0P9M8g0K4-S2-HogKKLgOTHULF_2uxOjjg8UtVJeC6EG0Ptf8g0f5; H_BDCLCKID_SF=tRAOoC--tIvqKRopMtOhq4tehHREaKr9WDTm_Do-2lTvSqcR5xQI0xIseMcZBM34-nn9-pPKKR78eqQk365F3MIpbnPtWnTB3mkjbITzfn02OI-z0TKVy-4syPRrKMRnWNTrKfA-b4ncjRcTehoM3xI8LNj405OTbIFO0KJDJCcjqR8ZD6DBjjjP; H_BDCLCKID_SF_BFESS=tRAOoC--tIvqKRopMtOhq4tehHREaKr9WDTm_Do-2lTvSqcR5xQI0xIseMcZBM34-nn9-pPKKR78eqQk365F3MIpbnPtWnTB3mkjbITzfn02OI-z0TKVy-4syPRrKMRnWNTrKfA-b4ncjRcTehoM3xI8LNj405OTbIFO0KJDJCcjqR8ZD6DBjjjP; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1757841893; HMACCOUNT=9691ADE6F8B7F116; BAIDU_WISE_UID=wapp_1757841893339_583; USER_JUMP=-1; st_key_id=17; arialoadData=false; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGl3ixVdpjxtMIx1uoaGiQnXGEimjy3MrXEpSuItnI4KDzM0udPS9FXOSlnZDFq4odTgwNSQKKIDdXA6eDfuiw2FU7J7xedw9YiDB8v1LZSlzAfjfhzGIkWylUjp0qrpiQvGgLbz7OSojK1zRbqBESR5Pdk2R9IA3lxxOVzA+Iw1TWLSgWjlFVG9Xmh1+20oPSbrzvDjYtVPmZ+9/6evcXmhcO1Y58MgLozKnaQIaLfWRIXZy/8llaWZittcIfh39p/xUSUZS0ReZYJMPG6nCsxNJlhI2UyeJA6QroZFMelR7tnTNS/pLMWceus0e757/UPzWCk2doxxowOinC9vxVcqAAv3LCf1Y7/fHL3PTSf9vid/u2VLX4h1nBtx8EF07eCMhWVv+2qjbPV7ZhXk3reaWRFEeso3s/Kc9n/UXtUfNU1sHiCdbrCW5yYsuSM9SPGDZsl7FhTAKw7qIu38vFZiq+DRc8Vbf7jOiN9xPe0lOdZHUhGHZ82rL5jTCsILwcRVCndrarbwmu7G154MpYiKmTXZkqV7Alo4QZzicdyMbWvwvmR2/m//YVTM8qeZWgDSHjDmtehgLWM45zARbPujeqU0T92Gmgs89l2htrSKIbmRn70TptpwRdVKCM+bVyBUb9OIRwTeyCAWS0fZrc1gRPDIkYns/t116LOWZXT+ZJdImdyxYIjA1uSy2hfTFv/d3cnXH4nh+maaicAPllDg7JjsxZAfQoVAycJHizlQ5d34k8SzMID0x3kxnXwHfxXvz6DS3RnKydYTBUIWPYKJvmIpFg/34wKycfRQ7ypzzglRzl9ZokDxrmKvekLmyAprGRChHnhPuJeIKACPXiVuli9ItRLEkdb1mLxNHAk3uJy88YX/Rf/sKUjR12zxRTDxxJNDJS+Dlsbqu3n4I65ujli/3rQ8Zk1MjmTOsz9+kTqOM4upsnQ6IWq/zeZTItMCgHpQhuhr4ip73honuzoJhfJJqPUSX01viD97GXfw7kf+R6as3JPAEXsdOdDsWEAgJn+ZMVrELI7pXz8Jko9Xv3uSDHo/C3kmFLrauvEYpUg3FbqEqM6JmRHqkwRhSJQtmfffhEiJHXdZXgTikpxSzRszeYvFyXCPSuJ5oyoOgoCPKXE8fX73WOZ0mAlF1mc=; BDUSS=UJ5Skc3OEVKU3NyR0p5NEJPenJhNUlGcVl3bzRrZDUzfnhxMDNkNDhQQWJGLTVvSVFBQUFBJCQAAAAAAAAAAAEAAADbj7dF0PGw1LDUeGJiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABuKxmgbisZoZ; BDUSS_BFESS=UJ5Skc3OEVKU3NyR0p5NEJPenJhNUlGcVl3bzRrZDUzfnhxMDNkNDhQQWJGLTVvSVFBQUFBJCQAAAAAAAAAAAEAAADbj7dF0PGw1LDUeGJiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABuKxmgbisZoZ; STOKEN=c331fad005e891ccd3bfde737f7ec8314bcef5288d41e24e40908e8bb3b5c1ed; 1169657819_FRSVideoUploadTip=1; video_bubble1169657819=1; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1757842147; XFI=43f7ada0-914d-11f0-bed2-9b5e767723eb; BA_HECTOR=00848g2k25ak2hah8l0h000g20ak861kcd2n525; ariaappid=c890648bf4dd00d05eb9751dd0548c30; ariauseGraymode=false; ZFY=Zgp0vTgh163PO8jS98Qie1lZPOcooK9sjY8o1f7ax:B8:C; XFCS=BE1ECAE22FC7B86655CB157465B4013D4C051BFFE77464B3DAB06198859D333B; XFT=O6iY98trcFfv4eTzI55DTI2SL59nvAqrHbUysLx7Tgo=; ab_sr=1.0.1_N2NlOTMzNjY1MmE4MWUwOGYwZGU2NGFlZjQ4NDQwMGZlNGI5NWI5MGRhZmVjNDAyZDgzYjExYjFiNzhiN2FlMjYyYzIwYzgzMzBhMDhiZjlmNDE0NWYyNTVmZmFmNzliMDZhZTVhNWJmNjIwMTllMjc0YTNkZWE2OTQ0NWZiNWEzYmY0YzAxMTQ5NGEyY2ZmNDljNjBjYzg1MGJkMWNjZmM1MTlmMjRmZTk1NjRhNWIzYzE2NWU2MzFhYmY1M2Yz; st_data=268c378fc3fd8b0e05de841a378a2743104c219954fca1d9be3b30b38e719ae9c35ff6926ec33cf596246fff8a8b058c2736c085c7f85616c0486f4883e76d57c6cd48b16378347eef0e875e7797775ea954292e2b9c437631c7fca1720a3815440aede7a91c239f062e99b217c85a8967f2519f7aa556e6b9229d4e2d0d20c0e24c369aa993fc32d3799d560b8039cf; st_sign=f7267cea'  # 可选，建议加上
# }
# word = input('请输入贴吧名称：')
# page = int(input('请输入页码：'))
# for i in range(page):
#     params = {
#         'kw': word,
#         'pn': i * 50
#     }
#     res = requests.get(url, params=params, headers=headers)
#     with open(f'{word}-{i+1}.html', 'w', encoding='utf-8') as f:
#         f.write(res.text)
#     time.sleep(1)  # 增加延时，降低被封风险

# 6.改写为面向对象
# 7.post请求
# 8.session 保持会话
# 9.cookies池
# 10.代理
# url = 'https://www.baidu.com/' # 百度首页
# headers = {
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0',
# }
# proxies = {
#     'http': 'http://12.34.56.79:9527'}
# res = requests.get(url, headers=headers, proxies=proxies)
# print(res.content.decode())
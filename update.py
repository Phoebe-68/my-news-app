import requests
import json
import datetime
import os
import re

def main():
    # 1. 填入 GitHub 官方正规合法的全称网址
    url = "https://azure.com"
    token = os.environ.get('GH_TOKEN', '').strip()
    
    if not token:
        print("❌ 错误：后台未找到名为 GH_TOKEN 的密钥，请检查仓库 Secrets 配置！")
        return
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    today = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    date_str = today.strftime("%Y年%m月%d日")
    
    prompt = f"""
    今天是 {date_str}。请结合全球、亚太以及财经科技的最新真实动态，生成今日新闻。
    每条新闻必须是一句事实，紧接着在括号内加上一句通俗背景解释。
    必须严格按照以下 JSON 格式输出，不要包含任何 markdown 标记（如 ```json 等）：
    {{
      "global": [ "全球新闻1(背景解释)", "全球新闻2(背景解释)" ],
      "asia": [ "亚太新闻1(背景解释)" ],
      "tech_finance": [ "科技财经新闻1(背景解释)" ]
    }}
    数量严格要求：global 必须凑足 20 条，asia 必须 10 条，tech_finance 必须 10 条。
    """

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    print("📡 正在向 AI 发起新闻生成请求...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ AI 接口请求失败，状态码: {response.status_code}, 返回内容: {response.text}")
        return
        
    ai_data = response.json()['choices']['message']['content'].strip()
    
    # 剥离可能存在的 markdown 外壳
    ai_data = re.sub(r'^```[a-zA-Z]*\s*', '', ai_data)
    ai_data = re.sub(r'\s*```$', '', ai_data)
    ai_data = ai_data.strip()

    try:
        news_json = json.loads(ai_data)
        print("✅ AI 返回数据成功通过 JSON 安全解析验证！")
    except Exception as e:
        print("❌ JSON 解析失败，AI 返回的原始文本为：", ai_data)
        raise e

    # 2. 读取并精准重写 index.html 网页文件
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 精准替换页面中的日期标题
    html = re.sub(r'id="current-date"[^>]*>.*?<\/p>', f'id="current-date" class="text-xs text-slate-400 font-medium mt-0.5">{date_str}</p>', html)
    
    # 精准定位并替换 JavaScript 里的 newsData 对象
    new_js_block = f"""const newsData = {{
        global: {json.dumps(news_json['global'], ensure_ascii=False, indent=16)},
        asia: {json.dumps(news_json['asia'], ensure_ascii=False, indent=16)},
        'tech-finance': {json.dumps(news_json['tech_finance'], ensure_ascii=False, indent=16)}
    }};"""
    
    html = re.sub(r'const newsData = \{.*?\};', new_js_block, html, flags=re.DOTALL)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("🎉 网页 index.html 数据注入成功！")

if __name__ == "__main__":
    main()

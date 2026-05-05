import feedparser
import requests
import os
import google.generativeai as genai
from datetime import datetime

# 配置参数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "pushed_links.txt"

# 初始化 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_ai_summary(title, raw_content):
    """调用 Gemini 进行翻译、分类和摘要"""
    prompt = f"""
    你是一个资深的曼联足球专栏作家。请处理以下新闻：
    标题：{title}
    内容摘要：{raw_content}

    任务要求：
    1. 判定类别：【比赛战报】、【转会动态】、【伤病更新】或【其他动态】。
    2. 翻译并总结：用专业且富有激情的中文简述核心事实，不超过80字。
    3. 格式：[类别] 摘要内容。
    4. 过滤：如果内容与曼联一线队完全无关，请只回复“IGNORE”。
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return f"新闻快讯：{title}（摘要生成失败）"

def process():
    # 确保数据库文件存在
    if not os.path.exists(DB_FILE):
        open(DB_FILE, 'w').close()

    with open(DB_FILE, 'r') as f:
        pushed_links = set(f.read().splitlines())

    # 抓取源（可以添加更多源）
    feeds = ["https://feeds.bbci.co.uk/sport/football/teams/manchester-united/rss.xml"]
    
    new_entries = []
    current_pushed = []

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]: # 每次检查最新的10条
            if entry.link not in pushed_links:
                summary = get_ai_summary(entry.title, entry.summary)
                
                if "IGNORE" not in summary:
                    new_entries.append(f"🔴 **​{summary}​**\n🔗 [原文链接]({entry.link})")
                    current_pushed.append(entry.link)

    if new_entries:
        # 推送到 Telegram
        full_message = "\n\n".join(new_entries)
        send_to_telegram(f"🕒 **曼联实时情报 ({datetime.now().strftime('%H:%M')})​**\n\n" + full_message)
        
        # 更新本地数据库
        with open(DB_FILE, 'a') as f:
            for link in current_pushed:
                f.write(link + "\n")
        return True # 表示有更新
    return False

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    has_update = process()
    # 打印结果供 GitHub Action 判断是否需要 Commit
    print(f"HAS_UPDATE={has_update}")

import feedparser
import requests
import time
from datetime import datetime, timedelta

# 配置参数（建议通过环境变量读取）
TELEGRAM_TOKEN = "8711686375:AAFyjRORcT-xcEe9ps39g8pzBBW4ne4pgb8"
CHAT_ID = "7571469813"
# 示例 RSS 源：BBC 曼联频道
RSS_URLS = [
    "https://feeds.bbci.co.uk/sport/football/teams/manchester-united/rss.xml",
    "https://www.manchestereveningnews.co.uk/sport/football/?service=rss",
    "https://rsshub.app/hupu/bbs/manutd/1",
    
]

def get_mufc_news():
    news_list = []
    now = datetime.now()
    # 筛选过去 24 小时的新闻
    day_ago = now - timedelta(days=1)

    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # 解析发布时间
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if published_time > day_ago:
                news_list.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary
                })
    return news_list

def format_message(news_items):
    if not news_items:
        return "🔴 今日暂无重磅曼联新闻更新。"
    
    # 按照你要求的【结构化日报】格式组织
    message = "🔴 **曼联早报 (MUFC Daily)​**\n"
    message += f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # 这里可以根据关键词做简单的自动分类逻辑
    message += "【最新动态】\n"
    for item in news_items:
        message += f"• {item['title']}\n🔗 [阅读原文]({item['link']})\n\n"
    
    return message

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    news = get_mufc_news()
    formatted_text = format_message(news)
    send_to_telegram(formatted_text)

import feedparser
import requests
import os
import google.generativeai as genai
from datetime import datetime

# ================= 配置区 =================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "pushed_links.txt"
PROMPT_FILE = os.path.join("agents", "agent_prompt.md")

# 初始化 Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("错误: 未找到 GEMINI_API_KEY 环境变量")

def load_prompt():
    """从独立文件读取 Prompt 模板"""
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return "请作为曼联编辑总结以下新闻：{news_batch}"

def mufc_editor_agent(news_batch):
    """Agent 核心逻辑"""
    if not news_batch:
        return None

    template = load_prompt()
    current_date = datetime.now().strftime('%Y年%m月%d日')
    
    # 使用 replace 注入变量，避免 format 带来的大括号转义问题
    full_prompt = template.replace("{current_date}", current_date)
    
    if "{news_batch}" in full_prompt:
        full_prompt = full_prompt.replace("{news_batch}", news_batch)
    else:
        full_prompt += f"\n\n待处理数据内容：\n{news_batch}"

    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Agent 运行异常: {e}")
        return None

def send_to_telegram(text):
    """发送消息到 Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"发送 Telegram 失败: {e}")

def run_workflow():
    """主工作流"""
    # 1. 确保数据库文件存在
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write("")

    # 2. 读取已推送链接
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        pushed_links = set(line.strip() for line in f if line.strip())

    # 3. 抓取新闻源
    rss_sources = [
        "https://feeds.bbci.co.uk/sport/football/teams/manchester-united/rss.xml",
        "https://www.skysports.com/rss/11667"
    ]
    
    collected_data = []
    new_links = []

    for url in rss_sources:
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            if entry.link not in pushed_links:
                # 清洗摘要中的 HTML 标签
                clean_summary = entry.summary.split('<')[0] if '<' in entry.summary else entry.summary
                info = f"标题: {entry.title}\n摘要: {clean_summary}\n链接: {entry.link}"
                collected_data.append(info)
                new_links.append(entry.link)

    # 4. 如果有新内容，交给 Agent 处理并发送
    if collected_data:
        print(f"发现 {len(collected_data)} 条新动态，正在调用 Agent...")
        batch_text = "\n---\n".join(collected_data)
        report = mufc_editor_agent(batch_text)
        
        if report:
            send_to_telegram(report)
            # 5. 更新本地数据库
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                for link in new_links:
                    f.write(link + "\n")
            print("任务完成：已推送并更新数据库。")
            return True
    else:
        print("今日暂无新动态。")
    return False

if __name__ == "__main__":
    run_workflow()

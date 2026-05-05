import feedparser
import requests
import os
from google import genai  # 修改这一行
from datetime import datetime
from dotenv import load_dotenv # 需要先 pip install python-dot

load_dotenv()

# ================= 配置区 =================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DB_FILE = "pushed_links.txt"
# 确保路径与你的目录结构一致
PROMPT_FILE = os.path.join("agents", "agent_prompt.md")

# 初始化新版 Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

def load_prompt():
    """从独立文件读取 Prompt 模板"""
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取 Prompt 文件失败: {e}")
    return "请作为曼联编辑总结以下新闻：{news_batch}"

def mufc_editor_agent(news_batch):
    """新版 Agent 核心逻辑"""
    if not news_batch:
        return None

    template = load_prompt()
    current_date = datetime.now().strftime('%Y年%m月%d日')
    
    # 注入变量
    full_prompt = template.replace("{current_date}", current_date)
    if "{news_batch}" in full_prompt:
        full_prompt = full_prompt.replace("{news_batch}", news_batch)
    else:
        full_prompt += f"\n\n待处理新闻数据：\n{news_batch}"

    try:
        # 使用新版 SDK 调用方法
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Agent 运行异常: {e}")
        return None

def send_to_telegram(text):    
    #发送消息到 Telegram (使用 HTML 模式以提高兼容性)    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"        
    
    # 将 Markdown 的加粗 ** 简单替换为 HTML 的 <b>，提高容错率    
    # # 如果你的 Agent 输出包含很多 Markdown 语法，这一步可以确保基础样式保留    
    html_text = text.replace("**​", "<b>").replace("​**", "</b>")         
    
    payload = {        
        "chat_id": CHAT_ID,        
        "text": text,  # 如果 AI 输出的是标准 Markdown，我们尝试先用 MarkdownV2 或 HTML        
        "parse_mode": "HTML", # 切换为 HTML 模式        
        "disable_web_page_preview": False    
    }        
    try:        # 第一次尝试：HTML 模式        
        res = requests.post(url, json=payload)        
        if res.status_code != 200:            # 如果 HTML 失败（可能是因为内容里有 < 或 >），则退回到纯文本模式发送，确保信息不丢失            
            print(f"HTML 模式发送失败 ({res.status_code})，尝试纯文本模式...")            
            payload.pop("parse_mode")            
            res = requests.post(url, json=payload)                
            
        res.raise_for_status()        
        print("Telegram 消息发送成功！")    
    except Exception as e:        
        print(f"发送 Telegram 最终失败: {e}")


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
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                if entry.link not in pushed_links:
                    # 基础内容清洗
                    clean_summary = entry.summary.split('<')[0] if '<' in entry.summary else entry.summary
                    info = f"标题: {entry.title}\n摘要: {clean_summary}\n链接: {entry.link}"
                    collected_data.append(info)
                    new_links.append(entry.link)
        except Exception as e:
            print(f"抓取源 {url} 失败: {e}")

    # 4. 如果有新内容，交给 Agent 处理
    if collected_data:
        print(f"发现 {len(collected_data)} 条新动态，正在调用新版 Agent...")
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

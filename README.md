# MUFC Intel Agent (曼联情报站)

这是一个基于 **Gemini 2.0 Agent** 驱动的自动化情报系统。它每天定时抓取全球权威媒体的曼联新闻，通过 AI 进行去重、翻译和结构化编排，最终推送到你的 Telegram 频道。

### **核心功能**
*   **AI 智能编辑**：使用 `gemini-2.0-flash` 模型，自动识别并分类【转会动态】、【比赛战报】和【伤病更新】。
*   **精准去重**：建立本地链接数据库，确保同一条新闻在不同源之间绝不重复推送。
*   **HTML 优雅排版**：完美适配 Telegram HTML 模式，支持加粗标题、列表和超链接预览。
*   **北美时区适配**：定时任务严格设定在北美东部时间 (EST/EDT) 早上 6:00 运行。

---

### **项目结构**
```text
├── .github/workflows/
│   └── agent_service.yml    # GitHub Actions 自动化配置 (Node.js 24 + Python 3.11)
├── agent/
│   └── agent_prompt.md      # Agent 核心指令手册 (HTML 模版，独立维护)
├── mufc_agent.py            # 主程序逻辑 (基于最新 google-genai SDK)
├── pushed_links.txt         # 去重数据库 (由脚本自动生成与更新)
└── .env                     # 本地环境变量 (私密文件，不进入 Git 仓库)

### **快速开始**
#### **1. 环境准备**

Python: 建议版本 3.11 或更高。
API Keys:

Gemini API: 在 Google AI Studio 获取。
Telegram Bot: 通过 @BotFather 创建机器人并获取 Token。
Chat ID: 通过 @userinfobot 获取你的个人 ID。



#### **2. 本地运行与调试**
安装依赖库：
bashCopypip install feedparser requests google-genai python-dotenv

在根目录创建 .env 文件并配置变量：
📝Write📋复制📝插入GEMINI_API_KEY=你的_API_KEY
TELEGRAM_TOKEN=你的_BOT_TOKEN
CHAT_ID=你的_CHAT_ID

执行脚本：
bashCopypython mufc_agent.py

#### **3. 云端部署 (GitHub Actions)​**

将项目推送到你的 GitHub 私有仓库。
在仓库的 Settings > Secrets and variables > Actions 中添加上述三个加密变量。
系统将根据 agent_service.yml 的 Cron 设定，在 UTC 10:00 (对应北美东部夏令时 EDT 06:00)​ 自动触发。


### **维护与进阶**

修改排版风格：只需编辑 agent/agent_prompt.md，即可改变 AI 的语气、分类逻辑或视觉格式，无需改动 Python 代码。
增加新闻源：在 mufc_agent.py 的 rss_sources 列表中添加新的 RSS 链接（如 BBC, Sky Sports 等）。
时区切换：

夏令时 (EDT)​: Cron 设为 0 10 * * *。
冬令时 (EST)​: Cron 设为 0 11 * * *。


Current Status:​ 🟢 Stable (As of May 2026)
Author:​ Tabbit Agent & MUFC Fan
Glory Glory Man United!​
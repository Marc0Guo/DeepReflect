# Vibe Roast · AI 聊天记录 Roast

## 第一次必问（不要默认扫盘）

Skill 触发后，agent **应先问用户**数据来源，**不要**一上来就跑 `extract_*`：

| 选项 | 含义 | 价格 |
|------|------|------|
| **1** | **当前对话 / agent 记忆** — 用 Cursor/Claude 上下文 | 💰|
| **2** | **Cursor** — `extract_cursor.py` |💰💰💰|
| **3** | **Claude Code** — `extract_claude.py` |💰💰💰|


```bash
# 仅当用户选了 2 或 3 之后会跑
python3 skills/chat-history-roast/scripts/extract_cursor.py --limit 50
python3 skills/chat-history-roast/scripts/extract_claude.py --limit 30
```

`--limit` 建议 **20–80**。不要默认双 extract + 全库扫描，会很贵。

## 样本

- [中文](./examples/sample/roast-report.zh.html)
- [English](./examples/sample/roast-report.en.html)

## 安装

在**任意项目根目录**（有 `.git` 或 `.cursor`）：

```bash
npm install deepreflect-chat-history-roast-skill
```

`postinstall` 会自动安装到 `.cursor/skills/chat-history-roast/`。

```bash
npx chat-history-roast-skill install
```

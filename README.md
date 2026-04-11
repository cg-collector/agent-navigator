# 🤖 AI Agent Navigator

AI Agent 智能导航站 — 260+ 份 AI Agent 研究报告的可视化浏览平台

## 📊 数据概览

| 分类 | 数量 |
|------|------|
| 多智能体 (Multi-Agent) | 78 |
| 运行时框架 (Runtime) | 49 |
| 工具链 (Toolchain) | 41 |
| 编码框架 (Coding Framework) | 36 |
| 其他 (Other) | 22 |
| GUI-Agent | 14 |
| 浏览器代理 (Browser Agent) | 11 |
| 评测基准 (Benchmark) | 10 |
| **总计** | **261** |

## ✨ 功能

- 🔍 **实时搜索** — 标题/摘要/标签模糊匹配，300ms 防抖
- 🏷️ **分类筛选** — 8 大分类，一键过滤
- 📊 **多维度排序** — 按评分 / Stars / ID 排序
- 📄 **详情面板** — 右侧滑出，Markdown 渲染完整报告
- 🔗 **标签联动** — 点击卡片标签自动筛选
- ⌨️ **快捷键** — `/` 聚焦搜索，`Esc` 关闭详情
- 🌐 **URL 路由** — 支持浏览器前进/后退（hash路由）
- 📱 **响应式** — 桌面4列 / 平板3列 / 手机1列

## 🚀 启动

```bash
cd agent-navigator
python3 -m http.server 8080
```

然后访问 `http://localhost:8080`

## 📁 项目结构

```
agent-navigator/
├── index.html          # 主页面 (94行)
├── style.css           # 深色主题样式 (717行)
├── app.js              # 核心逻辑 (361行)
├── build_index.py      # 数据索引生成脚本
├── PLAN.md             # GLM-5.1 Leader 架构评审报告
├── README.md           # 本文件
└── data/
    ├── index.json      # 261条结构化元数据
    └── reports/        # 260+份原始研究报告 (.md)
```

## 🎨 设计

- 深色主题 (#0a0a0a 背景)
- Indigo → Purple 渐变强调色
- 8 种分类颜色编码
- Shimmer 骨架屏加载动画
- 卡片 Hover 动效 + 自定义滚动条

## 🏗️ 架构

纯前端应用，零依赖（除 marked.js CDN）：
- **数据层**: Python 脚本扫描 md → JSON 索引
- **展示层**: Vanilla JS + CSS Grid + marked.js
- **无后端**: 直接 `python3 -m http.server` 即可运行

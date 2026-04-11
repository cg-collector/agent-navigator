# AI Agent Navigator — Code Review v1

**审查人:** GLM-5.1 (Project Leader)
**日期:** 2026-04-11
**项目状态:** 功能可用，但多处质量问题需要修复

---

## 📊 数据质量审查

| 检查项 | 结果 |
|--------|------|
| 总条目 | 261 条 |
| 模板化标题 | **39 条**（`AI Agent 开源项目学习报告 #XXX`） |
| 组织名含垃圾 | **44 条**（含 `**`、`-`、数字开头等 markdown 残留） |
| key_innovations 垃圾 | **32 条**（含 `License`、`**`、`1.`、`项目名称:` 等） |
| 空标题 | 0 ✓ |
| Score 范围 | 2.2 - 9.5 ✓ |
| 分类分布 | 合理 ✓ |

---

## 🐛 问题清单（按严重度）

### P0 — 必须立即修复

#### P0-1: key_innovations 含垃圾数据，被当作标签直接渲染
- **位置:** `data/index.json` 多条记录 + `app.js showDetail()`
- **问题:** `key_innovations` 字段大量包含 `License`、`**`、`-`、数字开头、`项目名称:`、`语言支持:` 等垃圾值，这些被直接渲染为 `.meta-tag` 标签出现在详情面板
- **示例:** id=005, id=006, id=010, id=011, id=012
- **修复建议:** 过滤掉 key_innovations 中不含实质内容的短条目（长度<10 或匹配垃圾 pattern），或在渲染时做过滤

#### P0-2: 搜索高亮存在 XSS 风险
- **位置:** `app.js highlight()` 方法
- **问题:** 直接将用户输入作为正则表达式 source 拼接，未做 HTML 转义。如果搜索 `<script>`，会破坏页面或执行脚本
- **修复建议:** 先对 `text` 做 HTML 转义，再执行高亮替换

---

### P1 — 重要问题

#### P1-1: 39 条标题是模板文本
- **位置:** `data/index.json` (id: 007~261 范围内的部分)
- **问题:** `title` 字段大量是 `"AI Agent 开源项目学习报告 #XXX"`，完全无法识别是什么项目
- **影响:** 卡片显示无意义，用户无法通过标题了解项目
- **修复建议:** 标题应改为实际项目名称（如 `Agent S`、`DeepAgent`、`smolagents`）

#### P1-2: 44 条 organization 字段含 markdown 残留
- **位置:** `data/index.json`
- **问题:** `organization` 字段包含 `**`、`-`、数字编号等 markdown 格式残留，显然是从总结文本中错误提取的
- **示例:** `**1. ReAct（早期）**`、`- 通过 sub_agents 参数建立父子关系`
- **影响:** 详情面板 organization 显示混乱
- **修复建议:** 清理 organization 字段，提取纯文本名称

#### P1-3: ID 排序不正确
- **位置:** `app.js sortData()` → `case 'id'`
- **问题:** `String(a.id).localeCompare(String(b.id))` 对字符串排序会导致 `010` < `009`（字典序），而非数值序
- **修复建议:** `parseInt(a.id) - parseInt(b.id)` 或补零后缀统一长度比较

---

### P2 — 中等优化

#### P2-1: 卡片信息不够丰富
- **位置:** `app.js renderCards()`
- **问题:** 卡片只显示 title/summary/category/tags/stars/score，缺少 `organization` 和 `language` 字段——这两个字段对用户快速识别项目很有用
- **修复建议:** 在卡片底部 meta 区增加 organization 和 language 的显示

#### P2-2: 详情面板 key_innovations 展示效果差
- **位置:** `app.js showDetail()` → metaHtml
- **问题:** key_innovations 中的 markdown 片段（如 `**xxx**：` 格式）被直接作为纯文本标签显示，格式混乱
- **修复建议:** key_innovations 过滤垃圾后作为 `meta-tag` 显示，或改为小列表项

#### P2-3: 报告内链接未处理
- **位置:** `app.js showDetail()` → `marked.parse(md)`
- **问题:** 加载的 markdown 内容中可能有相对路径的链接或图片，无法正确解析
- **修复建议:** 对 markdown 中的相对链接（如 `001.md`）进行替换，或显示时注明

#### P2-4: 移动端标签栏横向滚动体验差
- **位置:** `style.css .tags-bar`
- **问题:** 标签栏 overflow-x: auto 但没有视觉暗示，用户不知道可以滚动
- **修复建议:** 右侧渐变遮罩暗示可滚动，或滚动到底部高亮

#### P2-5: 卡片标签点击范围过小
- **位置:** `app.js cardGrid click` 事件 + `style.css .card-tag`
- **问题:** 标签元素很小（font-size: 0.72rem），点击区域仅文字区域
- **修复建议:** 标签 padding 足够，但可适当增大文字大小以提升可读性

#### P2-6: 排序选择器选项未显示升序/降序符号
- **位置:** `index.html sortSelect`
- **问题:** "按评分 ↓" 选项文字带 ↓，但 select 显示时会截断或显示不全
- **修复建议:** 保持文字或用 CSS 自定义样式，视觉上更清晰

---

### P3 — 体验细节

#### P3-1: 骨架屏和实际卡片大小不完全对齐
- **位置:** `style.css .skeleton-card`
- **问题:** skeleton-card 和 .card 的 min-height 不同，切换时可能有轻微跳动
- **修复建议:** 统一设置 `.card` min-height: 160px

#### P3-2: 无结果状态可以更明显
- **位置:** `style.css .no-results`
- **问题:** 空状态文字不够醒目，没有插画或图形辅助
- **修复建议:** 考虑加入一个简单的 SVG 或 emoji 组合增强情感化设计

#### P3-3: 键盘快捷键 '/' 提示缺失
- **问题:** 代码支持 '/' 聚焦搜索框，但没有 UI 提示用户
- **修复建议:** 在搜索框 placeholder 旁增加 `"/"` 小标签

#### P3-4: 详情面板报告内容 Markdown 样式偏弱
- **位置:** `style.css .detail-body`
- **问题:** 报告内容渲染后的样式（标题层级、列表、图片）可以更精致
- **修复建议:** 增强 h1-h6 样式层级差异，优化 code block 配色，增加图片 max-width: 100%

---

## ✅ 现有优点

1. **骨架屏** 体验良好，加载状态有感知
2. **URL hash 路由** 实现完整，支持书签和分享
3. **分类颜色系统** 清晰，视觉层次分明
4. **详情面板** 动画流畅，overlay 设计合理
5. **Debounce 搜索** 实现正确，不会频繁触发
6. **标签点击搜索** 功能实用
7. **暗色主题** 整体协调，对比度良好
8. **响应式布局** 覆盖 640px/900px 两个断点

---

## 📋 修复优先级

| 优先级 | 问题数 | 行动计划 |
|--------|--------|---------|
| P0 | 2 | 立即修复：XSS漏洞 + key_innovations 垃圾过滤 |
| P1 | 3 | 修复 ID 排序 + 开始修复数据（标题/org 需要 build_index.py 重新生成或手动清理） |
| P2 | 4 | 增强卡片信息 + 移动端优化 + 报告链接处理 |
| P3 | 4 | 体验打磨 |

---

## ✅ 已修复问题

| 问题 | 修复内容 | 状态 |
|------|---------|------|
| P0-1 XSS高亮漏洞 | `highlight()` 先 HTML 转义再执行正则替换 | ✅ 已修复 |
| P0-2 key_innovations 垃圾 | 新增 `getCleanInnovations()` 过滤函数 | ✅ 已修复 |
| P1-3 ID排序错误 | `localeCompare` → `parseInt` 数值排序 | ✅ 已修复 |
| P2-1 卡片信息不足 | 新增 organization + language 显示区 + `.card-meta` 样式 | ✅ 已修复 |
| P2-4 移动端标签栏滚动 | CSS mask-image 渐变遮罩暗示可滚动 | ✅ 已修复 |
| P3-1 skeleton跳动 | 统一 `.card` min-height: 160px | ✅ 已修复 |
| P3-3 无键盘提示 | 搜索框 placeholder 增加 `(按 / 聚焦)` | ✅ 已修复 |
| P3-4 报告图片溢出 | `.detail-body img { max-width:100% }` | ✅ 已修复 |

## ⚠️ 待修复（数据层面，需重建 index.json）

这些问题需要修复 `build_index.py` 脚本并重新生成 `data/index.json`：

| 问题 | 说明 |
|------|------|
| 39 条模板标题 | `title` 字段为 `"AI Agent 开源项目学习报告 #XXX"`，需改为真实项目名 |
| 44 条脏 organization | 包含 `**`、`-`、数字开头等 markdown 残留，需清理为纯文本 |
| 32 条垃圾 key_innovations | 已通过 `getCleanInnovations()` 前端过滤缓解，但根本原因是生成脚本 |

**注意:** P1 的数据质量问题根源在于 `build_index.py` 脚本生成逻辑，需要同步修复生成脚本才能根治。

---

*Review 完成时间: 2026-04-11*

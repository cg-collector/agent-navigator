# AI Agent Navigator - 项目计划书

## 1. 架构评审

### 1.1 前端代码质量评估

**优点：**
- ✅ 深色主题设计完整，CSS 变量体系良好
- ✅ 响应式布局（mobile/desktop）
- ✅ Skeleton loading、键盘快捷键、hash 路由等 UX 细节到位
- ✅ 使用原生 JS，无外部依赖（除 marked.js）
- ✅ 搜索高亮、防抖、排序等核心功能完整

**严重问题（必须修复）：**

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| P0 | **分类标签不匹配** | 致命 | 8个分类中7个无法筛选 |
| P1 | `stars` 字段是字符串，全局排序无法正确工作 | 高 | 排序结果错误 |
| P2 | `key_innovations` 数据脏（包含 "GitHub", "Stars" 等非创新点内容） | 中 | 详情页显示垃圾数据 |
| P3 | `sortData` 中 `score` 排序使用 `(b.score\|\|0)`，但 score 是 float，应直接比较 | 低 | 功能正常但不精确 |

### 1.2 数据结构设计

```json
{
  "id": "001",           // ✅ 字符串 ID
  "title": "DeerFlow",   // ✅
  "url": "...",          // ✅
  "organization": "...", // ✅
  "stars": "43447",      // ⚠️ string 而非 number
  "category": "运行时框架(Runtime)", // ⚠️ 与前端标签不一致
  "score": 9.0,          // ✅ float
  "tags": [...],         // ✅
  "language": "C++",     // ✅
  "license": "",         // ✅
  "key_innovations": [...], // ⚠️ 包含无关字段
  "summary": "...",      // ✅
  "file": "reports/001.md" // ✅
}
```

**问题：**
1. `stars` 应为 number 类型，当前是 string
2. `category` 值与前端 hardcoded 标签不一致

---

## 2. 完整任务清单

### Phase 1: 紧急修复（阻塞功能）
- [ ] **T1**: 修复前端分类标签，与数据 category 值一一对应
- [ ] **T2**: 修复 `stars` 排序（转换为 number）
- [ ] **T3**: 修复 `sortSelect` 默认值与 UI 标签匹配

### Phase 2: 数据质量
- [ ] **T4**: 修复 `key_innovations` 数据清洗（过滤无关字段）
- [ ] **T5**: 重建 `data/index.json`（修复 stars 类型）

### Phase 3: 整合测试
- [ ] **T6**: 启动 http server 验证页面功能
- [ ] **T7**: 验证搜索、筛选、排序、详情面板
- [ ] **T8**: 验证详情页 Markdown 渲染

### Phase 4: 文档与交付
- [ ] **T9**: 写 README.md
- [ ] **T10**: 输出验收报告

---

## 3. 质量验收标准

### 功能验收
- [ ] 搜索框输入关键词 → 实时过滤卡片（300ms 防抖）
- [ ] 点击分类标签 → 只显示该分类项目
- [ ] 切换排序（评分/Stars/ID）→ 卡片顺序正确变化
- [ ] 点击卡片 → 侧边详情面板打开，显示元信息
- [ ] 详情面板显示 Markdown 渲染后的报告内容
- [ ] 点击标签（card-tag）→ 自动填入搜索框并过滤
- [ ] `/` 快捷键 → 聚焦搜索框
- [ ] `Escape` → 关闭详情面板
- [ ] 浏览器前进/后退 → URL hash 变化，状态同步

### 视觉验收
- [ ] 深色主题，背景网格图案
- [ ] 分类标签有对应颜色（8色）
- [ ] Skeleton loading 骨架屏
- [ ] 搜索高亮 `<mark>` 样式
- [ ] 响应式布局（320px+ 屏幕）

### 性能验收
- [ ] 首屏加载 < 2s（261项数据）
- [ ] 搜索响应 < 100ms（前端过滤）
- [ ] 详情面板打开 < 500ms

---

## 4. 风险点和备选方案

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 分类数据持续不匹配 | 高 | 高 | 修复 build_index.py 或前端标签映射 |
| key_innovations 数据脏 | 中 | 中 | 数据清洗脚本 + 前端过滤展示 |
| 261 个 md 文件报告加载慢 | 低 | 低 | 懒加载 + loading 状态 |

---

## 5. 修复计划

### 立即执行（build_index.py 重建数据）

```python
# 修复 stars 类型
item['stars'] = int(item['stars']) if item['stars'] else 0

# 修复 category 映射（前端去掉括号形式）
category_map = {
    '运行时框架(Runtime)': '运行时框架',
    '工具链(Toolchain)': '工具链',
    '编码框架(Coding Framework)': '编码框架',
    '多智能体(Multi-Agent)': '多智能体',
    'GUI-Agent': 'GUI-Agent',
    '浏览器代理(Browser Agent)': '浏览器代理',
    '评测基准(Benchmark)': '评测基准',
    '其他(Other)': '其他'
}
item['category'] = category_map.get(item['category'], item['category'])

# 过滤 key_innovations 脏数据
noise = {'GitHub', 'Stars', '解决的问题：', 'GitHub:', 'Stars:'}
item['key_innovations'] = [k for k in item['key_innovations'] if k not in noise]
```

### 前端修复

1. `tags-bar` 标签文字改为：`运行时框架`、`工具链`、`编码框架`、`多智能体`、`GUI-Agent`、`浏览器代理`、`评测基准`、`其他`
2. `app.js` 的 `getCategoryClass()` 方法补充缺失映射
3. `sortData()` 中 stars 排序前转换为 number

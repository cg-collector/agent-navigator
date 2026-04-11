#!/usr/bin/env python3
"""Scan agent study reports and generate structured JSON index. v2 — better extraction."""

import os, re, json, glob, shutil

SRC_DIR = "/home/openclaw/.openclaw/workspace/memory/agent-study"
OUT_DIR = "/home/openclaw/.openclaw/workspace/agent-navigator/data"
REPORTS_DIR = os.path.join(OUT_DIR, "reports")
INDEX_FILE = os.path.join(OUT_DIR, "index.json")

CATEGORIES = ["GUI-Agent", "编码框架", "多智能体", "工具链", "评测基准", "浏览器代理", "运行时框架", "其他"]

CATEGORY_MAP = {
    "GUI-Agent": "GUI-Agent",
    "编码框架(Coding Framework)": "编码框架",
    "多智能体(Multi-Agent)": "多智能体",
    "工具链(Toolchain)": "工具链",
    "评测基准(Benchmark)": "评测基准",
    "浏览器代理(Browser Agent)": "浏览器代理",
    "运行时框架(Runtime)": "运行时框架",
    "其他(Other)": "其他",
}

CATEGORY_RULES = {
    "GUI-Agent": [r"gui.?agent", r"computer.?use", r"视觉.*操作", r"屏幕.*操作", r"桌面.*自动化", r"gui.*control"],
    "编码框架": [r"coding.*agent", r"pair.*program", r"aider", r"code.*assist", r"ide.*agent",
                r"编程.*助手", r"devin", r"swe.?agent", r"openhands", r"cursor", r"copilot"],
    "多智能体": [r"multi.?agent", r"多智能体", r"agent.*team", r"agent.*swarm", r"crewai",
                r"autogen", r"agentscope", r"orchestrat", r"角色扮演", r"societies"],
    "工具链": [r"tool.*call", r"mcp", r"function.*call", r"memory.*manage", r"reme",
              r"rag.*tool", r"skill.*system", r"plugin.*arch", r"工具.*生态"],
    "评测基准": [r"benchmark", r"评测.*基准", r"evaluat", r"swe.?bench", r"webarena",
                r"agentbench", r"测试.*集", r"leaderboard"],
    "浏览器代理": [r"browser.*agent", r"web.*agent", r"browser.*use", r"surfing",
                  r"web.*navigation", r"playwright.*agent", r"puppeteer.*agent"],
    "运行时框架": [r"运行时", r"runtime", r"harness", r"langgraph", r"langchain",
                  r"agent.*runtime", r"工作流.*引擎", r"deerflow", r"agno", r"phidata",
                  r"dify", r"coze", r"fastapi.*agent"],
    "其他": [],
}

def skip_metadata(text):
    """Remove metadata block at the top of a report file."""
    lines = text.split('\n')
    result = []
    in_meta = True
    for line in lines:
        stripped = line.strip()
        if in_meta:
            if stripped == '' or stripped == '---' or stripped.startswith('***'):
                continue
            # Lines like: - **Key**: value  or  - **Key** (no value)
            if re.match(r'^[-*]\s+\*\*', stripped):
                continue
            # Lines like: > **Key**: value  or  > Key: value
            if stripped.startswith('>'):
                # But skip if it looks like a real paragraph (ends with 。？！ or long sentence)
                if len(stripped) > 30 and re.search(r'[。？！]$', stripped):
                    in_meta = False
                    result.append(line)
                continue
            # Lines like: - Key: value  or  * Key: value  (no bold markers)
            if re.match(r'^[-*]\s+([A-Za-z\u4e00-\u9fff0-9_ -]+)\s*[:：]\s*', stripped):
                continue
            # Table rows
            if re.match(r'^\s*\|', stripped):
                continue
            # Skip blank/separator lines at top
            # If we've seen enough non-meta lines, stop skipping
            in_meta = False
        result.append(line)
    return '\n'.join(result)

def extract_title(text, filename):
    m = re.search(r'^#+\s+(.+)', text, re.M)
    if m:
        t = m.group(1).strip()
        # Remove report suffixes like "学习报告", "研究报告", "AI Agent 开源项目学习报告"
        t = re.sub(r'\s*(学习报告|研究报告|开源\s*Agent\s*项目学习)\s*$', '', t)
        t = re.sub(r'\s*[-—:：]\s*.+$', '', t).strip()
        # Also remove leading prefixes
        t = re.sub(r'^(开源\s*)?Agent\s*项目\s*', '', t)
        if len(t) > 2:
            return t
    return os.path.splitext(filename)[0]

def extract_url(text):
    patterns = [
        r'(?:GitHub|github)[^\n]*?(https?://github\.com/[^\s\)\]}>"\']+)',
        r'项目链接[^\n]*?(https?://github\.com/[^\s\)\]}>"\']+)',
        r'(https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            url = m.group(1) if m.lastindex else m.group(0)
            url = re.sub(r'[).,;:\]}>"\']+$', '', url)
            if 'github.com' in url:
                return url
    return ""

def extract_stars(text):
    m = re.search(r'(?:Stars?)[^0-9]*?([\d,]+(?:\.\d+)?[kKmM+]?)', text, re.I)
    if m:
        s = m.group(1).replace(',', '').lower()
        if s.endswith('k'): return int(float(s[:-1]) * 1000)
        if s.endswith('m'): return int(float(s[:-1]) * 1000000)
        if '.' in s and not s.endswith(('k', 'm', 'K', 'M')):
            return 0
        try: return int(float(s.rstrip('+')))
        except: return 0
    return 0

def extract_org(text, url):
    # From explicit field
    m = re.search(r'(?:作者|团队|组织|Organization|团队|by\s+)[^\n]*?[:：]\s*([^\n]{2,40})', text, re.I)
    if m:
        org = m.group(1).strip().rstrip(',;，')
        if len(org) > 1 and len(org) < 50:
            return org
    # From URL
    if url:
        m2 = re.search(r'github\.com/([^/]+)/', url)
        if m2:
            return m2.group(1)
    return ""

def extract_language(text):
    langs = ['Python', 'TypeScript', 'JavaScript', 'Rust', 'Go', 'Java', 'Swift', 'Kotlin', 'C++', 'Ruby']
    for lang in langs:
        if re.search(rf'\b{lang}\b', text, re.I):
            return lang
    return ""

def extract_license(text):
    for lic in ['MIT', 'Apache-2.0', 'Apache 2.0', 'GPL-3.0', 'BSD-3-Clause', 'LGPL', 'AGPL', 'MPL']:
        if re.search(lic, text, re.I):
            return lic
    return ""

def extract_score(text):
    m = re.search(r'(?:评分|Score)[^\d]*?([0-9]\.[0-9])', text, re.I)
    if m:
        try: return round(float(m.group(1)), 1)
        except: pass
    stars_str = extract_stars(text)
    if stars_str:
        try:
            s = int(stars_str)
            if s > 50000: return 9.5
            elif s > 30000: return 9.0
            elif s > 20000: return 8.5
            elif s > 10000: return 8.0
            elif s > 5000: return 7.5
            elif s > 1000: return 7.0
            else: return 6.5
        except: pass
    return 7.0

def categorize(text, title):
    combined = (title + " " + text[:1500]).lower()
    best_cat, best_score = "其他", 0
    for cat, patterns in CATEGORY_RULES.items():
        if cat == "其他":
            continue
        score = sum(len(re.findall(p, combined)) for p in patterns)
        if score > best_score:
            best_score, best_cat = score, cat
    return best_cat

def extract_tags(text, title):
    combined = (title + " " + text[:1200])
    found = []
    seen = set()
    patterns = [
        r'\b(LangChain|LangGraph|OpenAI|Anthropic|GPT|Claude|LLM|RAG|MCP|VectorDB|Embedding)\b',
        r'\b(PyTorch|TensorFlow|FastAPI|Flask|NextJS|React|Vue|TypeScript|Rust|Go|Java)\b',
        r'\b(多模态|代码生成|自动化|对话系统|知识库|搜索引擎|数据分析|图像识别|推荐系统)\b',
        r'\b(Memory|ToolUse|FunctionCall|Streaming|StructuredOutput|FineTuning|RLHF)\b',
        r'\b(Agentic-RAG|ReAct|PlanExecute|Reflexion|CoT|ChainOfThought)\b',
        r'\b(Multi-Agent|Agent-Team|ToolChain|RAG|向量检索|记忆管理)\b',
    ]
    for pats in patterns:
        for m in re.finditer(pats, combined, re.I):
            tag = m.group(1)
            if tag not in seen and len(tag) >= 2:
                found.append(tag)
                seen.add(tag)
    return found[:5] if found else ["AI-Agent", "开源"]

def extract_innovations(text):
    """Extract key innovations from the actual content section, not metadata."""
    clean = skip_metadata(text)
    
    innovations = []
    # Look in 项目简介 / 一、项目简介 / ## 简介 sections
    m = re.search(
        r'(?:(?:^|\n)(?:##?\s*(?:项目简介|简介|核心创新|核心亮点)|一[.、]\s*项目))(.*?)(?=\n##|\n#|\Z)',
        clean, re.S | re.M)
    if m:
        section = m.group(1)
        # Find bullet points
        items = re.findall(r'[-*•]\s+(.{5,80})', section)
        innovations = [i.strip().rstrip('。；.,') for i in items[:3] if len(i.strip()) > 5]
        # If no bullets, take first sentences
        if not innovations:
            sents = re.split(r'[。？！\n]', section)
            innovations = [s.strip() for s in sents if len(s.strip()) > 10][:3]
    
    # Filter noise: metadata fragments that aren't real innovations
    noise_patterns = [
        r'^(GitHub|Stars?|评分|研究|项目地址|许可证|链接|官网|文档)',
        r'^\s*[A-Za-z]+://',  # URLs
        r'^\s*[-*•]?\s*[A-Za-z]+:\s*$',  # "Key:" alone
        r'^\s*[A-Za-z]+\s*[#:：]\s*$',
    ]
    filtered = []
    for inn in innovations:
        inn_clean = inn.strip()
        is_noise = False
        for pat in noise_patterns:
            if re.match(pat, inn_clean, re.I):
                is_noise = True
                break
        if not is_noise and len(inn_clean) > 4:
            filtered.append(inn_clean)
    innovations = filtered[:3] if filtered else []
    
    if not innovations:
        # Fallback: bold items in first 1000 chars of cleaned content
        bold = re.findall(r'\*\*([^*\n]{4,60})\*\*', clean[:1000])
        innovations = [b for b in bold if not re.match(r'^(GitHub|Stars?|评分|研究|项目地址)', b)][:3]
    
    return innovations[:3] if innovations else []

def extract_summary(text, title):
    """Get real content summary, not metadata."""
    clean = skip_metadata(text)
    
    # Look for explicit summary line
    m = re.search(r'(?:一句话简介|定位|Summary)[^\n]*?[:：]\s*([^\n]{10,120})', clean, re.I)
    if m:
        val = m.group(1).strip()
        if len(val) > 15:
            return val[:120]
    
    # Look in 项目简介 / 一、项目简介 section
    for section_title in [r'(?:^|\n)(?:##?\s*(?:项目简介|简介|一[.、]\s*项目简介?)|##\s*一[.、])',
                           r'(?:^|\n)(?:##?\s*项目(?:背景|简介|定位))']:
        m = re.search(section_title + r'(.*?)(?=\n##|\n#|\Z)', clean, re.S | re.M)
        if m:
            para = m.group(1).strip()
            para = re.sub(r'^[-*#>|\s]+', '', para)
            para = re.sub(r'\n+', ' ', para)
            if len(para) > 20:
                return para[:120]
    
    # Take first real paragraph after metadata
    paras = re.split(r'\n\n+', clean)
    for p in paras[:8]:
        p = p.strip()
        if len(p) > 30 and not p.startswith('#') and '---' not in p:
            p = re.sub(r'^[-*#>\s]+', '', p)
            # Reject if it's mostly bold markers
            if len(p) > 15 and p.count('**') < 3 and not re.match(r'^\*\*[^*]+\*\*$', p):
                return p[:120]
    
    return f"{title}的AI Agent研究分析"

def process_file(filepath):
    fname = os.path.basename(filepath)
    fid = os.path.splitext(fname)[0]
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    head = text[:2500]
    clean_head = skip_metadata(head)
    
    title = extract_title(text, fname)
    url = extract_url(head)
    org = extract_org(head, url)
    stars = extract_stars(head)
    language = extract_language(text)
    license_name = extract_license(head)
    score = round(extract_score(head), 1)
    category = categorize(text, title)
    tags = extract_tags(text, title)
    innovations = extract_innovations(text)
    summary = extract_summary(text, title)
    
    return {
        "id": fid,
        "title": title,
        "url": url,
        "organization": org,
        "stars": stars,
        "category": category,
        "score": score,
        "tags": tags,
        "language": language,
        "license": license_name,
        "key_innovations": innovations,
        "summary": summary,
        "file": f"reports/{fname}"
    }

def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
    print(f"Found {len(files)} markdown files")
    
    results = []
    for i, fp in enumerate(files):
        try:
            entry = process_file(fp)
            results.append(entry)
            shutil.copy2(fp, os.path.join(REPORTS_DIR, os.path.basename(fp)))
            if (i + 1) % 50 == 0:
                print(f"  Processed {i+1}/{len(files)}...")
        except Exception as e:
            print(f"  ERROR {os.path.basename(fp)}: {e}")
    
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Done! Total: {len(results)} reports indexed")
    print(f"📁 Index: {INDEX_FILE}")
    
    cat_stats = {}
    for r in results:
        c = r["category"]
        cat_stats[c] = cat_stats.get(c, 0) + 1
    
    print("\n📊 Category Distribution:")
    for c in CATEGORIES:
        n = cat_stats.get(c, 0)
        bar = "█" * min(n, 50)
        print(f"  {c:<35} {n:>3}  {bar}")
    
    # Spot check
    print("\n🔍 Sample entries:")
    for idx in [0, 50, 130, 200, 260]:
        if idx < len(results):
            r = results[idx]
            print(f"  [{r['id']}] {r['title']} | {r['category']} | ⭐{r['stars']} | score={r['score']}")
            print(f"       summary: {r['summary'][:80]}")
            if r['key_innovations']:
                print(f"       innovations: {r['key_innovations'][:2]}")

if __name__ == "__main__":
    main()

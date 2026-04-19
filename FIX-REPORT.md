# AI Agent Navigator — Bug Fix Report

**Date:** 2026-04-11  
**Fixer:** GLM-5.1 (Project Leader)  
**Bug:** "报告文件未找到" — Detail panel fails to load report content on card click

---

## Root Cause Analysis

### Primary Bug: Double `reports/` Path Prefix

**Location:** `app.js` → `showDetail()` method

The `showDetail()` method was constructing the report URL like this:

```javascript
// BEFORE (buggy)
const res = await fetch(`data/reports/${item.file}`);
```

The `data/index.json` entries store the file path in the `file` field like `"reports/001.md"`.

So the resulting URL became: `data/reports/reports/001.md` — **doubled `reports/` prefix!**

- **index.json `file` value:** `reports/001.md`
- **Code prepended:** `data/reports/`
- **Actual URL fetched:** `data/reports/reports/001.md` → **HTTP 404**

### Why It Wasn't Caught Earlier

All 261 entries in `data/index.json` have `file` values starting with `reports/`, and all report files exist under `data/reports/`. The bug only manifests when the fetch is actually attempted (clicking a card).

### Other Issues Found

1. **No error context:** The "报告文件未找到" message didn't indicate the actual URL or HTTP status code, making debugging difficult.
2. **No marked.js fallback:** If the CDN fails to load, `marked.parse()` would throw an error with no recovery.
3. **Error message hardcoded:** The Chinese message "报告文件未找到" was in the code without path information.

---

## Fixes Applied

### 1. URL Construction Fix (`app.js`)

**Before:**
```javascript
const res = await fetch(`data/reports/${item.file}`);
```

**After:**
```javascript
const res = await fetch('data/' + item.file);
```

This correctly produces `data/reports/001.md` from `item.file = "reports/001.md"`.

### 2. Better Error Messages

Added HTTP status code and path to all error messages:
```javascript
bodyEl.innerHTML = `<p style="...">报告文件未找到 (HTTP ${res.status})<br><small>路径: data/${item.file}</small></p>`;
```

### 3. marked.js Fallback

Added a runtime check before calling `marked.parse()`:
```javascript
if (typeof marked !== 'undefined' && marked.parse) {
    bodyEl.innerHTML = marked.parse(md);
} else {
    // Fallback: render as preformatted text
    bodyEl.innerHTML = '<pre style="...">' + md.replace(/</g, '&lt;') + '</pre>';
}
```

---

## Test Results

### File Existence Check
- **Total index entries:** 261
- **Missing report files:** 0 ✅
- **All 261 entries have matching `.md` files in `data/reports/`**

### HTTP Server Path Tests (via curl)

| URL | Expected | Result |
|-----|----------|--------|
| `http://localhost:8080/data/index.json` | HTTP 200 | ✅ 200 |
| `http://localhost:8080/data/reports/001.md` | HTTP 200 | ✅ 200 |
| `http://localhost:8080/data/reports/005.md` | HTTP 200 | ✅ 200 |
| `http://localhost:8080/data/reports/100.md` | HTTP 200 | ✅ 200 |
| `http://localhost:8080/data/reports/230.md` | HTTP 200 | ✅ 200 |
| `http://localhost:8080/data/reports/267.md` | HTTP 200 | ✅ 200 |
| ~~`http://localhost:8080/data/reports/reports/001.md`~~ | ~~HTTP 404~~ | ✅ 404 (bug URL correctly fails) |

### Search & Filter Tests

| Test | Result |
|------|--------|
| Search "langchain" | 54 results ✅ |
| Category "编码框架" | 36 results ✅ |

### Fixed URL Construction Verification

Simulated JavaScript URL construction:
- `fetch('data/' + 'reports/001.md')` → `data/reports/001.md` ✅

---

## GitHub Pages Compatibility

The fixed code uses relative paths that work correctly in both:
- **Local development:** `http://localhost:8080/index.html` → `data/reports/001.md`
- **GitHub Pages:** `https://cg-collector.github.io/agent-navigator/` → relative paths resolve correctly from the subdirectory

---

## Changes Summary

**File modified:** `app.js`

| Change | Lines |
|--------|-------|
| URL fix: `data/reports/${item.file}` → `'data/' + item.file` | ~1 |
| Error messages now include HTTP status and path | ~3 |
| marked.js fallback to `<pre>` if CDN fails | ~4 |
| Catch block now captures `err.message` | ~1 |

**Total:** 1 file changed, 12 insertions(+), 5 deletions(-)

---

## Commit

```
[main 0bbc665] 🐛 Fix: detail panel report loading + GitHub Pages compatibility
 1 file changed, 12 insertions(+), 5 deletions(-)
```

Note: `git push origin main` failed due to network issues reaching GitHub from this server. Commit exists locally.

---

## Verification Checklist

- [x] Bug reproduced and root cause identified
- [x] `showDetail()` URL construction fixed
- [x] All 261 report files exist and are reachable
- [x] Error messages improved with HTTP status + path
- [x] marked.js fallback added
- [x] Search and filter logic verified
- [x] GitHub Pages compatibility preserved
- [x] Local commit created
- [ ] git push (blocked by network)

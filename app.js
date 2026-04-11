/* ===== AI Agent Navigator - Main App ===== */

class AgentNavigator {
  constructor() {
    this.allData = [];
    this.filteredData = [];
    this.activeCategory = 'all';
    this.searchQuery = '';
    this.sortField = 'score';
    this.currentReportId = null;

    // DOM refs
    this.searchInput = document.getElementById('searchInput');
    this.sortSelect = document.getElementById('sortSelect');
    this.cardGrid = document.getElementById('cardGrid');
    this.skeletonGrid = document.getElementById('skeletonGrid');
    this.noResults = document.getElementById('noResults');
    this.tagsBar = document.getElementById('tagsBar');
    this.statsBar = document.getElementById('statsText');
    this.detailPanel = document.getElementById('detailPanel');
    this.detailOverlay = document.getElementById('detailOverlay');
    this.closeDetailBtn = document.getElementById('closeDetailBtn');

    this.init();
  }

  init() {
    this.bindEvents();
    this.parseHash();
    this.loadData();
  }

  bindEvents() {
    // Search with debounce
    let searchTimer;
    this.searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.applyFilters();
        this.updateHash();
      }, 300);
    });

    // Sort
    this.sortSelect.addEventListener('change', (e) => {
      this.sortField = e.target.value;
      this.applyFilters();
    });

    // Category tags
    this.tagsBar.addEventListener('click', (e) => {
      const btn = e.target.closest('.tag-btn');
      if (!btn) return;
      this.tagsBar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.activeCategory = btn.dataset.category;
      this.applyFilters();
      this.updateHash();
    });

    // Card clicks (delegated)
    this.cardGrid.addEventListener('click', (e) => {
      const tag = e.target.closest('.card-tag');
      if (tag) {
        e.stopPropagation();
        this.searchInput.value = tag.textContent.trim();
        this.searchQuery = tag.textContent.trim().toLowerCase();
        this.activeCategory = 'all';
        this.tagsBar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-category="all"]').classList.add('active');
        this.applyFilters();
        this.updateHash();
        return;
      }
      const card = e.target.closest('.card');
      if (card && !tag) {
        const id = card.dataset.id;
        this.showDetail(id);
      }
    });

    // Detail panel close
    this.closeDetailBtn.addEventListener('click', () => this.closeDetail());
    this.detailOverlay.addEventListener('click', () => this.closeDetail());

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeDetail();
      if (e.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        this.searchInput.focus();
        this.searchInput.select();
      }
    });

    // Hash change for browser back/forward
    window.addEventListener('hashchange', () => this.parseHash());
  }

  parseHash() {
    const hash = window.location.hash.slice(1);
    const params = new URLSearchParams(hash);

    if (params.has('search')) {
      this.searchQuery = params.get('search').toLowerCase();
      this.searchInput.value = params.get('search');
    } else {
      this.searchQuery = '';
      this.searchInput.value = '';
    }

    if (params.has('category')) {
      this.activeCategory = params.get('category');
      this.tagsBar.querySelectorAll('.tag-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.category === this.activeCategory);
      });
    } else {
      this.activeCategory = 'all';
      this.tagsBar.querySelectorAll('.tag-btn').forEach((b, i) => {
        b.classList.toggle('active', i === 0);
      });
    }

    if (params.has('report')) {
      this.showDetail(params.get('report'));
    }

    if (this.allData.length > 0) {
      this.applyFilters();
    }
  }

  updateHash() {
    const params = new URLSearchParams();
    if (this.searchQuery) params.set('search', this.searchInput.value);
    if (this.activeCategory !== 'all') params.set('category', this.activeCategory);
    const hash = params.toString();
    window.history.replaceState(null, '', hash ? '#' + hash : window.location.pathname);
  }

  async loadData() {
    try {
      const res = await fetch('data/index.json');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.allData = await res.json();
      this.skeletonGrid.style.display = 'none';
      this.applyFilters();
    } catch (err) {
      console.error('Failed to load data:', err);
      this.skeletonGrid.innerHTML = '<p style="color:var(--text-muted);grid-column:1/-1;text-align:center;padding:40px;">数据加载失败，请确保 data/index.json 存在</p>';
    }
  }

  applyFilters() {
    let data = this.filterData(this.searchQuery, this.activeCategory);
    data = this.sortData(data, this.sortField);
    this.filteredData = data;
    this.renderCards(data);
    this.updateStats(data);
  }

  filterData(query, category) {
    return this.allData.filter(item => {
      // Category filter
      if (category !== 'all' && item.category !== category) return false;

      // Search filter
      if (!query) return true;
      const q = query.toLowerCase();
      const fields = [
        item.title || '',
        item.summary || '',
        item.organization || '',
        item.id || '',
        ...(item.tags || []),
        ...(item.key_innovations || []),
        item.language || '',
        item.license || ''
      ];
      return fields.some(f => f.toLowerCase().includes(q));
    });
  }

  sortData(data, field) {
    const sorted = [...data];
    switch (field) {
      case 'score':
        sorted.sort((a, b) => (b.score || 0) - (a.score || 0));
        break;
      case 'stars':
        sorted.sort((a, b) => (b.stars || 0) - (a.stars || 0));
        break;
      case 'id':
        sorted.sort((a, b) => parseInt(a.id, 10) - parseInt(b.id, 10));
        break;
    }
    return sorted;
  }

  highlight(text, query) {
    if (!query || !text) return text || '';
    // Escape HTML first to prevent XSS, then do highlight
    const esc = (s) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    try {
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const re = new RegExp(`(${escaped})`, 'gi');
      return esc(text).replace(re, '<mark>$1</mark>');
    } catch { return esc(text); }
  }

  getCleanInnovations(arr) {
    if (!arr || !arr.length) return [];
    const garbage = /^(License|项目名称:|语言支持:|\d+\.\s*\*?$|-$|^[*-]\s*$)/;
    return arr.filter(ki => {
      const t = ki.trim();
      return t.length >= 8 && !garbage.test(t) && !t.startsWith('**') && !t.startsWith('1.') && !t.startsWith('2.') && !t.startsWith('3.');
    });
  }

  getCategoryClass(cat) {
    const map = {
      'GUI-Agent': 'cat-GUI-Agent',
      '编码框架': 'cat-编码框架',
      '多智能体': 'cat-多智能体',
      '工具链': 'cat-工具链',
      '评测基准': 'cat-评测基准',
      '浏览器代理': 'cat-浏览器代理',
      '运行时框架': 'cat-运行时框架'
    };
    return map[cat] || 'cat-其他';
  }

  renderCards(data) {
    if (data.length === 0) {
      this.cardGrid.innerHTML = '';
      this.noResults.style.display = 'block';
      return;
    }

    this.noResults.style.display = 'none';

    this.cardGrid.innerHTML = data.map(item => {
      const catClass = this.getCategoryClass(item.category);
      const titleHl = this.highlight(item.title, this.searchQuery);
      const summaryHl = this.highlight(item.summary, this.searchQuery);
      const tagsHtml = (item.tags || []).slice(0, 4).map(t =>
        `<span class="card-tag">${this.highlight(t, this.searchQuery)}</span>`
      ).join('');

      // Build footer meta row: org + language + stars
      const metaParts = [];
      if (item.organization && !item.organization.startsWith('**') && !item.organization.startsWith('-') && !item.organization.startsWith('1.') && !item.organization.startsWith('2.')) {
        metaParts.push(`<span class="card-meta-item">🏢 ${this.highlight(item.organization, this.searchQuery)}</span>`);
      }
      if (item.language) {
        metaParts.push(`<span class="card-meta-item">💻 ${item.language}</span>`);
      }
      if (item.stars) {
        metaParts.push(`<span class="card-stars">⭐ ${item.stars.toLocaleString()}</span>`);
      }

      return `
        <article class="card" data-id="${item.id}">
          <div class="card-header">
            <h3 class="card-title">${titleHl}</h3>
            ${item.score != null ? `<span class="card-score">${item.score}</span>` : ''}
          </div>
          <div class="card-category ${catClass}">
            <span class="cat-dot"></span>${item.category || '其他'}
          </div>
          <p class="card-summary">${summaryHl}</p>
          <div class="card-footer">
            <div class="card-tags">${tagsHtml}</div>
          </div>
          ${metaParts.length ? `<div class="card-meta">${metaParts.join('')}</div>` : ''}
        </article>
      `;
    }).join('');
  }

  updateStats(data) {
    const total = this.allData.length;
    const showing = data.length;
    const counts = {};
    this.allData.forEach(d => {
      const c = d.category || '其他';
      counts[c] = (counts[c] || 0) + 1;
    });

    const catColors = {
      'GUI-Agent': '#3b82f6', '编码框架': '#22c55e', '多智能体': '#f59e0b',
      '工具链': '#ec4899', '评测基准': '#14b8a6', '浏览器代理': '#8b5cf6',
      '运行时框架': '#ef4444', '其他': '#6b7280'
    };

    let html = `<strong>共 ${total} 个项目</strong>`;
    if (showing < total) html += ` · 显示 <strong>${showing}</strong> 个`;
    html += ' &nbsp;|&nbsp; ';

    const parts = Object.entries(counts).map(([c, n]) =>
      `<span class="stat-item"><span class="dot" style="background:${catColors[c]||'#888'}"></span>${c}: ${n}</span>`
    );
    html += parts.join('');

    this.statsBar.innerHTML = html;
  }

  async showDetail(id) {
    this.currentReportId = id;
    const item = this.allData.find(d => d.id === id);
    if (!item) return;

    // Update header
    document.getElementById('detailTitle').textContent = item.title || id;

    // Build meta
    const catClass = this.getCategoryClass(item.category);
    const metaHtml = `
      <div class="meta-row">
        <span class="meta-label">分类</span>
        <span class="meta-value"><span class="card-category ${catClass}" style="font-size:0.78rem;"><span class="cat-dot"></span>${item.category || '其他'}</span></span>
      </div>
      ${item.organization ? `<div class="meta-row"><span class="meta-label">组织</span><span class="meta-value">${item.organization}</span></div>` : ''}
      ${item.url ? `<div class="meta-row"><span class="meta-label">链接</span><span class="meta-value"><a href="${item.url}" target="_blank" rel="noopener">${item.url.replace(/^https?:\/\//,'')}</a></span></div>` : ''}
      ${item.stars ? `<div class="meta-row"><span class="meta-label">Stars</span><span class="meta-value">⭐ ${item.stars.toLocaleString()}</span></div>` : ''}
      ${item.score != null ? `<div class="meta-row"><span class="meta-label">评分</span><span class="meta-value" style="color:var(--accent-start);font-weight:600;">${item.score}</span></div>` : ''}
      ${item.language ? `<div class="meta-row"><span class="meta-label">语言</span><span class="meta-value">${item.language}</span></div>` : ''}
      ${item.license ? `<div class="meta-row"><span class="meta-label">协议</span><span class="meta-value">${item.license}</span></div>` : ''}
      ${(item.tags && item.tags.length) ? `<div class="meta-row"><span class="meta-label">标签</span><span class="meta-value">${item.tags.map(t => `<span class="meta-tag">${t}</span>`).join('')}</span></div>` : ''}
      ${this.getCleanInnovations(item.key_innovations).length ? `<div class="meta-row"><span class="meta-label">创新点</span><span class="meta-value">${this.getCleanInnovations(item.key_innovations).map(ki => `<span class="meta-tag">${ki}</span>`).join('')}</span></div>` : ''}
    `;
    document.getElementById('detailMeta').innerHTML = metaHtml;

    // Load report
    const bodyEl = document.getElementById('detailBody');
    bodyEl.innerHTML = '<div class="detail-loading">加载报告内容...</div>';

    // Show panel
    this.detailPanel.classList.add('open');
    this.detailOverlay.classList.add('visible');
    document.body.style.overflow = 'hidden';

    // Update hash without triggering full reload
    const params = new URLSearchParams(window.location.hash.slice(1));
    params.set('report', id);
    window.history.pushState(null, '', '#' + params.toString());

    // Fetch and render markdown
    // item.file is like "reports/001.md" (relative to data/ directory)
    if (item.file) {
      try {
        // item.file is relative to data/ so prefix with "data/"
        const res = await fetch('data/' + item.file);
        if (res.ok) {
          const md = await res.text();
          if (typeof marked !== 'undefined' && marked.parse) {
            bodyEl.innerHTML = marked.parse(md);
          } else {
            // Fallback: render as preformatted text if marked.js failed to load
            bodyEl.innerHTML = '<pre style="white-space:pre-wrap;font-size:0.9rem;line-height:1.6;">' + md.replace(/</g, '&lt;') + '</pre>';
          }
        } else {
          bodyEl.innerHTML = `<p style="color:var(--text-muted);">报告文件未找到 (HTTP ${res.status})<br><small>路径: data/${item.file}</small></p>`;
        }
      } catch (err) {
        bodyEl.innerHTML = `<p style="color:var(--text-muted);">报告加载失败: ${err.message}<br><small>路径: data/${item.file}</small></p>`;
      }
    } else {
      bodyEl.innerHTML = `<p style="color:var(--text-muted);margin-bottom:12px;">${item.summary || '暂无详细报告'}</p>`;
    }
  }

  closeDetail() {
    this.detailPanel.classList.remove('open');
    this.detailOverlay.classList.remove('visible');
    document.body.style.overflow = '';
    this.currentReportId = null;

    // Remove report from hash
    const params = new URLSearchParams(window.location.hash.slice(1));
    params.delete('report');
    const newHash = params.toString();
    window.history.pushState(null, '', newHash ? '#' + newHash : window.location.pathname);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  window.app = new AgentNavigator();
});

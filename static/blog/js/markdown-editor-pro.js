/**
 * Professional Markdown Editor
 * Features: Auto-save, drag-drop, templates, shortcuts, analytics
 */

class MarkdownEditorPro {
  constructor(options = {}) {
    this.editor = document.getElementById(options.editorId || 'mdx-editor');
    this.preview = document.getElementById(options.previewId || 'mdx-preview');
    this.form = this.editor ? this.editor.closest('form') : null;
    
    // State management
    this.state = {
      history: [this.editor ? this.editor.value : ''],
      historyStep: 0,
      isDirty: false,
      lastSaved: Date.now(),
      autoSaveInterval: null,
      syncScroll: true,
      spellCheck: true,
    };

    // Statistics
    this.stats = {
      words: 0,
      characters: 0,
      sentences: 0,
      paragraphs: 0,
      readingTime: 0,
    };

    // Configure marked with better options
    if (window.marked) {
      marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: true,
        mangle: false,
        highlight: (code, lang) => {
          if (window.hljs && lang && hljs.getLanguage(lang)) {
            try {
              return hljs.highlight(code, { language: lang }).value;
            } catch (e) {}
          }
          return code;
        },
      });
    }

    this.init();
  }

  init() {
    if (!this.editor || !this.preview) return;

    this.setupEventListeners();
    this.setupToolbar();
    this.setupTemplates();
    this.setupDragDrop();
    this.setupAutoSave();
    this.setupKeyboardShortcuts();
    this.renderPreview();
    this.updateStats();
    this.loadDraft();
  }

  setupEventListeners() {
    let typingTimer;
    const typingDelay = 300;

    // Editor input with debouncing
    this.editor.addEventListener('input', (e) => {
      this.state.isDirty = true;
      clearTimeout(typingTimer);
      typingTimer = setTimeout(() => {
        this.renderPreview();
        this.updateStats();
        this.saveToHistory(this.editor.value);
        this.updateCursorPosition();
      }, typingDelay);
    });

    // Cursor tracking
    ['keyup', 'click', 'focus'].forEach(event => {
      this.editor.addEventListener(event, () => this.updateCursorPosition());
    });

    // Tab handling
    this.editor.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        this.insertAtCursor('  ');
      }
    });

    // Prevent accidental navigation away
    window.addEventListener('beforeunload', (e) => {
      if (this.state.isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    });

    // Form submit - clear dirty flag
    if (this.form) {
      this.form.addEventListener('submit', () => {
        this.state.isDirty = false;
        this.clearDraft();
      });
    }

    // Synchronized scrolling
    this.editor.addEventListener('scroll', () => {
      if (this.state.syncScroll) {
        const scrollPercent = this.editor.scrollTop / (this.editor.scrollHeight - this.editor.clientHeight);
        this.preview.scrollTop = scrollPercent * (this.preview.scrollHeight - this.preview.clientHeight);
      }
    });
  }

  setupToolbar() {
    // Toolbar button handlers
    document.querySelectorAll('[data-snippet]').forEach(btn => {
      btn.addEventListener('click', () => {
        const snippet = btn.dataset.snippet.replace(/&#10;/g, '\n');
        const highlight = btn.dataset.highlight || '';
        this.insertSnippet(snippet, highlight);
      });
    });

    // View mode toggle
    const toggleViewBtn = document.getElementById('toggle-view-mode');
    const editorContainer = document.getElementById('editor-container');
    const viewModeText = document.getElementById('view-mode-text');
    let currentViewMode = 'split';

    if (toggleViewBtn && editorContainer) {
      toggleViewBtn.addEventListener('click', () => {
        const modes = ['split', 'editor-only', 'preview-only'];
        const currentIndex = modes.indexOf(currentViewMode);
        currentViewMode = modes[(currentIndex + 1) % modes.length];
        
        editorContainer.className = 'editor-split-view';
        if (currentViewMode !== 'split') {
          editorContainer.classList.add(currentViewMode);
        }
        
        const labels = { split: 'Split', 'editor-only': 'Editor', 'preview-only': 'Preview' };
        viewModeText.textContent = labels[currentViewMode];
      });
    }

    // Fullscreen toggle
    const fullscreenBtn = document.getElementById('toggle-fullscreen');
    const editorSection = document.querySelector('.space-y-6 > section:nth-child(2)');
    let isFullscreen = false;

    if (fullscreenBtn && editorSection) {
      fullscreenBtn.addEventListener('click', () => {
        isFullscreen = !isFullscreen;
        if (isFullscreen) {
          editorSection.classList.add('editor-fullscreen');
          document.getElementById('fullscreen-text').textContent = 'Exit';
          document.body.style.overflow = 'hidden';
        } else {
          editorSection.classList.remove('editor-fullscreen');
          document.getElementById('fullscreen-text').textContent = 'Expand';
          document.body.style.overflow = '';
        }
      });

      // ESC key to exit fullscreen
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isFullscreen) {
          fullscreenBtn.click();
        }
      });
    }

    // Clear editor
    const clearBtn = document.getElementById('clear-editor');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (this.editor.value && confirm('Are you sure you want to clear all content?')) {
          this.saveToHistory(this.editor.value);
          this.editor.value = '';
          this.renderPreview();
          this.updateStats();
        }
      });
    }

    // Undo/Redo
    document.getElementById('undo-editor')?.addEventListener('click', () => this.undo());
    document.getElementById('redo-editor')?.addEventListener('click', () => this.redo());

    // Copy HTML
    const copyHtmlBtn = document.getElementById('copy-html');
    if (copyHtmlBtn) {
      copyHtmlBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(this.preview.innerHTML);
          this.showToast('HTML copied to clipboard!', 'success');
        } catch (e) {
          this.showToast('Failed to copy HTML', 'error');
        }
      });
    }

    // Sync scroll toggle
    const syncScrollBtn = document.getElementById('toggle-sync-scroll');
    if (syncScrollBtn) {
      syncScrollBtn.addEventListener('click', () => {
        this.state.syncScroll = !this.state.syncScroll;
        syncScrollBtn.classList.toggle('active', this.state.syncScroll);
        this.showToast(`Scroll sync ${this.state.syncScroll ? 'enabled' : 'disabled'}`, 'info');
      });
    }

    // Spell check toggle
    const spellCheckBtn = document.getElementById('toggle-spell-check');
    if (spellCheckBtn) {
      spellCheckBtn.addEventListener('click', () => {
        this.state.spellCheck = !this.state.spellCheck;
        this.editor.spellcheck = this.state.spellCheck;
        spellCheckBtn.classList.toggle('active', this.state.spellCheck);
      });
    }
  }

  setupTemplates() {
    // Template insertion
    document.querySelectorAll('[data-template]').forEach(btn => {
      btn.addEventListener('click', () => {
        const templateId = btn.dataset.template;
        const template = document.getElementById(templateId);
        if (template) {
          const content = template.content.textContent.trim() + '\n\n';
          this.insertAtCursor(content);
        }
      });
    });

    // Copy URL buttons
    document.querySelectorAll('[data-copy]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const value = btn.dataset.copy;
        try {
          await navigator.clipboard.writeText(value);
          const original = btn.textContent;
          btn.textContent = 'Copied!';
          setTimeout(() => btn.textContent = original, 1500);
        } catch (e) {
          this.showToast('Failed to copy', 'error');
        }
      });
    });

    // Quick templates dropdown
    const templateBtn = document.getElementById('quick-templates');
    if (templateBtn) {
      templateBtn.addEventListener('click', () => {
        this.showTemplatesModal();
      });
    }
  }

  setupDragDrop() {
    // Drag and drop for images
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this.editor.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      this.editor.addEventListener(eventName, () => {
        this.editor.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      this.editor.addEventListener(eventName, () => {
        this.editor.classList.remove('drag-over');
      });
    });

    this.editor.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files);
      const imageFiles = files.filter(file => file.type.startsWith('image/'));
      
      if (imageFiles.length > 0) {
        this.handleImageUpload(imageFiles);
      }
    });

    // Paste image handler
    this.editor.addEventListener('paste', (e) => {
      const items = Array.from(e.clipboardData.items);
      const imageItems = items.filter(item => item.type.startsWith('image/'));
      
      if (imageItems.length > 0) {
        e.preventDefault();
        const files = imageItems.map(item => item.getAsFile()).filter(Boolean);
        this.handleImageUpload(files);
      }
    });
  }

  setupAutoSave() {
    const statusEl = document.getElementById('save-status');
    
    // Auto-save every 30 seconds
    this.state.autoSaveInterval = setInterval(() => {
      if (this.state.isDirty) {
        this.saveDraft();
        if (statusEl) {
          statusEl.textContent = '💾 Draft saved';
          statusEl.className = 'text-xs text-green-600 dark:text-green-400';
        }
      }
    }, 30000);

    // Update save status indicator
    setInterval(() => {
      if (statusEl && this.state.isDirty) {
        const elapsed = Math.floor((Date.now() - this.state.lastSaved) / 1000);
        if (elapsed < 60) {
          statusEl.textContent = `✏️ Unsaved changes`;
          statusEl.className = 'text-xs text-amber-600 dark:text-amber-400';
        }
      }
    }, 5000);
  }

  setupKeyboardShortcuts() {
    const shortcuts = {
      'Ctrl+b': () => this.insertSnippet('**Bold text**', 'Bold text'),
      'Ctrl+i': () => this.insertSnippet('_Italic text_', 'Italic text'),
      'Ctrl+k': () => this.insertSnippet('[Link text](https://example.com)', 'Link text'),
      'Ctrl+Alt+c': () => this.insertSnippet('`inline code`', 'inline code'),
      'Ctrl+Alt+h': () => this.insertSnippet('## Heading\n\n', ''),
      'Ctrl+Alt+l': () => this.insertSnippet('- List item\n', ''),
      'Ctrl+Alt+q': () => this.insertSnippet('> Quote\n\n', ''),
      'Ctrl+s': (e) => { e.preventDefault(); this.saveDraft(); this.showToast('Draft saved!', 'success'); },
      'Ctrl+z': (e) => { if (!e.shiftKey) { e.preventDefault(); this.undo(); }},
      'Ctrl+y': (e) => { e.preventDefault(); this.redo(); },
      'Ctrl+Shift+z': (e) => { e.preventDefault(); this.redo(); },
      'Ctrl+/': (e) => { e.preventDefault(); this.showKeyboardShortcuts(); },
    };

    this.editor.addEventListener('keydown', (e) => {
      const key = `${e.ctrlKey ? 'Ctrl+' : ''}${e.altKey ? 'Alt+' : ''}${e.shiftKey ? 'Shift+' : ''}${e.key.toLowerCase()}`;
      
      if (shortcuts[key]) {
        shortcuts[key](e);
      }
    });
  }

  renderPreview() {
    if (!this.preview || !this.editor) return;

    const raw = this.editor.value || '';

    if (!raw.trim()) {
      this.preview.innerHTML = `
        <div class="flex flex-col items-center justify-center py-16 text-center text-neutral-400 dark:text-neutral-500">
          <svg class="h-12 w-12 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p class="text-sm font-medium">Your preview will appear here</p>
          <p class="text-xs mt-2">Start typing to see your formatted content</p>
        </div>
      `;
    } else {
      let html = window.marked ? marked.parse(raw) : raw;
      html = window.DOMPurify ? DOMPurify.sanitize(html) : html;
      
      // Add table of contents if there are headings
      const headings = this.extractHeadings(raw);
      if (headings.length > 0) {
        const toc = this.generateTableOfContents(headings);
        html = toc + html;
      }
      
      this.preview.innerHTML = html;

      // Highlight code blocks
      if (window.hljs) {
        this.preview.querySelectorAll('pre code').forEach(block => {
          hljs.highlightElement(block);
        });
      }

      // Add click-to-copy to code blocks
      this.preview.querySelectorAll('pre').forEach(pre => {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.onclick = async () => {
          const code = pre.querySelector('code')?.textContent || pre.textContent;
          try {
            await navigator.clipboard.writeText(code);
            copyBtn.innerHTML = '✓ Copied';
            setTimeout(() => copyBtn.innerHTML = '📋 Copy', 2000);
          } catch (e) {}
        };
        pre.style.position = 'relative';
        pre.appendChild(copyBtn);
      });
    }
  }

  updateStats() {
    const text = this.editor.value || '';
    
    // Calculate statistics
    this.stats.characters = text.length;
    this.stats.words = text.trim() ? text.trim().split(/\s+/).length : 0;
    this.stats.sentences = (text.match(/[.!?]+/g) || []).length;
    this.stats.paragraphs = text.split(/\n\n+/).filter(p => p.trim()).length;
    this.stats.readingTime = Math.max(1, Math.ceil(this.stats.words / 200));

    // Update UI
    const wordCountEl = document.getElementById('mdx-word-count');
    const readingTimeEl = document.getElementById('mdx-reading-time');

    if (wordCountEl) {
      const span = wordCountEl.querySelector('span') || wordCountEl;
      span.textContent = `${this.stats.words} ${this.stats.words === 1 ? 'word' : 'words'}`;
    }

    if (readingTimeEl) {
      const span = readingTimeEl.querySelector('span') || readingTimeEl;
      span.textContent = `~${this.stats.readingTime} ${this.stats.readingTime === 1 ? 'min' : 'mins'}`;
    }

    // Update character count if exists
    const charCountEl = document.getElementById('char-count');
    if (charCountEl) {
      charCountEl.textContent = `${this.stats.characters} chars`;
    }
  }

  updateCursorPosition() {
    const cursorPositionEl = document.getElementById('cursor-position');
    if (!cursorPositionEl || !this.editor) return;

    const pos = this.editor.selectionStart;
    const textBefore = this.editor.value.substring(0, pos);
    const lines = textBefore.split('\n');
    const line = lines.length;
    const col = lines[lines.length - 1].length + 1;

    cursorPositionEl.textContent = `Line ${line}, Col ${col}`;
  }

  insertSnippet(snippet, highlight) {
    this.insertAtCursor(snippet);

    if (highlight && snippet.includes(highlight)) {
      const start = this.editor.selectionStart;
      const highlightPos = snippet.indexOf(highlight);
      const highlightStart = start - snippet.length + highlightPos;
      const highlightEnd = highlightStart + highlight.length;
      this.editor.setSelectionRange(highlightStart, highlightEnd);
    }

    this.editor.focus();
    this.renderPreview();
    this.updateStats();
    this.saveToHistory(this.editor.value);
  }

  insertAtCursor(text) {
    const start = this.editor.selectionStart;
    const end = this.editor.selectionEnd;
    const before = this.editor.value.substring(0, start);
    const after = this.editor.value.substring(end);
    
    this.editor.value = before + text + after;
    this.editor.selectionStart = this.editor.selectionEnd = start + text.length;
    this.state.isDirty = true;
  }

  saveToHistory(value) {
    if (value === this.state.history[this.state.historyStep]) return;
    
    this.state.history = this.state.history.slice(0, this.state.historyStep + 1);
    this.state.history.push(value);
    this.state.historyStep++;
    
    // Limit history size
    if (this.state.history.length > 50) {
      this.state.history.shift();
      this.state.historyStep--;
    }
  }

  undo() {
    if (this.state.historyStep > 0) {
      this.state.historyStep--;
      this.editor.value = this.state.history[this.state.historyStep];
      this.renderPreview();
      this.updateStats();
      this.updateCursorPosition();
    }
  }

  redo() {
    if (this.state.historyStep < this.state.history.length - 1) {
      this.state.historyStep++;
      this.editor.value = this.state.history[this.state.historyStep];
      this.renderPreview();
      this.updateStats();
      this.updateCursorPosition();
    }
  }

  saveDraft() {
    try {
      localStorage.setItem('blog_draft_content', this.editor.value);
      localStorage.setItem('blog_draft_timestamp', Date.now().toString());
      this.state.lastSaved = Date.now();
      this.state.isDirty = false;
    } catch (e) {
      console.error('Failed to save draft:', e);
    }
  }

  loadDraft() {
    try {
      const draft = localStorage.getItem('blog_draft_content');
      const timestamp = localStorage.getItem('blog_draft_timestamp');
      
      if (draft && timestamp && !this.editor.value) {
        const age = Date.now() - parseInt(timestamp);
        const hours = Math.floor(age / 3600000);
        
        if (hours < 24) {
          if (confirm(`Found a draft from ${hours} hour(s) ago. Would you like to restore it?`)) {
            this.editor.value = draft;
            this.renderPreview();
            this.updateStats();
            this.showToast('Draft restored!', 'success');
          }
        }
      }
    } catch (e) {
      console.error('Failed to load draft:', e);
    }
  }

  clearDraft() {
    try {
      localStorage.removeItem('blog_draft_content');
      localStorage.removeItem('blog_draft_timestamp');
    } catch (e) {}
  }

  async handleImageUpload(files) {
    this.showToast(`Uploading ${files.length} image(s)...`, 'info');
    
    // In a real implementation, you would upload to your server
    // For now, we'll create a placeholder
    for (const file of files) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const markdown = `\n![${file.name}](${e.target.result})\n`;
        this.insertAtCursor(markdown);
        this.renderPreview();
      };
      reader.readAsDataURL(file);
    }
    
    this.showToast('Images inserted! Please upload via the sidebar for permanent storage.', 'warning');
  }

  extractHeadings(markdown) {
    const headings = [];
    const lines = markdown.split('\n');
    
    for (const line of lines) {
      const match = line.match(/^(#{1,6})\s+(.+)$/);
      if (match) {
        headings.push({
          level: match[1].length,
          text: match[2],
          id: match[2].toLowerCase().replace(/[^\w]+/g, '-'),
        });
      }
    }
    
    return headings;
  }

  generateTableOfContents(headings) {
    if (headings.length === 0) return '';
    
    let toc = '<div class="toc"><h2>Table of Contents</h2><ul>';
    
    for (const heading of headings) {
      const indent = '  '.repeat(heading.level - 1);
      toc += `${indent}<li><a href="#${heading.id}">${heading.text}</a></li>`;
    }
    
    toc += '</ul></div>';
    return toc;
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    const container = document.getElementById('toast-container') || (() => {
      const div = document.createElement('div');
      div.id = 'toast-container';
      document.body.appendChild(div);
      return div;
    })();
    
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  showKeyboardShortcuts() {
    const shortcuts = [
      { keys: 'Ctrl + B', action: 'Bold text' },
      { keys: 'Ctrl + I', action: 'Italic text' },
      { keys: 'Ctrl + K', action: 'Insert link' },
      { keys: 'Ctrl + Alt + C', action: 'Inline code' },
      { keys: 'Ctrl + Alt + H', action: 'Heading' },
      { keys: 'Ctrl + Alt + L', action: 'List item' },
      { keys: 'Ctrl + Alt + Q', action: 'Quote' },
      { keys: 'Ctrl + S', action: 'Save draft' },
      { keys: 'Ctrl + Z', action: 'Undo' },
      { keys: 'Ctrl + Y', action: 'Redo' },
      { keys: 'Ctrl + /', action: 'Show shortcuts' },
      { keys: 'Tab', action: 'Indent' },
      { keys: 'Esc', action: 'Exit fullscreen' },
    ];

    const modal = document.createElement('div');
    modal.className = 'shortcuts-modal';
    modal.innerHTML = `
      <div class="shortcuts-content">
        <h3>Keyboard Shortcuts</h3>
        <div class="shortcuts-list">
          ${shortcuts.map(s => `
            <div class="shortcut-item">
              <kbd>${s.keys}</kbd>
              <span>${s.action}</span>
            </div>
          `).join('')}
        </div>
        <button class="btn-close" onclick="this.closest('.shortcuts-modal').remove()">Close</button>
      </div>
    `;
    
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('show'), 10);
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });
  }

  showTemplatesModal() {
    const templates = [
      {
        name: 'Blog Post',
        content: `# Title Here

## Introduction

Your opening paragraph...

## Main Content

### Section 1

Content here...

### Section 2

More content...

## Conclusion

Wrap up your thoughts...`
      },
      {
        name: 'Tutorial',
        content: `# Tutorial: [Topic]

## Prerequisites

- Requirement 1
- Requirement 2

## Step 1: Setup

\`\`\`bash
# Command here
\`\`\`

## Step 2: Implementation

Code and explanation...

## Troubleshooting

Common issues and solutions...`
      },
      {
        name: 'Code Review',
        content: `# Code Review: [Feature Name]

## Overview

Brief description...

## Changes

\`\`\`javascript
// Code snippet
\`\`\`

## Pros

- Advantage 1
- Advantage 2

## Cons

- Issue 1
- Issue 2

## Recommendations

Suggestions for improvement...`
      },
    ];

    const modal = document.createElement('div');
    modal.className = 'templates-modal';
    modal.innerHTML = `
      <div class="templates-content">
        <h3>Quick Templates</h3>
        <div class="templates-grid">
          ${templates.map((t, i) => `
            <button class="template-card" data-index="${i}">
              <h4>${t.name}</h4>
              <p>Click to insert</p>
            </button>
          `).join('')}
        </div>
        <button class="btn-close" onclick="this.closest('.templates-modal').remove()">Close</button>
      </div>
    `;
    
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('show'), 10);
    
    modal.querySelectorAll('.template-card').forEach((card, index) => {
      card.addEventListener('click', () => {
        this.editor.value = templates[index].content;
        this.renderPreview();
        this.updateStats();
        this.saveToHistory(this.editor.value);
        modal.remove();
        this.showToast('Template inserted!', 'success');
      });
    });
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });
  }

  destroy() {
    if (this.state.autoSaveInterval) {
      clearInterval(this.state.autoSaveInterval);
    }
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.markdownEditor = new MarkdownEditorPro({
    editorId: 'mdx-editor',
    previewId: 'mdx-preview',
  });
});

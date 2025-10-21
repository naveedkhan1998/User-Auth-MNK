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
    // Initialize tag management and image preview first (they work independently)
    this.setupTagManagement();
    this.setupImagePreview();
    this.setupSEOValidator();
    this.setupVersionHistory();
    this.setupLinkManagement();

    // Only setup editor-specific features if editor exists
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

    // Synchronized scrolling (improved to handle TOC)
    this.editor.addEventListener('scroll', () => {
      if (this.state.syncScroll) {
        // Calculate scroll percentage based on content, not total height
        const editorScrollableHeight = this.editor.scrollHeight - this.editor.clientHeight;
        const previewScrollableHeight = this.preview.scrollHeight - this.preview.clientHeight;
        
        if (editorScrollableHeight > 0 && previewScrollableHeight > 0) {
          const scrollPercent = this.editor.scrollTop / editorScrollableHeight;
          
          // Adjust for TOC if present
          const toc = this.preview.querySelector('.toc');
          const tocOffset = toc ? toc.offsetHeight : 0;
          
          // Apply scroll with TOC offset consideration
          this.preview.scrollTop = (scrollPercent * (previewScrollableHeight - tocOffset)) + tocOffset;
        }
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
    
    // Get the blog post ID from the URL or form
    const blogPostId = this.getBlogPostId();
    
    if (!blogPostId) {
      this.showToast('Please save the post first before uploading images.', 'warning');
      return;
    }
    
    for (const file of files) {
      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('alt_text', file.name.replace(/\.[^/.]+$/, '')); // filename without extension
        formData.append('caption', '');
        
        // Get CSRF token
        const csrfToken = this.getCSRFToken();
        
        // Upload to Django backend
        const uploadUrl = `/console/blog/${blogPostId}/upload-image/`;
        const response = await fetch(uploadUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
          },
          body: formData,
        });
        
        if (response.ok) {
          const data = await response.json();
          
          // Insert markdown with the uploaded image URL
          const markdown = `\n![${data.alt_text || file.name}](${data.image_url})\n`;
          this.insertAtCursor(markdown);
          this.renderPreview();
          
          this.showToast(`${file.name} uploaded successfully!`, 'success');
          
          // Update sidebar image list dynamically without page reload
          this.updateImageSidebar(data);
        } else {
          const errorData = await response.json().catch(() => ({}));
          this.showToast(`Failed to upload ${file.name}: ${errorData.error || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        console.error('Upload error:', error);
        this.showToast(`Error uploading ${file.name}`, 'error');
      }
    }
  }
  
  getBlogPostId() {
    // Try to get from URL pattern: /console/blog/{uuid}/
    const urlMatch = window.location.pathname.match(/\/console\/blog\/([a-f0-9-]+)\//);
    if (urlMatch) {
      return urlMatch[1];
    }
    
    // Try to get from a hidden input or data attribute
    const form = this.editor.closest('form');
    if (form) {
      const idInput = form.querySelector('input[name="blog_post_id"]');
      if (idInput) {
        return idInput.value;
      }
    }
    
    return null;
  }
  
  getCSRFToken() {
    // Get CSRF token from cookie
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  updateImageSidebar(imageData) {
    // Find the image list in the sidebar
    const imageList = document.querySelector('.blog-images-list, #blog-images, [class*="image-list"]');
    
    if (!imageList) {
      // If no sidebar exists, silently skip (might be on create page)
      return;
    }

    // Create a new image item element
    const imageItem = document.createElement('div');
    imageItem.className = 'image-item border rounded p-2 mb-2';
    imageItem.innerHTML = `
      <img src="${imageData.image_url}" alt="${imageData.alt_text}" class="w-full h-auto mb-1 rounded">
      <p class="text-sm text-gray-700 truncate" title="${imageData.alt_text}">${imageData.alt_text}</p>
      ${imageData.caption ? `<p class="text-xs text-gray-500 truncate">${imageData.caption}</p>` : ''}
      <small class="text-xs text-gray-400">Just uploaded</small>
    `;

    // Add to the top of the list
    imageList.insertBefore(imageItem, imageList.firstChild);

    // Add a subtle highlight animation
    imageItem.style.backgroundColor = '#d1fae5'; // light green
    setTimeout(() => {
      imageItem.style.transition = 'background-color 1s ease';
      imageItem.style.backgroundColor = '';
    }, 100);
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

  // ==================== SEO OPTIMIZATION ====================

  setupSEOValidator() {
    const titleInput = document.querySelector('input[name="title"]');
    const slugInput = document.querySelector('input[name="slug"]');
    const metaTitleInput = document.querySelector('input[name="meta_title"]');
    const metaDescInput = document.querySelector('textarea[name="meta_description"]');
    const descriptionInput = document.querySelector('textarea[name="description"]');

    if (!titleInput || !metaTitleInput || !metaDescInput) return;

    // Initialize on load
    this.updateSEOPreview();
    this.validateSEOFields();

    // Add event listeners
    titleInput.addEventListener('input', () => {
      this.updateSEOPreview();
      this.validateSEOFields();
    });

    slugInput?.addEventListener('input', () => {
      this.updateSEOPreview();
    });

    metaTitleInput.addEventListener('input', () => {
      this.updateSEOPreview();
      this.validateMetaTitle();
      this.calculateSEOScore();
    });

    metaDescInput.addEventListener('input', () => {
      this.updateSEOPreview();
      this.validateMetaDescription();
      this.calculateSEOScore();
    });

    descriptionInput?.addEventListener('input', () => {
      this.updateSEOPreview();
      this.calculateSEOScore();
    });
  }

  validateMetaTitle() {
    const metaTitleInput = document.querySelector('input[name="meta_title"]');
    const counter = document.getElementById('meta-title-counter');
    const bar = document.getElementById('meta-title-bar');

    if (!metaTitleInput || !counter || !bar) return;

    const length = metaTitleInput.value.length;
    const optimal = { min: 50, max: 60 };

    // Update counter
    counter.textContent = `${length} / 60 characters`;

    // Color coding
    if (length === 0) {
      counter.className = 'text-xs font-medium text-gray-500';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-gray-200';
      bar.style.width = '0%';
    } else if (length < optimal.min) {
      counter.className = 'text-xs font-medium text-yellow-600 dark:text-yellow-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-yellow-400';
      bar.style.width = `${(length / optimal.min) * 100}%`;
    } else if (length <= optimal.max) {
      counter.className = 'text-xs font-medium text-green-600 dark:text-green-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-green-500';
      bar.style.width = '100%';
    } else {
      counter.className = 'text-xs font-medium text-red-600 dark:text-red-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-red-500';
      bar.style.width = '100%';
    }
  }

  validateMetaDescription() {
    const metaDescInput = document.querySelector('textarea[name="meta_description"]');
    const counter = document.getElementById('meta-description-counter');
    const bar = document.getElementById('meta-description-bar');

    if (!metaDescInput || !counter || !bar) return;

    const length = metaDescInput.value.length;
    const optimal = { min: 120, max: 160 };

    // Update counter
    counter.textContent = `${length} / 160 characters`;

    // Color coding
    if (length === 0) {
      counter.className = 'text-xs font-medium text-gray-500';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-gray-200';
      bar.style.width = '0%';
    } else if (length < optimal.min) {
      counter.className = 'text-xs font-medium text-yellow-600 dark:text-yellow-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-yellow-400';
      bar.style.width = `${(length / optimal.min) * 100}%`;
    } else if (length <= optimal.max) {
      counter.className = 'text-xs font-medium text-green-600 dark:text-green-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-green-500';
      bar.style.width = '100%';
    } else {
      counter.className = 'text-xs font-medium text-red-600 dark:text-red-400';
      bar.className = 'h-1 rounded-full mt-1 transition-all bg-red-500';
      bar.style.width = '100%';
    }
  }

  validateSEOFields() {
    this.validateMetaTitle();
    this.validateMetaDescription();
  }

  updateSEOPreview() {
    const titleInput = document.querySelector('input[name="title"]');
    const slugInput = document.querySelector('input[name="slug"]');
    const metaTitleInput = document.querySelector('input[name="meta_title"]');
    const metaDescInput = document.querySelector('textarea[name="meta_description"]');
    const descriptionInput = document.querySelector('textarea[name="description"]');

    const previewTitle = document.getElementById('preview-title');
    const previewDescription = document.getElementById('preview-description');
    const previewSlug = document.getElementById('preview-slug');

    if (!previewTitle || !previewDescription || !previewSlug) return;

    // Update preview title (use meta_title if exists, otherwise use title)
    const displayTitle = metaTitleInput?.value || titleInput?.value || 'Your Post Title';
    previewTitle.textContent = displayTitle;

    // Update preview description (use meta_description if exists, otherwise use description)
    const displayDesc = metaDescInput?.value || descriptionInput?.value || 'Your post description will appear here...';
    previewDescription.textContent = displayDesc;

    // Update preview slug
    const displaySlug = slugInput?.value || 'your-post-slug';
    previewSlug.textContent = displaySlug;
  }

  calculateSEOScore() {
    const titleInput = document.querySelector('input[name="title"]');
    const metaTitleInput = document.querySelector('input[name="meta_title"]');
    const metaDescInput = document.querySelector('textarea[name="meta_description"]');
    const descriptionInput = document.querySelector('textarea[name="description"]');
    const badge = document.getElementById('seo-score-badge');

    if (!badge) return;

    let score = 0;
    let maxScore = 4;

    // Check title length
    const titleLength = (metaTitleInput?.value || titleInput?.value || '').length;
    if (titleLength >= 50 && titleLength <= 60) score += 1;

    // Check meta description length
    const descLength = (metaDescInput?.value || descriptionInput?.value || '').length;
    if (descLength >= 120 && descLength <= 160) score += 1;

    // Check if meta title exists
    if (metaTitleInput?.value) score += 1;

    // Check if meta description exists
    if (metaDescInput?.value) score += 1;

    // Calculate percentage
    const percentage = Math.round((score / maxScore) * 100);

    // Update badge
    if (percentage >= 75) {
      badge.textContent = `${percentage}% Optimized`;
      badge.className = 'ml-auto text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
    } else if (percentage >= 50) {
      badge.textContent = `${percentage}% Optimized`;
      badge.className = 'ml-auto text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
    } else {
      badge.textContent = `${percentage}% Optimized`;
      badge.className = 'ml-auto text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300';
    }
  }

  // ==================== TAG MANAGEMENT ====================

  setupTagManagement() {
    const tagInputField = document.getElementById('tag-input-field');
    const tagPillsContainer = document.getElementById('tag-pills-container');
    const originalTagInput = document.querySelector('input[name="tags_input"]');
    const autocompleteDropdown = document.getElementById('tag-autocomplete');

    console.log('Tag Management Setup:', {
      tagInputField: !!tagInputField,
      tagPillsContainer: !!tagPillsContainer,
      originalTagInput: !!originalTagInput,
      originalValue: originalTagInput?.value
    });

    if (!tagInputField || !tagPillsContainer || !originalTagInput) return;

    // State for tags
    this.tags = [];
    this.availableTags = [];

    // Load initial tags from form
    this.loadInitialTags(originalTagInput);

    // Fetch available tags from other posts
    this.fetchAvailableTags();

    // Event listeners
    tagInputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        this.addTag(tagInputField.value.trim());
        tagInputField.value = '';
        autocompleteDropdown.classList.add('hidden');
      } else if (e.key === 'Backspace' && tagInputField.value === '' && this.tags.length > 0) {
        // Remove last tag on backspace if input is empty
        this.removeTag(this.tags[this.tags.length - 1]);
      }
    });

    tagInputField.addEventListener('input', (e) => {
      const query = e.target.value.trim().toLowerCase();
      if (query.length > 0) {
        this.showAutocomplete(query);
      } else {
        autocompleteDropdown.classList.add('hidden');
      }
    });

    // Click outside to close autocomplete
    document.addEventListener('click', (e) => {
      if (!tagInputField.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
        autocompleteDropdown.classList.add('hidden');
      }
    });
  }

  loadInitialTags(originalInput) {
    if (originalInput.value) {
      const tags = originalInput.value.split(',').map(t => t.trim()).filter(t => t);
      tags.forEach(tag => this.addTag(tag, false));
      // Render all tags after loading
      if (tags.length > 0) {
        this.renderTags();
      }
    }
  }

  async fetchAvailableTags() {
    try {
      // Try to fetch from API endpoint
      const response = await fetch('/api/blog/posts/?fields=tags');
      if (response.ok) {
        const data = await response.json();
        const tagSet = new Set();
        
        data.results?.forEach(post => {
          if (post.tags && Array.isArray(post.tags)) {
            post.tags.forEach(tag => tagSet.add(tag));
          }
        });
        
        this.availableTags = Array.from(tagSet).sort();
      }
    } catch (error) {
      console.log('Could not fetch tags:', error);
      // Fallback to common tags
      this.availableTags = ['tutorial', 'announcement', 'release', 'design', 'development', 'guide', 'tips'];
    }
  }

  addTag(tagText, updateUI = true) {
    const tag = tagText.toLowerCase().trim();
    
    if (!tag || this.tags.includes(tag)) return;
    
    this.tags.push(tag);
    
    if (updateUI) {
      this.renderTags();
      this.updateOriginalInput();
    }
  }

  removeTag(tag) {
    this.tags = this.tags.filter(t => t !== tag);
    this.renderTags();
    this.updateOriginalInput();
  }

  renderTags() {
    const container = document.getElementById('tag-pills-container');
    if (!container) return;

    const colors = [
      'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
      'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300',
      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    ];

    container.innerHTML = this.tags.map((tag, index) => {
      const colorClass = colors[index % colors.length];
      return `
        <span class="tag-pill inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${colorClass} animate-in">
          <span>${tag}</span>
          <button type="button" class="tag-remove hover:bg-black/10 dark:hover:bg-white/10 rounded-full p-0.5 transition" data-tag="${tag}">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </span>
      `;
    }).join('');

    // Add click handlers to remove buttons
    container.querySelectorAll('.tag-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.removeTag(btn.dataset.tag);
      });
    });
  }

  updateOriginalInput() {
    const originalInput = document.querySelector('input[name="tags_input"]');
    if (originalInput) {
      originalInput.value = this.tags.join(', ');
    }
  }

  showAutocomplete(query) {
    const dropdown = document.getElementById('tag-autocomplete');
    if (!dropdown) return;

    const suggestions = this.availableTags
      .filter(tag => tag.toLowerCase().includes(query) && !this.tags.includes(tag))
      .slice(0, 5);

    if (suggestions.length === 0) {
      dropdown.classList.add('hidden');
      return;
    }

    dropdown.innerHTML = suggestions.map(tag => `
      <button type="button" class="tag-suggestion w-full text-left px-3 py-2 hover:bg-primary-50 dark:hover:bg-primary-950/30 text-sm transition" data-tag="${tag}">
        <span class="font-medium text-neutral-900 dark:text-neutral-100">${tag}</span>
      </button>
    `).join('');

    dropdown.classList.remove('hidden');

    // Add click handlers
    dropdown.querySelectorAll('.tag-suggestion').forEach(btn => {
      btn.addEventListener('click', () => {
        this.addTag(btn.dataset.tag);
        document.getElementById('tag-input-field').value = '';
        dropdown.classList.add('hidden');
      });
    });
  }

  // ==================== FEATURED IMAGE PREVIEW ====================

  setupImagePreview() {
    const fileInput = document.getElementById('id_featured_image');
    const dropZone = document.getElementById('image-drop-zone');
    const previewContainer = document.getElementById('featured-image-preview');
    const thumbnail = document.getElementById('featured-image-thumbnail');
    const dimensionsSpan = document.getElementById('image-dimensions');
    const removeBtn = document.getElementById('remove-featured-image');

    if (!fileInput || !dropZone) return;

    // Check if there's an existing image on page load
    this.checkExistingFeaturedImage();

    // Click to open file dialog
    dropZone.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.previewImage(file);
      }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-primary-500', 'bg-primary-50', 'dark:bg-primary-950/30');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-primary-500', 'bg-primary-50', 'dark:bg-primary-950/30');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-primary-500', 'bg-primary-50', 'dark:bg-primary-950/30');
      
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        // Set the file to the input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        this.previewImage(file);
      }
    });

    // Remove button
    if (removeBtn) {
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.removeFeaturedImage();
      });
    }
  }

  checkExistingFeaturedImage() {
    // Check if form has existing featured image (edit mode)
    const fileInput = document.getElementById('id_featured_image');
    const existingImageUrl = fileInput?.dataset.existingImage;
    
    if (existingImageUrl) {
      const thumbnail = document.getElementById('featured-image-thumbnail');
      const previewContainer = document.getElementById('featured-image-preview');
      const dropZone = document.getElementById('image-drop-zone');
      
      if (thumbnail && previewContainer) {
        thumbnail.src = existingImageUrl;
        previewContainer.classList.remove('hidden');
        if (dropZone) dropZone.classList.add('hidden');
      }
    }
  }

  previewImage(file) {
    const previewContainer = document.getElementById('featured-image-preview');
    const thumbnail = document.getElementById('featured-image-thumbnail');
    const dimensionsSpan = document.getElementById('image-dimensions');
    const dropZone = document.getElementById('image-drop-zone');

    if (!thumbnail || !previewContainer) return;

    const reader = new FileReader();
    
    reader.onload = (e) => {
      thumbnail.src = e.target.result;
      
      // Get image dimensions
      const img = new Image();
      img.onload = () => {
        const sizeKB = (file.size / 1024).toFixed(1);
        if (dimensionsSpan) {
          dimensionsSpan.textContent = `${img.width} × ${img.height} • ${sizeKB} KB`;
        }
      };
      img.src = e.target.result;
      
      // Show preview, hide drop zone
      previewContainer.classList.remove('hidden');
      if (dropZone) dropZone.classList.add('hidden');
      
      this.showToast('Image loaded! Remember to save the form.', 'success');
    };
    
    reader.readAsDataURL(file);
  }

  removeFeaturedImage() {
    const fileInput = document.getElementById('id_featured_image');
    const previewContainer = document.getElementById('featured-image-preview');
    const dropZone = document.getElementById('image-drop-zone');
    const thumbnail = document.getElementById('featured-image-thumbnail');

    if (fileInput) fileInput.value = '';
    if (thumbnail) thumbnail.src = '';
    if (previewContainer) previewContainer.classList.add('hidden');
    if (dropZone) dropZone.classList.remove('hidden');

    this.showToast('Image removed', 'info');
  }

  // ==================== VERSION HISTORY & DRAFTS ====================

  setupVersionHistory() {
    const historyBtn = document.getElementById('show-version-history');
    if (!historyBtn) return;

    historyBtn.addEventListener('click', () => this.showVersionHistoryModal());

    // Save version periodically (every 5 minutes)
    setInterval(() => {
      if (this.editor && this.state.isDirty) {
        this.saveVersion('Auto-save');
      }
    }, 5 * 60 * 1000);

    // Keyboard shortcut: Ctrl+H
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'h') {
        e.preventDefault();
        this.showVersionHistoryModal();
      }
    });
  }

  saveVersion(label = 'Manual save') {
    if (!this.editor) return;

    const version = {
      id: Date.now(),
      content: this.editor.value,
      label: label,
      timestamp: new Date().toISOString(),
      wordCount: this.stats.words,
      charCount: this.stats.characters,
    };

    // Get existing versions
    const versions = this.getVersions();
    versions.unshift(version);

    // Keep only last 20 versions
    const trimmed = versions.slice(0, 20);

    // Save to localStorage
    const key = this.getVersionStorageKey();
    localStorage.setItem(key, JSON.stringify(trimmed));

    this.showToast(`Version saved: ${label}`, 'success');
  }

  getVersions() {
    const key = this.getVersionStorageKey();
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : [];
  }

  getVersionStorageKey() {
    // Use URL path as key to separate versions per post
    const path = window.location.pathname;
    return `mdx_versions_${path}`;
  }

  deleteVersion(versionId) {
    const versions = this.getVersions().filter(v => v.id !== versionId);
    const key = this.getVersionStorageKey();
    localStorage.setItem(key, JSON.stringify(versions));
    this.showToast('Version deleted', 'info');
  }

  restoreVersion(versionId) {
    const versions = this.getVersions();
    const version = versions.find(v => v.id === versionId);
    
    if (version && this.editor) {
      this.editor.value = version.content;
      this.renderPreview();
      this.updateStats();
      this.state.isDirty = true;
      this.showToast('Version restored!', 'success');
    }
  }

  clearAllVersions() {
    if (!confirm('Delete all saved versions? This cannot be undone.')) return;
    
    const key = this.getVersionStorageKey();
    localStorage.removeItem(key);
    this.showToast('All versions cleared', 'info');
  }

  showVersionHistoryModal() {
    const versions = this.getVersions();

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-content-large">
        <div class="modal-header">
          <h3 class="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Version History
          </h3>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          ${versions.length === 0 ? `
            <div class="text-center py-12 text-neutral-500 dark:text-neutral-400">
              <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-lg font-medium">No versions saved yet</p>
              <p class="text-sm mt-2">Versions are automatically saved every 5 minutes</p>
            </div>
          ` : `
            <div class="flex justify-between items-center mb-4">
              <p class="text-sm text-neutral-600 dark:text-neutral-400">
                ${versions.length} version${versions.length !== 1 ? 's' : ''} saved
              </p>
              <button id="clear-all-versions" class="text-xs px-3 py-1 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 transition">
                Clear All
              </button>
            </div>
            <div class="version-timeline space-y-3 max-h-96 overflow-y-auto">
              ${versions.map(version => {
                const date = new Date(version.timestamp);
                const timeAgo = this.getTimeAgo(date);
                const preview = version.content.substring(0, 100) + (version.content.length > 100 ? '...' : '');
                
                return `
                  <div class="version-item border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 hover:border-purple-400 dark:hover:border-purple-600 transition">
                    <div class="flex justify-between items-start mb-2">
                      <div>
                        <p class="font-semibold text-neutral-900 dark:text-neutral-100">${version.label}</p>
                        <p class="text-xs text-neutral-500 dark:text-neutral-400">${timeAgo} • ${version.wordCount} words • ${version.charCount} chars</p>
                      </div>
                      <div class="flex gap-2">
                        <button class="restore-version text-xs px-2 py-1 rounded bg-purple-100 text-purple-700 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-400 transition" data-id="${version.id}">
                          Restore
                        </button>
                        <button class="delete-version text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 transition" data-id="${version.id}">
                          Delete
                        </button>
                      </div>
                    </div>
                    <p class="text-sm text-neutral-600 dark:text-neutral-300 font-mono bg-neutral-50 dark:bg-neutral-800 p-2 rounded">${preview}</p>
                  </div>
                `;
              }).join('')}
            </div>
          `}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });

    if (versions.length > 0) {
      modal.querySelectorAll('.restore-version').forEach(btn => {
        btn.addEventListener('click', () => {
          this.restoreVersion(parseInt(btn.dataset.id));
          modal.remove();
        });
      });

      modal.querySelectorAll('.delete-version').forEach(btn => {
        btn.addEventListener('click', () => {
          this.deleteVersion(parseInt(btn.dataset.id));
          modal.remove();
          this.showVersionHistoryModal();
        });
      });

      modal.querySelector('#clear-all-versions')?.addEventListener('click', () => {
        this.clearAllVersions();
        modal.remove();
        this.showVersionHistoryModal();
      });
    }
  }

  getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    const intervals = {
      year: 31536000,
      month: 2592000,
      week: 604800,
      day: 86400,
      hour: 3600,
      minute: 60,
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
      const interval = Math.floor(seconds / secondsInUnit);
      if (interval >= 1) {
        return `${interval} ${unit}${interval !== 1 ? 's' : ''} ago`;
      }
    }
    return 'Just now';
  }

  // ==================== LINK MANAGEMENT ====================

  setupLinkManagement() {
    if (!this.editor) return;

    // Auto-detect URLs when pasting
    this.editor.addEventListener('paste', (e) => {
      const text = e.clipboardData.getData('text');
      if (this.isValidURL(text)) {
        e.preventDefault();
        this.handlePastedURL(text);
      }
    });

    // Update link count on content change
    this.editor.addEventListener('input', () => {
      this.updateLinkCount();
    });

    // Initial count
    this.updateLinkCount();
  }

  isValidURL(string) {
    try {
      const url = new URL(string);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
      return false;
    }
  }

  handlePastedURL(url) {
    // Create markdown link format
    const linkText = `[${url}](${url})`;
    this.insertAtCursor(linkText);
    this.showToast('Link inserted!', 'success');

    // Try to fetch link preview
    this.fetchLinkPreview(url);
  }

  async fetchLinkPreview(url) {
    try {
      // Note: This would need a backend endpoint to avoid CORS
      // For now, just show the URL info
      const urlObj = new URL(url);
      const isInternal = urlObj.hostname === window.location.hostname;
      
      this.showToast(
        `${isInternal ? 'Internal' : 'External'} link: ${urlObj.hostname}`,
        isInternal ? 'success' : 'info'
      );
    } catch (error) {
      console.error('Link preview error:', error);
    }
  }

  updateLinkCount() {
    if (!this.editor) return;

    const content = this.editor.value;
    
    // Match markdown links: [text](url)
    const markdownLinks = content.match(/\[([^\]]+)\]\(([^)]+)\)/g) || [];
    
    // Match plain URLs
    const urlRegex = /https?:\/\/[^\s]+/g;
    const plainLinks = content.match(urlRegex) || [];
    
    // Remove duplicates
    const allLinks = [...new Set([...markdownLinks, ...plainLinks])];
    const linkCount = allLinks.length;

    // Update UI
    const linkCountEl = document.getElementById('link-count');
    if (linkCountEl) {
      const span = linkCountEl.querySelector('span');
      if (span) {
        span.textContent = `${linkCount} link${linkCount !== 1 ? 's' : ''}`;
      }
    }

    // Store for later use
    this.stats.linkCount = linkCount;
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

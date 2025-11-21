class TranslationApp {
    constructor() {
        this.currentModId = null;
        this.allMods = [];
        this.currentItems = [];
        this.modifications = new Map();
        this.currentFilter = 'untranslated';
        this.itemSearchTerm = '';
        this.modSearchTerm = '';

        this.init();
    }

    async init() {
        this.initTheme();
        this.bindEvents();
        await this.loadStats();
        await this.loadMods();
    }

    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        const icon = document.getElementById('themeIcon');
        icon.textContent = theme === 'light' ? '🌙' : '☀️';
    }

    bindEvents() {
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        document.getElementById('modSearch').addEventListener('input', (e) => {
            this.modSearchTerm = e.target.value.toLowerCase();
            this.renderModList();
        });

        document.getElementById('filterSelect').addEventListener('change', (e) => {
            this.currentFilter = e.target.value;
            if (this.currentModId) {
                this.loadModItems(this.currentModId);
            }
        });

        document.getElementById('itemSearch').addEventListener('input', (e) => {
            this.itemSearchTerm = e.target.value.toLowerCase();
            this.renderItems();
        });

        document.getElementById('saveButton').addEventListener('click', () => {
            this.saveTranslations();
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();

            document.getElementById('totalMods').textContent = stats.total_mods;
            document.getElementById('totalKeys').textContent = stats.total_keys;
            document.getElementById('totalTranslated').textContent = stats.total_translated;
            document.getElementById('totalUntranslated').textContent = stats.total_untranslated;
            document.getElementById('progressPercentage').textContent = `${stats.progress_percentage}%`;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async loadMods() {
        try {
            const response = await fetch('/api/mods');
            this.allMods = await response.json();
            this.renderModList();
        } catch (error) {
            console.error('Failed to load mods:', error);
            this.showNotification('Failed to load mods', 'error');
        }
    }

    renderModList() {
        const modList = document.getElementById('modList');
        const filteredMods = this.allMods.filter(mod =>
            mod.mod_id.toLowerCase().includes(this.modSearchTerm)
        );

        if (filteredMods.length === 0) {
            modList.innerHTML = '<div class="loading">No mods found</div>';
            return;
        }

        modList.innerHTML = filteredMods.map(mod => `
            <div class="mod-item ${mod.mod_id === this.currentModId ? 'active' : ''}"
                 data-mod-id="${mod.mod_id}">
                <div class="mod-name">${this.escapeHtml(mod.mod_id)}</div>
                <div class="mod-stats">
                    <span>${mod.total_keys} keys</span>
                    ${mod.untranslated_count > 0
                        ? `<span class="badge badge-warning">${mod.untranslated_count} untranslated</span>`
                        : `<span class="badge badge-success">Complete</span>`
                    }
                </div>
            </div>
        `).join('');

        modList.querySelectorAll('.mod-item').forEach(item => {
            item.addEventListener('click', () => {
                const modId = item.dataset.modId;
                this.loadModItems(modId);
            });
        });
    }

    async loadModItems(modId) {
        if (this.modifications.size > 0) {
            if (!confirm('You have unsaved changes. Do you want to discard them?')) {
                return;
            }
        }

        this.currentModId = modId;
        this.modifications.clear();
        this.updateSaveButton();
        this.renderModList();

        document.getElementById('currentModId').textContent = modId;
        document.getElementById('editorContent').innerHTML = '<div class="loading">Loading translations...</div>';

        try {
            const response = await fetch(`/api/mods/${modId}?filter=${this.currentFilter}`);
            const data = await response.json();
            this.currentItems = data.items;
            this.renderItems();
        } catch (error) {
            console.error('Failed to load mod items:', error);
            this.showNotification('Failed to load translations', 'error');
        }
    }

    renderItems() {
        const editorContent = document.getElementById('editorContent');

        let filteredItems = this.currentItems;
        if (this.itemSearchTerm) {
            filteredItems = this.currentItems.filter(item =>
                item.key.toLowerCase().includes(this.itemSearchTerm) ||
                item.english.toLowerCase().includes(this.itemSearchTerm) ||
                item.chinese.toLowerCase().includes(this.itemSearchTerm)
            );
        }

        if (filteredItems.length === 0) {
            editorContent.innerHTML = '<div class="loading">No items to display</div>';
            return;
        }

        editorContent.innerHTML = filteredItems.map(item => {
            const currentValue = this.modifications.has(item.key)
                ? this.modifications.get(item.key)
                : item.chinese;
            const isModified = this.modifications.has(item.key);

            return `
                <div class="translation-item ${isModified ? 'modified' : ''}" data-key="${this.escapeHtml(item.key)}">
                    <div class="translation-key">${this.escapeHtml(item.key)}</div>
                    <div class="translation-content">
                        <div class="translation-field">
                            <div class="translation-label">English</div>
                            <div class="translation-value">${this.escapeHtml(item.english)}</div>
                        </div>
                        <div class="translation-field">
                            <div class="translation-label">Chinese</div>
                            <textarea
                                class="translation-input"
                                data-key="${this.escapeHtml(item.key)}"
                                placeholder="Enter Chinese translation..."
                            >${this.escapeHtml(currentValue)}</textarea>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        editorContent.querySelectorAll('.translation-input').forEach(input => {
            input.addEventListener('input', (e) => {
                this.handleTranslationChange(e.target.dataset.key, e.target.value);
            });
        });
    }

    handleTranslationChange(key, value) {
        const originalItem = this.currentItems.find(item => item.key === key);
        if (!originalItem) return;

        if (value !== originalItem.chinese) {
            this.modifications.set(key, value);
        } else {
            this.modifications.delete(key);
        }

        this.updateSaveButton();
        this.updateItemModifiedState(key);
    }

    updateItemModifiedState(key) {
        const item = document.querySelector(`.translation-item[data-key="${this.escapeAttribute(key)}"]`);
        if (item) {
            if (this.modifications.has(key)) {
                item.classList.add('modified');
            } else {
                item.classList.remove('modified');
            }
        }
    }

    updateSaveButton() {
        const saveButton = document.getElementById('saveButton');
        saveButton.disabled = this.modifications.size === 0;
        saveButton.textContent = this.modifications.size > 0
            ? `Save ${this.modifications.size} Changes`
            : 'Save Translations';
    }

    async saveTranslations() {
        if (this.modifications.size === 0 || !this.currentModId) {
            return;
        }

        const saveButton = document.getElementById('saveButton');
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';

        try {
            const translations = Object.fromEntries(this.modifications);
            const response = await fetch(`/api/mods/${this.currentModId}/translations`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ translations }),
            });

            if (!response.ok) {
                throw new Error('Failed to save translations');
            }

            this.showNotification('Translations saved successfully', 'success');

            this.currentItems = this.currentItems.map(item => {
                if (this.modifications.has(item.key)) {
                    return { ...item, chinese: this.modifications.get(item.key) };
                }
                return item;
            });

            this.modifications.clear();
            this.updateSaveButton();

            await this.loadStats();
            await this.loadMods();

            this.renderItems();
        } catch (error) {
            console.error('Failed to save translations:', error);
            this.showNotification('Failed to save translations', 'error');
        } finally {
            saveButton.disabled = false;
            this.updateSaveButton();
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;

        setTimeout(() => notification.classList.add('show'), 10);

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeAttribute(text) {
        return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TranslationApp();
});

"""
📋 Drag-and-Drop Kanban Board — Custom Gradio Component (Enhanced)
A fully interactive Kanban board with drag-and-drop, inline editing,
priority labels, search/filter, column collapse, and more.
Built entirely with gr.HTML for Gradio 6.
"""
import gradio as gr
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr
import json

load_dotenv()  # loads OPENAI_API_KEY from your .env file automatically

# ─── Component ────────────────────────────────────────────────────

HTML_TEMPLATE = """
<div class="kanban-wrapper">
    <div class="kanban-header">
        <h2>${board_title}</h2>
        <div class="header-right">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" class="search-input" placeholder="Search cards..." />
            </div>
            <div class="header-stats">
                ${(() => {
                    const cols = (value && value.columns) || [];
                    const total = cols.reduce((sum, col) => sum + col.cards.length, 0);
                    const done = cols.find(c => c.id === 'done');
                    const doneCount = done ? done.cards.length : 0;
                    const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
                    return '<span class="stat-pill">📊 ' + total + ' tasks</span>' +
                           '<span class="stat-pill done-pill">✅ ' + doneCount + ' done (' + pct + '%)</span>';
                })()}
            </div>
        </div>
    </div>

    <div class="progress-track">
        ${(() => {
            const cols = (value && value.columns) || [];
            const total = cols.reduce((sum, col) => sum + col.cards.length, 0);
            const done = cols.find(c => c.id === 'done');
            const doneCount = done ? done.cards.length : 0;
            const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
            return '<div class="progress-bar" style="width: ' + pct + '%"></div>';
        })()}
    </div>

    <div class="kanban-board">
        ${((value && value.columns) || []).map((col, colIdx) => `
            <div class="kanban-column ${col.collapsed ? 'collapsed' : ''}" data-col-idx="${colIdx}" data-col-id="${col.id}">
                <div class="column-header" style="border-top: 3px solid ${col.color}">
                    <div class="col-header-left">
                        <button class="collapse-btn" data-col-idx="${colIdx}">${col.collapsed ? '▶' : '▼'}</button>
                        <span class="col-title">${col.title}</span>
                    </div>
                    <span class="col-count" style="background: ${col.color}22; color: ${col.color}">${col.cards.length}</span>
                </div>
                <div class="card-list ${col.collapsed ? 'hidden' : ''}" data-col-idx="${colIdx}">
                    ${col.cards.map((card, cardIdx) => `
                        <div class="kanban-card" draggable="true" data-col-idx="${colIdx}" data-card-idx="${cardIdx}" data-card-id="${card.id}">
                            <div class="card-priority priority-${card.priority}"></div>
                            <div class="card-content">
                                <div class="card-text" data-col-idx="${colIdx}" data-card-idx="${cardIdx}">${card.text}</div>
                                <div class="card-footer">
                                    <div class="card-tags">
                                        ${(card.tags || []).map(t => '<span class="tag">' + t + '</span>').join('')}
                                    </div>
                                    <div class="card-actions">
                                        <button class="priority-cycle" data-col-idx="${colIdx}" data-card-idx="${cardIdx}" title="Cycle priority">
                                            ${card.priority === 'high' ? '🔴' : card.priority === 'medium' ? '🟡' : '🟢'}
                                        </button>
                                        <button class="delete-card" data-col-idx="${colIdx}" data-card-idx="${cardIdx}" title="Delete card">✕</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="add-card-area ${col.collapsed ? 'hidden' : ''}">
                    <input type="text" class="add-card-input" data-col-idx="${colIdx}" placeholder="+ Add a card…  ⏎" />
                </div>
            </div>
        `).join('')}
    </div>
</div>
"""

CSS_TEMPLATE = """
    .kanban-wrapper {
        background: linear-gradient(135deg, #0f172a 0%, #1a1a2e 100%);
        border-radius: 16px;
        padding: 24px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #e2e8f0;
        overflow-x: auto;
    }
    .kanban-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        flex-wrap: wrap;
        gap: 12px;
    }
    .kanban-header h2 { margin: 0; font-size: 22px; color: #f8fafc; letter-spacing: -0.3px; }
    .header-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

    .search-box {
        display: flex;
        align-items: center;
        background: rgba(255,255,255,0.06);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 4px 12px;
        transition: all 0.2s;
    }
    .search-box:focus-within { border-color: #6366f1; background: rgba(99, 102, 241, 0.06); }
    .search-icon { font-size: 13px; margin-right: 6px; }
    .search-input {
        background: none;
        border: none;
        color: #e2e8f0;
        font-size: 13px;
        outline: none;
        width: 140px;
    }
    .search-input::placeholder { color: #475569; }

    .header-stats { display: flex; gap: 8px; }
    .stat-pill {
        background: rgba(255,255,255,0.08);
        padding: 5px 14px;
        border-radius: 12px;
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
    }
    .done-pill { color: #10b981; }

    .progress-track {
        height: 4px;
        background: rgba(255,255,255,0.08);
        border-radius: 4px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #6366f1, #10b981);
        border-radius: 4px;
        transition: width 0.5s ease;
    }

    .kanban-board {
        display: flex;
        gap: 16px;
        min-height: 400px;
        padding-bottom: 8px;
    }
    .kanban-column {
        background: #1e293b;
        border-radius: 12px;
        min-width: 270px;
        max-width: 310px;
        flex: 1;
        display: flex;
        flex-direction: column;
        transition: min-width 0.3s, max-width 0.3s;
    }
    .kanban-column.collapsed {
        min-width: 60px;
        max-width: 60px;
    }
    .column-header {
        padding: 14px 14px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 12px 12px 0 0;
        user-select: none;
    }
    .col-header-left { display: flex; align-items: center; gap: 8px; }
    .collapse-btn {
        background: none;
        border: none;
        color: #64748b;
        cursor: pointer;
        font-size: 10px;
        padding: 2px 4px;
        border-radius: 4px;
        transition: color 0.2s;
    }
    .collapse-btn:hover { color: #e2e8f0; }
    .col-title { font-weight: 600; font-size: 14px; white-space: nowrap; }
    .col-count {
        min-width: 26px;
        height: 26px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
    }

    .card-list {
        flex: 1;
        padding: 6px 10px;
        min-height: 60px;
        transition: background 0.2s;
    }
    .card-list.hidden, .add-card-area.hidden { display: none; }
    .card-list.drag-over {
        background: rgba(99, 102, 241, 0.08);
        border-radius: 8px;
    }

    .kanban-card {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 12px 12px 16px;
        margin-bottom: 8px;
        cursor: grab;
        transition: all 0.15s ease;
        position: relative;
        overflow: hidden;
    }
    .kanban-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .kanban-card.dragging {
        opacity: 0.4;
        transform: rotate(2deg) scale(0.97);
    }
    .kanban-card.search-hidden { display: none; }
    .kanban-card.search-highlight { border-color: #f59e0b; box-shadow: 0 0 0 1px #f59e0b44; }

    .card-priority {
        width: 4px;
        height: 100%;
        position: absolute;
        left: 0;
        top: 0;
        border-radius: 10px 0 0 10px;
    }
    .priority-high { background: #ef4444; }
    .priority-medium { background: #f59e0b; }
    .priority-low { background: #10b981; }

    .card-content { padding-left: 4px; }
    .card-text {
        font-size: 13px;
        line-height: 1.5;
        color: #e2e8f0;
        cursor: text;
        border-radius: 4px;
        padding: 2px 4px;
        margin: -2px -4px;
        transition: background 0.15s;
    }
    .card-text:hover { background: rgba(255,255,255,0.04); }
    .card-text.editing {
        background: rgba(99, 102, 241, 0.1);
        outline: 1px solid #6366f1;
        min-height: 1.5em;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
    }
    .card-tags { display: flex; gap: 4px; flex-wrap: wrap; }
    .tag {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 2px 9px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
    }
    .card-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.15s; }
    .kanban-card:hover .card-actions { opacity: 1; }
    .priority-cycle, .delete-card {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 13px;
        padding: 3px 6px;
        border-radius: 6px;
        transition: all 0.15s;
        color: #475569;
    }
    .delete-card:hover { color: #ef4444; background: rgba(239, 68, 68, 0.1); }
    .priority-cycle:hover { background: rgba(255,255,255,0.08); }

    .add-card-area { padding: 6px 10px 14px; }
    .add-card-input {
        width: 100%;
        background: rgba(255,255,255,0.04);
        border: 1px dashed #334155;
        border-radius: 10px;
        padding: 10px 14px;
        color: #94a3b8;
        font-size: 13px;
        outline: none;
        transition: all 0.2s;
        box-sizing: border-box;
    }
    .add-card-input:focus {
        border-color: #6366f1;
        border-style: solid;
        background: rgba(99, 102, 241, 0.05);
        color: #e2e8f0;
    }
    .add-card-input::placeholder { color: #475569; }

    @keyframes cardIn {
        from { opacity: 0; transform: translateY(-8px) scale(0.97); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    .kanban-card { animation: cardIn 0.2s ease; }
"""

JS_ON_LOAD = """
    let dragSrcColIdx = null;
    let dragSrcCardIdx = null;

    // ── Drag & Drop ──────────────────────────────
    element.addEventListener('dragstart', (e) => {
        const card = e.target.closest('.kanban-card');
        if (!card) return;
        dragSrcColIdx = parseInt(card.dataset.colIdx);
        dragSrcCardIdx = parseInt(card.dataset.cardIdx);
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    });

    element.addEventListener('dragend', (e) => {
        const card = e.target.closest('.kanban-card');
        if (card) card.classList.remove('dragging');
        element.querySelectorAll('.card-list').forEach(cl => cl.classList.remove('drag-over'));
    });

    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        const cardList = e.target.closest('.card-list');
        if (cardList) cardList.classList.add('drag-over');
    });

    element.addEventListener('dragleave', (e) => {
        const cardList = e.target.closest('.card-list');
        if (cardList && !cardList.contains(e.relatedTarget)) {
            cardList.classList.remove('drag-over');
        }
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        const cardList = e.target.closest('.card-list');
        if (!cardList || dragSrcColIdx === null) return;
        cardList.classList.remove('drag-over');

        const destColIdx = parseInt(cardList.dataset.colIdx);
        const nv = JSON.parse(JSON.stringify(props.value));
        const card = nv.columns[dragSrcColIdx].cards.splice(dragSrcCardIdx, 1)[0];

        const cardElements = cardList.querySelectorAll('.kanban-card:not(.dragging)');
        let insertIdx = nv.columns[destColIdx].cards.length;
        for (let i = 0; i < cardElements.length; i++) {
            const rect = cardElements[i].getBoundingClientRect();
            if (e.clientY < rect.top + rect.height / 2) {
                insertIdx = i;
                break;
            }
        }

        nv.columns[destColIdx].cards.splice(insertIdx, 0, card);
        props.value = nv;
        trigger('change');
        dragSrcColIdx = null;
        dragSrcCardIdx = null;
    });

    // ── Delete card ──────────────────────────────
    element.addEventListener('click', (e) => {
        const delBtn = e.target.closest('.delete-card');
        if (!delBtn) return;
        e.stopPropagation();
        const colIdx = parseInt(delBtn.dataset.colIdx);
        const cardIdx = parseInt(delBtn.dataset.cardIdx);
        const nv = JSON.parse(JSON.stringify(props.value));
        nv.columns[colIdx].cards.splice(cardIdx, 1);
        props.value = nv;
        trigger('change');
    });

    // ── Cycle priority ───────────────────────────
    element.addEventListener('click', (e) => {
        const btn = e.target.closest('.priority-cycle');
        if (!btn) return;
        e.stopPropagation();
        const colIdx = parseInt(btn.dataset.colIdx);
        const cardIdx = parseInt(btn.dataset.cardIdx);
        const nv = JSON.parse(JSON.stringify(props.value));
        const card = nv.columns[colIdx].cards[cardIdx];
        const cycle = { low: 'medium', medium: 'high', high: 'low' };
        card.priority = cycle[card.priority] || 'low';
        props.value = nv;
        trigger('change');
    });

    // ── Collapse column ──────────────────────────
    element.addEventListener('click', (e) => {
        const btn = e.target.closest('.collapse-btn');
        if (!btn) return;
        const colIdx = parseInt(btn.dataset.colIdx);
        const nv = JSON.parse(JSON.stringify(props.value));
        nv.columns[colIdx].collapsed = !nv.columns[colIdx].collapsed;
        props.value = nv;
        trigger('change');
    });

    // ── Inline edit (double-click) ───────────────
    element.addEventListener('dblclick', (e) => {
        const textEl = e.target.closest('.card-text');
        if (!textEl) return;
        textEl.contentEditable = 'true';
        textEl.classList.add('editing');
        textEl.focus();

        // select all text
        const range = document.createRange();
        range.selectNodeContents(textEl);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    });

    // commit on blur or Enter
    function commitEdit(textEl) {
        textEl.contentEditable = 'false';
        textEl.classList.remove('editing');
        const colIdx = parseInt(textEl.dataset.colIdx);
        const cardIdx = parseInt(textEl.dataset.cardIdx);
        const newText = textEl.innerText.trim();
        if (!newText) return;
        const nv = JSON.parse(JSON.stringify(props.value));
        nv.columns[colIdx].cards[cardIdx].text = newText;
        props.value = nv;
        trigger('change');
    }

    element.addEventListener('blur', (e) => {
        if (e.target.classList && e.target.classList.contains('editing')) {
            commitEdit(e.target);
        }
    }, true);

    element.addEventListener('keydown', (e) => {
        // commit inline edit on Enter
        if (e.key === 'Enter' && e.target.classList.contains('editing')) {
            e.preventDefault();
            e.target.blur();
            return;
        }

        // add card on Enter
        if (e.key === 'Enter' && e.target.classList.contains('add-card-input')) {
            const text = e.target.value.trim();
            if (!text) return;
            const colIdx = parseInt(e.target.dataset.colIdx);
            const nv = JSON.parse(JSON.stringify(props.value));
            nv.columns[colIdx].cards.push({
                id: String(Date.now()),
                text: text,
                priority: 'medium',
                tags: []
            });
            props.value = nv;
            e.target.value = '';
            trigger('change');
        }
    });

    // ── Search / filter ──────────────────────────
    element.addEventListener('input', (e) => {
        if (!e.target.classList.contains('search-input')) return;
        const q = e.target.value.toLowerCase().trim();
        element.querySelectorAll('.kanban-card').forEach(card => {
            const text = card.querySelector('.card-text').innerText.toLowerCase();
            const tags = Array.from(card.querySelectorAll('.tag')).map(t => t.innerText.toLowerCase()).join(' ');
            const match = !q || text.includes(q) || tags.includes(q);
            card.classList.toggle('search-hidden', !match);
            card.classList.toggle('search-highlight', !!q && match);
        });
    });
    // ── Voice Control ─────────────────────────────────────────────
    (function setupVoice() {
        // Create the mic button
        const micBtn = document.createElement('button');
        micBtn.id = 'mic-btn';
        micBtn.innerText = '🎤';
        micBtn.title = 'Click and speak a command';
        micBtn.style.cssText = `
            position: fixed;
            bottom: 32px;
            right: 32px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: none;
            background: #6366f1;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(99,102,241,0.5);
            transition: all 0.2s;
            z-index: 9999;
        `;
        document.body.appendChild(micBtn);

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            micBtn.title = 'Speech recognition not supported in this browser (use Chrome/Edge)';
            micBtn.style.background = '#475569';
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        let listening = false;

        micBtn.addEventListener('click', () => {
            if (listening) return;
            listening = true;
            micBtn.innerText = '🔴';
            micBtn.style.background = '#ef4444';
            micBtn.style.boxShadow = '0 4px 20px rgba(239,68,68,0.6)';
            recognition.start();
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;

            // Show processing state
            micBtn.innerText = '⏳';
            micBtn.style.background = '#f59e0b';
            micBtn.style.boxShadow = '0 4px 20px rgba(245,158,11,0.6)';

            // 1. Find the visible textbox by elem_id and set its value
            const voiceBox = document.querySelector('#voice-input textarea, #voice-input input');
            if (!voiceBox) {
                console.error('voice-input element not found');
                micBtn.innerText = '🎤';
                micBtn.style.background = '#ef4444';
                return;
            }

            // Svelte requires the native setter, not direct .value assignment
            const setter = Object.getOwnPropertyDescriptor(
                Object.getPrototypeOf(voiceBox), 'value'
            ).set;
            setter.call(voiceBox, transcript);
            voiceBox.dispatchEvent(new Event('input', { bubbles: true }));

            // 2. Click the Execute button after a short delay so Svelte processes the input value first
            setTimeout(() => {
                // Try multiple selectors — Gradio 6 may apply elem_id to the button itself or a wrapper
                const executeBtn = document.querySelector('#execute-btn')
                                || document.querySelector('#execute-btn button')
                                || Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim().includes('Execute'));
                if (executeBtn) {
                    executeBtn.click();
                } else {
                    console.error('execute-btn not found');
                }
                // Reset mic button after a generous timeout (Python call takes ~2-4s)
                setTimeout(() => {
                    micBtn.innerText = '🎤';
                    micBtn.style.background = '#6366f1';
                    micBtn.style.boxShadow = '0 4px 20px rgba(99,102,241,0.5)';
                    listening = false;
                }, 8000);
            }, 300);
        };

        recognition.onend = () => {
            listening = false;
        };

        recognition.onerror = (event) => {
            listening = false;
            micBtn.innerText = '🎤';
            micBtn.style.background = '#6366f1';
            micBtn.style.boxShadow = '0 4px 20px rgba(99,102,241,0.5)';
            console.error('Speech recognition error:', event.error);
        };
    })();
"""


class KanbanBoard(gr.HTML):
    """A drag-and-drop Kanban board component."""

    def __init__(self, value=None, board_title="My Board", **kwargs):
        if value is None:
            value = {
                "columns": [
                    {
                        "id": "todo",
                        "title": "📋 To Do",
                        "color": "#6366f1",
                        "cards": [
                            {"id": "1", "text": "Research gr.HTML component", "priority": "high", "tags": ["gradio"]},
                            {"id": "2", "text": "Design the UI layout", "priority": "medium", "tags": ["design"]},
                            {"id": "3", "text": "Write documentation", "priority": "low", "tags": ["docs"]},
                        ],
                    },
                    {
                        "id": "progress",
                        "title": "🔨 In Progress",
                        "color": "#f59e0b",
                        "cards": [
                            {"id": "4", "text": "Build Kanban prototype", "priority": "high", "tags": ["dev"]},
                        ],
                    },
                    {
                        "id": "review",
                        "title": "👀 Review",
                        "color": "#8b5cf6",
                        "cards": [],
                    },
                    {
                        "id": "done",
                        "title": "✅ Done",
                        "color": "#10b981",
                        "cards": [
                            {"id": "5", "text": "Set up Gradio project", "priority": "medium", "tags": ["setup"]},
                        ],
                    },
                ],
            }

        super().__init__(
            value=value,
            board_title=board_title,
            html_template=HTML_TEMPLATE,
            css_template=CSS_TEMPLATE,
            js_on_load=JS_ON_LOAD,
            **kwargs,
        )

    def api_info(self):
        return {"type": "object", "description": "Kanban board state with columns and cards"}


# ─── Preset Boards ────────────────────────────────────────────────

PRESET_BOARDS = {
    "🚀 Product Launch": {
        "columns": [
            {
                "id": "backlog",
                "title": "📦 Backlog",
                "color": "#6366f1",
                "cards": [
                    {"id": "1", "text": "Market research & competitor analysis", "priority": "high", "tags": ["research"]},
                    {"id": "2", "text": "Define target audience personas", "priority": "high", "tags": ["strategy"]},
                    {"id": "3", "text": "Create pricing strategy", "priority": "medium", "tags": ["pricing"]},
                ],
            },
            {
                "id": "progress",
                "title": "🔨 In Progress",
                "color": "#f59e0b",
                "cards": [
                    {"id": "4", "text": "Build landing page", "priority": "high", "tags": ["dev", "design"]},
                    {"id": "5", "text": "Write launch blog post", "priority": "medium", "tags": ["content"]},
                ],
            },
            {
                "id": "review",
                "title": "👀 Review",
                "color": "#8b5cf6",
                "cards": [
                    {"id": "6", "text": "Product demo video", "priority": "medium", "tags": ["marketing"]},
                ],
            },
            {
                "id": "done",
                "title": "✅ Done",
                "color": "#10b981",
                "cards": [
                    {"id": "7", "text": "Set up analytics tracking", "priority": "low", "tags": ["analytics"]},
                    {"id": "8", "text": "Configure CI/CD pipeline", "priority": "medium", "tags": ["devops"]},
                ],
            },
        ],
    },
    "🎓 Study Plan": {
        "columns": [
            {
                "id": "topics",
                "title": "📚 Topics to Study",
                "color": "#6366f1",
                "cards": [
                    {"id": "1", "text": "Linear Algebra fundamentals", "priority": "high", "tags": ["math"]},
                    {"id": "2", "text": "Neural Network architectures", "priority": "high", "tags": ["ML"]},
                    {"id": "3", "text": "Transformer attention mechanisms", "priority": "medium", "tags": ["NLP"]},
                    {"id": "4", "text": "Diffusion models theory", "priority": "low", "tags": ["GenAI"]},
                ],
            },
            {
                "id": "studying",
                "title": "📖 Currently Studying",
                "color": "#f59e0b",
                "cards": [
                    {"id": "5", "text": "Backpropagation & chain rule", "priority": "high", "tags": ["math", "ML"]},
                ],
            },
            {
                "id": "practice",
                "title": "🧪 Needs Practice",
                "color": "#8b5cf6",
                "cards": [
                    {"id": "6", "text": "Implement CNN from scratch", "priority": "medium", "tags": ["coding"]},
                ],
            },
            {
                "id": "mastered",
                "title": "🏆 Mastered",
                "color": "#10b981",
                "cards": [
                    {"id": "7", "text": "Python basics & NumPy", "priority": "low", "tags": ["coding"]},
                    {"id": "8", "text": "Data preprocessing pipelines", "priority": "low", "tags": ["data"]},
                ],
            },
        ],
    },
    "🐛 Bug Tracker": {
        "columns": [
            {
                "id": "reported",
                "title": "🐛 Reported",
                "color": "#ef4444",
                "cards": [
                    {"id": "1", "text": "Login page crashes on Safari", "priority": "high", "tags": ["frontend", "P0"]},
                    {"id": "2", "text": "API timeout on large payloads", "priority": "high", "tags": ["backend", "P0"]},
                    {"id": "3", "text": "Dark mode text contrast issues", "priority": "low", "tags": ["a11y"]},
                ],
            },
            {
                "id": "investigating",
                "title": "🔬 Investigating",
                "color": "#f59e0b",
                "cards": [
                    {"id": "4", "text": "Memory leak in dashboard", "priority": "high", "tags": ["perf"]},
                ],
            },
            {
                "id": "fixing",
                "title": "🔧 Fixing",
                "color": "#6366f1",
                "cards": [
                    {"id": "5", "text": "CSV export encoding bug", "priority": "medium", "tags": ["data"]},
                ],
            },
            {
                "id": "done",
                "title": "✅ Resolved",
                "color": "#10b981",
                "cards": [
                    {"id": "6", "text": "Fix email notification delay", "priority": "medium", "tags": ["infra"]},
                    {"id": "7", "text": "Patch XSS vulnerability", "priority": "high", "tags": ["security"]},
                ],
            },
        ],
    },
    "🏠 Empty Board": {
        "columns": [
            {"id": "todo", "title": "📋 To Do", "color": "#6366f1", "cards": []},
            {"id": "progress", "title": "🔨 In Progress", "color": "#f59e0b", "cards": []},
            {"id": "review", "title": "👀 Review", "color": "#8b5cf6", "cards": []},
            {"id": "done", "title": "✅ Done", "color": "#10b981", "cards": []},
        ],
    },
}


# ─── Helper functions (LESSONS.md #1: always return gr.HTML, not subclass) ───

def _load_preset(preset, title):
    """Load a preset board. Returns gr.HTML() update, NOT KanbanBoard()."""
    data = PRESET_BOARDS.get(preset, PRESET_BOARDS["🏠 Empty Board"])
    total = sum(len(col["cards"]) for col in data["columns"])
    return (
        gr.HTML(value=data, board_title=title),
        f"Loaded '{preset}' — {total} cards across {len(data['columns'])} columns",
    )


def _update_title(title, board_val):
    """Update board title. Returns gr.HTML() update, NOT KanbanBoard()."""
    return gr.HTML(board_title=title)


def _on_board_change(board_val):
    """Compute status text from board state."""
    if isinstance(board_val, dict) and "columns" in board_val:
        cols = board_val["columns"]
        parts = [f"{col.get('title', '?')}: {len(col.get('cards', []))}" for col in cols]
        total = sum(len(col.get("cards", [])) for col in cols)
        done = next((col for col in cols if col.get("id") == "done"), None)
        done_count = len(done.get("cards", [])) if done else 0
        pct = round((done_count / total) * 100) if total > 0 else 0
        return f"📊 {total} total — {pct}% complete  ·  " + "  |  ".join(parts)
    return ""


def parse_voice_command(transcript: str, board_state: dict) -> dict:
    """
    Send the transcript + current board state to OpenAI.
    Returns a structured action dict.
    """
    client = OpenAI()  # automatically picks up OPENAI_API_KEY from environment

    # Build a readable summary of what cards exist on the board
    card_list = []
    for col in board_state.get("columns", []):
        for card in col.get("cards", []):
            card_list.append(f'"{card["text"]}" (in {col["title"]}, id={col["id"]})')
    cards_text = "\n".join(card_list) if card_list else "No cards yet."

    column_names = [
        f'{col["title"]} (id={col["id"]})'
        for col in board_state.get("columns", [])
    ]

    system_prompt = f"""You control a Kanban board. The board has these columns:
{chr(10).join(column_names)}

Current cards on the board:
{cards_text}

The user will give you a voice command. Return ONLY valid JSON — no explanation, no markdown, just raw JSON.

Use one of these schemas depending on what the user wants:

Add a card:
{{"action": "add", "text": "card text here", "column": "<column id>", "priority": "low|medium|high"}}

Move a card:
{{"action": "move", "card": "fuzzy card name", "to": "<column id>"}}

Delete a card:
{{"action": "delete", "card": "fuzzy card name"}}

Change priority:
{{"action": "priority", "card": "fuzzy card name", "priority": "low|medium|high"}}

Command not understood:
{{"action": "unknown", "message": "what you heard and why you could not parse it"}}

Rules:
- For "column" and "to" fields, use the column ID (e.g. "todo", "progress", "review", "done") — not the display title.
- For card names, use the closest match from the current card list. Fuzzy matching is fine.
- If the user says "in progress" map it to the column with "progress" in its id.
- If the user says "to do" map it to the column with "todo" in its id.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        response_format={"type": "json_object"},  # forces valid JSON output, no markdown wrapping
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

def action_dispatcher(action: dict, board_state: dict) -> tuple[dict, str]:
    """
    Execute the action returned by Claude on the board state.
    Returns (updated_board_state, status_message).
    """
    import copy, uuid
    state = copy.deepcopy(board_state)
    cols = state["columns"]

    act = action.get("action")

    # ── ADD ──────────────────────────────────────────────────────────
    if act == "add":
        target_col = next((c for c in cols if c["id"] == action.get("column")), None)
        if target_col is None:
            return state, f"Could not find column '{action.get('column')}'"
        target_col["cards"].append({
            "id": str(uuid.uuid4())[:8],
            "text": action["text"],
            "priority": action.get("priority", "medium"),
            "tags": [],
        })
        return state, f"Added \"{action['text']}\" to {target_col['title']}"

    # ── MOVE ─────────────────────────────────────────────────────────
    elif act == "move":
        card, src_col = _find_card(cols, action.get("card", ""))
        if card is None:
            return state, f"Could not find card matching \"{action.get('card')}\""
        dest_col = next((c for c in cols if c["id"] == action.get("to")), None)
        if dest_col is None:
            return state, f"Could not find destination column '{action.get('to')}'"
        src_col["cards"].remove(card)
        dest_col["cards"].append(card)
        return state, f"Moved \"{card['text']}\" → {dest_col['title']}"

    # ── DELETE ───────────────────────────────────────────────────────
    elif act == "delete":
        card, src_col = _find_card(cols, action.get("card", ""))
        if card is None:
            return state, f"Could not find card matching \"{action.get('card')}\""
        src_col["cards"].remove(card)
        return state, f"Deleted \"{card['text']}\""

    # ── PRIORITY ─────────────────────────────────────────────────────
    elif act == "priority":
        card, _ = _find_card(cols, action.get("card", ""))
        if card is None:
            return state, f"Could not find card matching \"{action.get('card')}\""
        card["priority"] = action.get("priority", "medium")
        return state, f"Set \"{card['text']}\" priority to {card['priority']}"

    # ── UNKNOWN ──────────────────────────────────────────────────────
    elif act == "unknown":
        return state, f"Not understood: {action.get('message', '')}"

    return state, f"Unknown action: {act}"

def handle_voice(transcript: str, board_state: dict):
    """
    Main handler: transcript → OpenAI → action → updated board.
    Called automatically by Gradio when voice_input changes.
    """
    if not transcript or not transcript.strip():
        return gr.HTML(), "Ready. Click the mic and speak."

    try:
        action = parse_voice_command(transcript, board_state)
        new_state, status_msg = action_dispatcher(action, board_state)
        return gr.HTML(value=new_state), f'Heard: "{transcript}" → {status_msg}'
    except json.JSONDecodeError:
        return gr.HTML(), f'OpenAI returned invalid JSON for: "{transcript}"'
    except Exception as e:
        return gr.HTML(), f"Error: {str(e)}"

def _find_card(cols, fuzzy_name):
    """
    Find a card by fuzzy name match across all columns.
    Returns (card_dict, column_dict) or (None, None).
    """
    fuzzy = fuzzy_name.lower()
    best_card = None
    best_col = None
    best_score = 0

    for col in cols:
        for card in col["cards"]:
            card_text = card["text"].lower()
            # score: full match > partial match > substring
            if card_text == fuzzy:
                return card, col  # exact match, stop immediately
            elif fuzzy in card_text or card_text in fuzzy:
                score = len(set(fuzzy.split()) & set(card_text.split()))
                if score > best_score:
                    best_score = score
                    best_card = card
                    best_col = col

    return best_card, best_col

# ─── App (LESSONS.md #4: theme goes in launch(), not Blocks()) ───

with gr.Blocks(title="Voice Kanban Board") as demo:

    board = KanbanBoard(board_title="My Project Board")

    with gr.Row():
        # Visible textbox — shows the transcript so the user can see what was heard
        # JS also fills this when mic captures speech
        voice_input = gr.Textbox(
            label="Voice Command",
            placeholder="Click the mic and speak, or type a command here and press Enter...",
            elem_id="voice-input",
            scale=5,
        )
        # Button — JS clicks this after filling the textbox; Gradio handles it natively
        execute_btn = gr.Button("▶ Execute", variant="primary", scale=1, elem_id="execute-btn")

    status = gr.Textbox(label="AI Status", interactive=False, value="Ready. Click the mic and speak.")

    execute_btn.click(fn=handle_voice, inputs=[voice_input, board], outputs=[board, status])
    voice_input.submit(fn=handle_voice, inputs=[voice_input, board], outputs=[board, status])
    board.change(fn=_on_board_change, inputs=board, outputs=status)


if __name__ == "__main__":
    demo.launch(theme="ocean")
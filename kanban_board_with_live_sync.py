"""
Kanban Board with Shared State
- UI auto-refreshes every 2 seconds from shared JSON file
- Python client can write to the same file
- Changes appear in browser automatically
"""

import gradio as gr
import json
from pathlib import Path

# Shared state file - global across all users and clients
STATE_FILE = Path(__file__).parent / "board_state.json"

DEFAULT_BOARD = {
    "title": "My Kanban Board",
    "columns": [
        {"id": "todo", "title": "📋 To Do", "color": "#6366f1", "cards": []},
        {"id": "progress", "title": "🔨 In Progress", "color": "#f59e0b", "cards": []},
        {"id": "review", "title": "👀 Review", "color": "#8b5cf6", "cards": []},
        {"id": "done", "title": "✅ Done", "color": "#10b981", "cards": []},
    ]
}

def load_board():
    """Load board from shared JSON file"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_BOARD.copy()

def save_board(board):
    """Save board to shared JSON file"""
    with open(STATE_FILE, "w") as f:
        json.dump(board, f, indent=2)
    return board

def render_board_html(board):
    """Render board as HTML"""
    title = board.get("title", "Kanban Board")
    columns = board.get("columns", [])
    
    columns_html = ""
    for col in columns:
        cards_html = ""
        for card in col.get("cards", []):
            priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
            priority = card.get("priority", "medium")
            tags_html = " ".join([f'<span style="background:#374151;padding:2px 6px;border-radius:4px;font-size:11px;">{t}</span>' for t in card.get("tags", [])])
            cards_html += f'''
            <div style="background:#1f2937;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {priority_colors.get(priority, '#f59e0b')};">
                <div style="margin-bottom:6px;">{card.get("text", "")}</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;">{tags_html}</div>
            </div>
            '''
        
        columns_html += f'''
        <div style="background:#111827;border-radius:12px;padding:16px;min-width:250px;flex:1;">
            <div style="font-weight:bold;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid {col.get("color", "#6366f1")};">
                {col.get("title", "Column")} <span style="opacity:0.6;">({len(col.get("cards", []))})</span>
            </div>
            <div>{cards_html if cards_html else '<div style="opacity:0.5;text-align:center;padding:20px;">No cards</div>'}</div>
        </div>
        '''
    
    html = f'''
    <div style="font-family:system-ui;color:white;padding:20px;">
        <h1 style="margin-bottom:20px;font-size:24px;">{title}</h1>
        <div style="display:flex;gap:16px;overflow-x:auto;">
            {columns_html}
        </div>
        <div style="margin-top:16px;opacity:0.5;font-size:12px;">Auto-refreshes every 2 seconds</div>
    </div>
    '''
    return html

def get_board_html():
    """Load and render board - called by timer"""
    board = load_board()
    return render_board_html(board)

def get_status():
    """Get board status text"""
    board = load_board()
    total_cards = sum(len(col.get("cards", [])) for col in board.get("columns", []))
    return f"📊 {total_cards} cards across {len(board.get('columns', []))} columns"

# API endpoint: Update entire board state (for Python client)
def api_set_board(board_data: dict):
    """API: Set the entire board state. Call this from Python client."""
    save_board(board_data)
    return {"status": "ok", "message": "Board updated"}

# API endpoint: Add a card
def api_add_card(column_id: str, text: str, priority: str = "medium", tags: list = None):
    """API: Add a card to a column"""
    board = load_board()
    import uuid
    card = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "priority": priority,
        "tags": tags or []
    }
    for col in board["columns"]:
        if col["id"] == column_id:
            col["cards"].append(card)
            break
    save_board(board)
    return {"status": "ok", "card_id": card["id"]}

# API endpoint: Move a card
def api_move_card(card_id: str, to_column_id: str):
    """API: Move a card to another column"""
    board = load_board()
    card_to_move = None
    
    # Find and remove card from current column
    for col in board["columns"]:
        for card in col["cards"]:
            if card["id"] == card_id:
                card_to_move = card
                col["cards"].remove(card)
                break
        if card_to_move:
            break
    
    # Add to target column
    if card_to_move:
        for col in board["columns"]:
            if col["id"] == to_column_id:
                col["cards"].append(card_to_move)
                break
        save_board(board)
        return {"status": "ok"}
    return {"status": "error", "message": "Card not found"}

# API endpoint: Clear board
def api_clear_board():
    """API: Clear all cards from the board"""
    board = load_board()
    for col in board["columns"]:
        col["cards"] = []
    save_board(board)
    return {"status": "ok"}

# API endpoint: Set title
def api_set_title(title: str):
    """API: Set board title"""
    board = load_board()
    board["title"] = title
    save_board(board)
    return {"status": "ok"}

# Initialize state file if it doesn't exist
if not STATE_FILE.exists():
    save_board(DEFAULT_BOARD)

# Build UI
with gr.Blocks(theme=gr.themes.Base(), css=".gradio-container {background: #0a0a0a;}") as demo:
    
    # Timer for auto-refresh (every 2 seconds)
    timer = gr.Timer(2)
    
    gr.Markdown("# 🗂️ Kanban Board with Live Sync")
    gr.Markdown("*This board auto-refreshes every 2 seconds. Use the Python client to make changes!*")
    
    # Board display - refreshes on timer tick
    board_html = gr.HTML(value=get_board_html)
    status = gr.Textbox(value=get_status, label="Status", interactive=False)
    
    # Timer triggers refresh
    timer.tick(fn=get_board_html, outputs=board_html)
    timer.tick(fn=get_status, outputs=status)
    
    # Manual refresh button
    refresh_btn = gr.Button("🔄 Refresh Now")
    refresh_btn.click(fn=get_board_html, outputs=board_html)
    refresh_btn.click(fn=get_status, outputs=status)
    
    # === API ENDPOINTS (hidden inputs/outputs for Python client) ===
    with gr.Row(visible=False):
        # Inputs for API calls
        api_board_data = gr.JSON()
        api_column_id = gr.Textbox()
        api_card_text = gr.Textbox()
        api_priority = gr.Textbox()
        api_tags = gr.JSON()
        api_card_id = gr.Textbox()
        api_to_column = gr.Textbox()
        api_title = gr.Textbox()
        # Output for API responses
        api_response = gr.JSON()
    
    # Wire up API functions with explicit api_name
    refresh_btn.click(
        fn=api_set_board,
        inputs=[api_board_data],
        outputs=[api_response],
        api_name="set_board"
    )
    
    refresh_btn.click(
        fn=api_add_card,
        inputs=[api_column_id, api_card_text, api_priority, api_tags],
        outputs=[api_response],
        api_name="add_card"
    )
    
    refresh_btn.click(
        fn=api_move_card,
        inputs=[api_card_id, api_to_column],
        outputs=[api_response],
        api_name="move_card"
    )
    
    refresh_btn.click(
        fn=api_clear_board,
        inputs=[],
        outputs=[api_response],
        api_name="clear_board"
    )
    
    refresh_btn.click(
        fn=api_set_title,
        inputs=[api_title],
        outputs=[api_response],
        api_name="set_title"
    )

# Launch
if __name__ == "__main__":
    demo.launch()
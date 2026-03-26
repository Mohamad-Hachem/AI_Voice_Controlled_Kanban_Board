"""
Python Client for Kanban Board
Run this while the Gradio app is running to see UI changes in real-time!
"""

from gradio_client import Client
import time

# Connect to local Gradio app
client = Client("http://127.0.0.1:7860")

print("Connected to Kanban Board!\n")

# 1. Clear the board first
print("1. Clearing board...")
result = client.predict(api_name="/clear_board")
print(f"   Result: {result}")
time.sleep(1)

# 2. Set a new title
print("\n2. Setting title to 'Sprint 42 - Demo'...")
result = client.predict(
    "🚀 Sprint 42 - Demo",
    api_name="/set_title"
)
print(f"   Result: {result}")
time.sleep(1)

# 3. Add cards to To Do
print("\n3. Adding cards to 'To Do' column...")
cards_to_add = [
    ("todo", "Build login page", "high", ["frontend", "auth"]),
    ("todo", "Write unit tests", "medium", ["testing"]),
    ("todo", "Update documentation", "low", ["docs"]),
]

for column_id, text, priority, tags in cards_to_add:
    result = client.predict(
        column_id,  # positional arg 1
        text,       # positional arg 2
        priority,   # positional arg 3
        tags,       # positional arg 4
        api_name="/add_card"
    )
    print(f"   Added: {text} -> {result}")
    time.sleep(0.5)

# 4. Add a card to In Progress
print("\n4. Adding card to 'In Progress'...")
result = client.predict(
    "progress",
    "Implement API endpoints",
    "high",
    ["backend", "api"],
    api_name="/add_card"
)
print(f"   Result: {result}")
time.sleep(1)

# 5. Add a card to Done
print("\n5. Adding card to 'Done'...")
result = client.predict(
    "done",
    "Project setup complete",
    "medium",
    ["setup"],
    api_name="/add_card"
)
print(f"   Result: {result}")

print("\n" + "="*50)
print("✅ Done! Check your browser - the board should have updated!")
print("="*50)

# Bonus: Add to review after a delay
print("\n⏳ In 3 seconds, will add a card to 'Review'...")
time.sleep(3)

print("\n6. Adding card to 'Review'...")
result = client.predict(
    "review",
    "Code review: Auth module",
    "high",
    ["review", "auth"],
    api_name="/add_card"
)
print(f"   Result: {result}")

print("\n🎉 All done! The UI should have updated automatically.")
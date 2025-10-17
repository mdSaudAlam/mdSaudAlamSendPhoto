import json, os, uuid

# In-memory maps
chat_map = {}         # token → chat_id
name_map = {}         # token → name
chat_to_token = {}    # chat_id → token

STORE_FILE = "tokens.json"

def save_store():
    """Save current maps to JSON file safely."""
    try:
        with open(STORE_FILE, "w") as f:
            json.dump({
                "chat_map": chat_map,
                "name_map": name_map,
                "chat_to_token": chat_to_token
            }, f, indent=2)
    except Exception as e:
        print("Error saving store:", e)

def load_store():
    """Load maps from JSON file if it exists."""
    global chat_map, name_map, chat_to_token
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE) as f:
                data = json.load(f)
                chat_map = data.get("chat_map", {})
                name_map = data.get("name_map", {})
                chat_to_token = data.get("chat_to_token", {})
        except Exception as e:
            print("Error loading store:", e)
            chat_map, name_map, chat_to_token = {}, {}, {}

# ✅ Load existing tokens at startup
load_store()

def generate_token(chat_id):
    """Generate a new unique token for a chat_id."""
    return str(uuid.uuid4())

def store_token_for_chat(token, chat_id):
    """Store mapping of token → chat_id and reverse."""
    chat_map[token] = chat_id
    chat_to_token[chat_id] = token
    save_store()

def get_chat_id(token):
    """Get chat_id from token."""
    return chat_map.get(token)

def get_token_for_chat(chat_id):
    """Get token from chat_id."""
    return chat_to_token.get(chat_id)

def store_chat_to_token(chat_id, token):
    """Store reverse mapping chat_id → token."""
    chat_to_token[chat_id] = token
    save_store()

def store_name(token, name):
    """Store user name for a token."""
    name_map[token] = name
    save_store()

def get_name(token):
    """Get user name from token."""
    return name_map.get(token)
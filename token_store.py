# Simple in-memory maps
chat_map = {}         # token → chat_id
name_map = {}         # token → name
chat_to_token = {}    # chat_id → token

def generate_token(chat_id):
    import uuid
    return str(uuid.uuid4())

def store_token_for_chat(token, chat_id):
    chat_map[token] = chat_id
    chat_to_token[chat_id] = token  # reverse mapping

def get_chat_id(token):
    return chat_map.get(token)

def get_token_for_chat(chat_id):
    return chat_to_token.get(chat_id)

def store_chat_to_token(chat_id, token):
    chat_to_token[chat_id] = token

def store_name(token, name):
    name_map[token] = name

def get_name(token):
    return name_map.get(token)